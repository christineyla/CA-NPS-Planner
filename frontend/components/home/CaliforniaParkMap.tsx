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

const MAP_WIDTH = 680;
const MAP_HEIGHT = 760;
const LAT_MIN = 32.3;
const LAT_MAX = 42.2;
const LNG_MIN = -124.8;
const LNG_MAX = -113.9;

const MAJOR_CITIES: MapCity[] = [
  { name: "San Francisco", latitude: 37.7749, longitude: -122.4194 },
  { name: "Los Angeles", latitude: 34.0522, longitude: -118.2437 },
  { name: "San Diego", latitude: 32.7157, longitude: -117.1611 },
  { name: "Sacramento", latitude: 38.5816, longitude: -121.4944 },
  { name: "Fresno", latitude: 36.7378, longitude: -119.7871 },
];

function projectToMap(latitude: number, longitude: number) {
  const x = ((longitude - LNG_MIN) / (LNG_MAX - LNG_MIN)) * MAP_WIDTH;
  const y = ((LAT_MAX - latitude) / (LAT_MAX - LAT_MIN)) * MAP_HEIGHT;

  return {
    x: Math.min(Math.max(20, x), MAP_WIDTH - 20),
    y: Math.min(Math.max(20, y), MAP_HEIGHT - 20),
  };
}

function markerClass(level: ParksMapDataItem["crowd_level"]): string {
  if (level === "low") return "fill-emerald-500";
  if (level === "moderate") return "fill-amber-400";
  if (level === "busy") return "fill-orange-500";
  if (level === "extreme") return "fill-rose-600";
  return "fill-slate-500";
}

export function CaliforniaParkMap({ parks, selectedParkId, onSelectPark }: CaliforniaParkMapProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-900">California park crowd map</h2>
        <p className="text-xs text-slate-500">Marker color = crowd level. Click a park marker to load analytics below.</p>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-gradient-to-b from-sky-100 to-sky-50 p-3">
        <svg viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} className="h-[520px] w-full" role="img" aria-label="Map of California parks and major cities">
          <rect x="0" y="0" width={MAP_WIDTH} height={MAP_HEIGHT} className="fill-sky-100" />
          <path
            d="M198 28 L223 24 L247 88 L317 150 L289 242 L332 356 L292 434 L338 532 L302 613 L325 694 L307 744 L224 742 L176 704 L146 626 L101 523 L66 414 L88 324 L74 236 L109 188 L136 136 L165 89 Z"
            className="fill-slate-100 stroke-slate-500"
            strokeWidth="4"
          />

          {MAJOR_CITIES.map((city) => {
            const point = projectToMap(city.latitude, city.longitude);
            return (
              <g key={city.name}>
                <circle cx={point.x} cy={point.y} r={5} className="fill-slate-500/80 stroke-white" strokeWidth="2" />
                <text x={point.x + 10} y={point.y + 5} className="fill-slate-700 text-[14px] font-semibold">
                  {city.name}
                </text>
              </g>
            );
          })}

          {parks.map((park) => {
            const point = projectToMap(park.latitude, park.longitude);
            const scoreLabel = park.crowd_score === null ? "N/A" : formatScore(park.crowd_score);
            const isSelected = selectedParkId === park.park_id;

            return (
              <g
                key={park.park_id}
                className="cursor-pointer"
                onClick={() => onSelectPark?.(park.park_id)}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelectPark?.(park.park_id);
                  }
                }}
                aria-label={`Select ${park.name}`}
              >
                <title>{`${park.name} - Crowd ${scoreLabel}`}</title>
                {isSelected ? (
                  <circle cx={point.x} cy={point.y} r={15} className="fill-emerald-100/90 stroke-emerald-500" strokeWidth="2" />
                ) : null}
                <circle
                  cx={point.x}
                  cy={point.y}
                  r={10}
                  className={`${markerClass(park.crowd_level)} stroke-white`}
                  strokeWidth="2"
                />
                <text x={point.x + 14} y={point.y + 4} className="fill-slate-900 text-[13px] font-bold">
                  {park.name.replace(" National Park", "")}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
}
