import { formatScore } from "@/lib/formatters";
import { ParksMapDataItem } from "@/types/park-dashboard";

interface CaliforniaParkMapProps {
  parks: ParksMapDataItem[];
}

const MAP_WIDTH = 560;
const MAP_HEIGHT = 680;
const LAT_MIN = 32.5;
const LAT_MAX = 42.2;
const LNG_MIN = -124.6;
const LNG_MAX = -114.0;

function projectToMap(latitude: number, longitude: number) {
  const x = ((longitude - LNG_MIN) / (LNG_MAX - LNG_MIN)) * MAP_WIDTH;
  const y = ((LAT_MAX - latitude) / (LAT_MAX - LAT_MIN)) * MAP_HEIGHT;

  return {
    x: Math.min(Math.max(18, x), MAP_WIDTH - 18),
    y: Math.min(Math.max(18, y), MAP_HEIGHT - 18),
  };
}

function markerClass(level: ParksMapDataItem["crowd_level"]): string {
  if (level === "low") return "fill-emerald-500";
  if (level === "moderate") return "fill-amber-400";
  if (level === "busy") return "fill-orange-500";
  if (level === "extreme") return "fill-rose-600";
  return "fill-slate-500";
}

export function CaliforniaParkMap({ parks }: CaliforniaParkMapProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-900">California park crowd map</h2>
        <p className="text-xs text-slate-500">Click any marker to open park dashboard</p>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-slate-50 p-3">
        <svg viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} className="h-[480px] w-full" role="img" aria-label="Map of California parks">
          <path
            d="M157 16 L177 16 L194 62 L245 118 L222 203 L251 286 L222 335 L253 401 L227 455 L243 523 L232 650 L183 648 L118 614 L96 549 L66 477 L29 360 L58 257 L42 197 L75 156 L98 114 L123 63 Z"
            className="fill-slate-200 stroke-slate-400"
            strokeWidth="4"
          />

          {parks.map((park) => {
            const point = projectToMap(park.latitude, park.longitude);
            const markerSize = 9;
            const scoreLabel = park.crowd_score === null ? "N/A" : formatScore(park.crowd_score);

            return (
              <a key={park.park_id} href={`/parks/${park.park_id}`}>
                <title>{`${park.name} - Crowd ${scoreLabel}`}</title>
                <circle cx={point.x} cy={point.y} r={markerSize} className={`${markerClass(park.crowd_level)} stroke-white`} strokeWidth="2" />
                <text x={point.x + 14} y={point.y + 4} className="fill-slate-800 text-[14px] font-medium">
                  {park.name.replace(" National Park", "")}
                </text>
              </a>
            );
          })}
        </svg>
      </div>
    </section>
  );
}
