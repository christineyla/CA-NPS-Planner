"use client";

import { useMemo, useState } from "react";

import type { ParksMapDataItem } from "@/types/parks";

type CaliforniaParkMapProps = {
  markers: ParksMapDataItem[];
};

type Bounds = {
  minLat: number;
  maxLat: number;
  minLon: number;
  maxLon: number;
};

function getMarkerColor(level: ParksMapDataItem["crowd_level"]): string {
  switch (level) {
    case "low":
      return "bg-emerald-500";
    case "moderate":
      return "bg-amber-400";
    case "busy":
      return "bg-orange-500";
    case "extreme":
      return "bg-rose-600";
    default:
      return "bg-slate-500";
  }
}

function normalizePosition(marker: ParksMapDataItem, bounds: Bounds) {
  const x = ((marker.longitude - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * 100;
  const y = 100 - ((marker.latitude - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * 100;

  return {
    left: `${Math.min(92, Math.max(8, x))}%`,
    top: `${Math.min(92, Math.max(8, y))}%`,
  };
}

export function CaliforniaParkMap({ markers }: CaliforniaParkMapProps) {
  const [selectedParkId, setSelectedParkId] = useState<number | null>(markers[0]?.park_id ?? null);

  const bounds = useMemo<Bounds>(() => {
    const latitudes = markers.map((marker) => marker.latitude);
    const longitudes = markers.map((marker) => marker.longitude);

    return {
      minLat: Math.min(...latitudes),
      maxLat: Math.max(...latitudes),
      minLon: Math.min(...longitudes),
      maxLon: Math.max(...longitudes),
    };
  }, [markers]);

  const selected = markers.find((marker) => marker.park_id === selectedParkId) ?? markers[0];

  return (
    <section className="grid gap-6 lg:grid-cols-[2fr_1fr]" aria-label="California park map">
      <div className="relative min-h-[420px] overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-sky-100 via-blue-50 to-emerald-100 p-6">
        <h2 className="text-xl font-semibold text-slate-900">California park map</h2>
        <p className="mt-1 text-sm text-slate-600">Click a marker to inspect park location and crowd level.</p>

        <div className="relative mt-6 h-[320px] rounded-xl border border-slate-300 bg-slate-50">
          <div className="absolute inset-6 rounded-[32%_48%_40%_54%] border-2 border-emerald-700/60 bg-emerald-100/40" />
          {markers.map((marker) => {
            const position = normalizePosition(marker, bounds);
            const isSelected = marker.park_id === selectedParkId;

            return (
              <button
                key={marker.park_id}
                type="button"
                onClick={() => setSelectedParkId(marker.park_id)}
                className="group absolute -translate-x-1/2 -translate-y-1/2"
                style={position}
                aria-label={`View ${marker.name}`}
              >
                <span
                  className={`block h-4 w-4 rounded-full ring-4 ring-white transition ${getMarkerColor(marker.crowd_level)} ${isSelected ? "scale-125" : "scale-100"}`}
                />
                <span className="pointer-events-none absolute left-1/2 top-5 hidden -translate-x-1/2 whitespace-nowrap rounded bg-slate-900 px-2 py-1 text-xs text-white group-hover:block">
                  {marker.name}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <aside className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Selected park</h3>
        <p className="mt-2 text-lg font-semibold text-slate-900">{selected?.name ?? "No park selected"}</p>
        {selected ? (
          <dl className="mt-4 space-y-2 text-sm text-slate-700">
            <div className="flex justify-between gap-3">
              <dt>Crowd score</dt>
              <dd className="font-medium">{selected.crowd_score?.toFixed(1) ?? "N/A"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>Crowd level</dt>
              <dd className="font-medium capitalize">{selected.crowd_level ?? "Unknown"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>Coordinates</dt>
              <dd className="font-medium">
                {selected.latitude.toFixed(3)}, {selected.longitude.toFixed(3)}
              </dd>
            </div>
          </dl>
        ) : null}
      </aside>
    </section>
  );
}
