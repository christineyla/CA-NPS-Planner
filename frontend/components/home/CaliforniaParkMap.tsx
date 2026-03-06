"use client";

import Script from "next/script";
import { useEffect, useMemo, useRef, useState } from "react";

import { formatScore } from "@/lib/formatters";
import { ParksMapDataItem } from "@/types/park-dashboard";

interface CaliforniaParkMapProps {
  parks: ParksMapDataItem[];
  selectedParkId?: number;
  onSelectPark?: (parkId: number) => void;
}

interface MapCity {
  name: string;
  latitude: number;
  longitude: number;
}

type CrowdLevel = ParksMapDataItem["crowd_level"];

type LeafletLatLng = [number, number];

interface LeafletMarker {
  bindTooltip(content: string, options?: { permanent?: boolean; direction?: "left" | "right" | "top" | "bottom"; offset?: [number, number] }): LeafletMarker;
  bindPopup(content: string): LeafletMarker;
  addTo(layer: LeafletLayerGroup): LeafletMarker;
  on(eventName: "click", handler: () => void): LeafletMarker;
  setStyle?(options: { color?: string; fillColor?: string; fillOpacity?: number; weight?: number; radius?: number }): void;
}

interface LeafletLayerGroup {
  addTo(map: LeafletMap): LeafletLayerGroup;
  clearLayers(): void;
}

interface LeafletMap {
  setView(center: LeafletLatLng, zoom: number): LeafletMap;
  remove(): void;
}

interface LeafletNamespace {
  map(element: HTMLDivElement, options?: { zoomControl?: boolean }): LeafletMap;
  tileLayer(urlTemplate: string, options: { attribution: string; maxZoom?: number; minZoom?: number }): { addTo(map: LeafletMap): void };
  layerGroup(): LeafletLayerGroup;
  circleMarker(latLng: LeafletLatLng, options: { radius: number; color: string; weight: number; fillColor: string; fillOpacity: number }): LeafletMarker;
}

declare global {
  interface Window {
    L?: LeafletNamespace;
  }
}

const MAJOR_CITIES: MapCity[] = [
  { name: "San Francisco", latitude: 37.7749, longitude: -122.4194 },
  { name: "Los Angeles", latitude: 34.0522, longitude: -118.2437 },
  { name: "San Diego", latitude: 32.7157, longitude: -117.1611 },
  { name: "Sacramento", latitude: 38.5816, longitude: -121.4944 },
  { name: "Fresno", latitude: 36.7378, longitude: -119.7871 },
];

function getCrowdColor(level: CrowdLevel): string {
  if (level === "low") return "#10b981";
  if (level === "moderate") return "#f59e0b";
  if (level === "busy") return "#f97316";
  if (level === "extreme") return "#e11d48";
  return "#64748b";
}

export function CaliforniaParkMap({ parks, selectedParkId, onSelectPark }: CaliforniaParkMapProps) {
  const mapElementRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markerLayerRef = useRef<LeafletLayerGroup | null>(null);
  const [isLeafletReady, setIsLeafletReady] = useState(false);

  const selectedPark = useMemo(() => parks.find((park) => park.park_id === selectedParkId), [parks, selectedParkId]);

  useEffect(() => {
    if (!isLeafletReady || !mapElementRef.current || mapRef.current !== null || !window.L) {
      return;
    }

    const map = window.L.map(mapElementRef.current, { zoomControl: true }).setView([36.7783, -119.4179], 6);

    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
      minZoom: 5,
    }).addTo(map);

    const markerLayer = window.L.layerGroup().addTo(map);

    mapRef.current = map;
    markerLayerRef.current = markerLayer;

    return () => {
      map.remove();
      mapRef.current = null;
      markerLayerRef.current = null;
    };
  }, [isLeafletReady]);

  useEffect(() => {
    if (!isLeafletReady || !window.L || !markerLayerRef.current || !mapRef.current) {
      return;
    }

    markerLayerRef.current.clearLayers();

    const markerLayer = markerLayerRef.current;
    const leaflet = window.L;
    if (!leaflet) {
      return;
    }

    parks.forEach((park) => {
      const scoreLabel = park.crowd_score === null ? "N/A" : formatScore(park.crowd_score);
      const isSelected = park.park_id === selectedParkId;
      const radius = isSelected ? 12 : 9;

      const marker = leaflet
        .circleMarker([park.latitude, park.longitude], {
          radius,
          color: "#ffffff",
          weight: 2,
          fillColor: getCrowdColor(park.crowd_level),
          fillOpacity: 0.95,
        })
        .bindTooltip(park.name.replace(" National Park", ""), { permanent: true, direction: "right", offset: [10, 0] })
        .bindPopup(`${park.name}<br/>Crowd score: ${scoreLabel}`)
        .addTo(markerLayer)
        .on("click", () => onSelectPark?.(park.park_id));

      if (isSelected && marker.setStyle) {
        marker.setStyle({ color: "#0f766e", weight: 3 });
      }
    });

    MAJOR_CITIES.forEach((city) => {
      leaflet
        .circleMarker([city.latitude, city.longitude], {
          radius: 7,
          color: "#1e3a8a",
          weight: 2,
          fillColor: "#60a5fa",
          fillOpacity: 0.9,
        })
        .bindTooltip(city.name, { permanent: true, direction: "right", offset: [8, 0] })
        .bindPopup(`${city.name}<br/>Major city`)
        .addTo(markerLayer);
    });
  }, [isLeafletReady, onSelectPark, parks, selectedParkId]);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <Script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" strategy="afterInteractive" onLoad={() => setIsLeafletReady(true)} />
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
        crossOrigin=""
      />

      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-900">California park crowd map</h2>
        <p className="text-xs text-slate-500">Zoom, pan, and click a park marker to load analytics below.</p>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200">
        <div ref={mapElementRef} className="h-[520px] w-full" role="img" aria-label="Interactive map of California parks and major cities" />
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-600">
        <span className="font-semibold text-slate-700">Legend:</span>
        <span className="inline-flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-emerald-500" />Low</span>
        <span className="inline-flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-amber-500" />Moderate</span>
        <span className="inline-flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-orange-500" />Busy</span>
        <span className="inline-flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-rose-600" />Extreme</span>
        <span className="inline-flex items-center gap-2"><span className="h-3 w-3 rounded-full border-2 border-blue-900 bg-blue-400" />Major city</span>
      </div>

      {selectedPark ? (
        <p className="mt-3 text-sm text-slate-600">
          Selected park: <span className="font-semibold text-slate-900">{selectedPark.name}</span>
        </p>
      ) : null}
    </section>
  );
}
