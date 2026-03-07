import { formatVisits } from "@/lib/formatters";
import { ForecastWeek, VisitationHistoryPoint } from "@/types/park-dashboard";

interface HistoricalForecastChartProps {
  forecast: ForecastWeek[];
  history: VisitationHistoryPoint[];
}

type PointType = "history" | "forecast";

interface ChartPoint {
  date: Date;
  label: string;
  visits: number;
  type: PointType;
  lower: number | null;
  upper: number | null;
}

const CHART_WIDTH = 760;
const CHART_HEIGHT = 260;
const PADDING = 28;

function formatLabel(date: Date): string {
  return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

function toChartPoints(history: VisitationHistoryPoint[], forecast: ForecastWeek[]): ChartPoint[] {
  const historyPoints = history.map((entry) => {
    const date = new Date(entry.observation_month);
    return {
      date,
      label: formatLabel(date),
      visits: entry.visits,
      type: "history" as const,
      lower: null,
      upper: null,
    };
  });

  const forecastPoints = forecast.slice(0, 26).map((week) => {
    const date = new Date(week.week_start);
    return {
      date,
      label: formatLabel(date),
      visits: week.predicted_visits,
      type: "forecast" as const,
      lower: week.predicted_visits_lower ?? null,
      upper: week.predicted_visits_upper ?? null,
    };
  });

  return [...historyPoints, ...forecastPoints].sort((a, b) => a.date.getTime() - b.date.getTime());
}

function pointToCoordinate(value: number, index: number, count: number, maxValue: number): [number, number] {
  const x = PADDING + (index * (CHART_WIDTH - PADDING * 2)) / Math.max(count - 1, 1);
  const y = CHART_HEIGHT - PADDING - (value / maxValue) * (CHART_HEIGHT - PADDING * 2);
  return [x, y];
}

function buildPath(points: ChartPoint[], maxValue: number, type: PointType): string {
  const filtered = points
    .map((point, index) => ({ point, index }))
    .filter(({ point }) => point.type === type);

  return filtered
    .map(({ point, index }, pathIndex) => {
      const [x, y] = pointToCoordinate(point.visits, index, points.length, maxValue);
      return `${pathIndex === 0 ? "M" : "L"}${x} ${y}`;
    })
    .join(" ");
}

function buildConfidenceBand(points: ChartPoint[], maxValue: number): string | null {
  const forecast = points
    .map((point, index) => ({ point, index }))
    .filter(({ point }) => point.type === "forecast" && point.lower !== null && point.upper !== null);

  if (forecast.length < 2) {
    return null;
  }

  const upperPath = forecast
    .map(({ point, index }, pathIndex) => {
      const [x, y] = pointToCoordinate(point.upper ?? point.visits, index, points.length, maxValue);
      return `${pathIndex === 0 ? "M" : "L"}${x} ${y}`;
    })
    .join(" ");

  const lowerPath = forecast
    .slice()
    .reverse()
    .map(({ point, index }, pathIndex) => {
      const [x, y] = pointToCoordinate(point.lower ?? point.visits, index, points.length, maxValue);
      return `${pathIndex === 0 ? "L" : "L"}${x} ${y}`;
    })
    .join(" ");

  return `${upperPath} ${lowerPath} Z`;
}

export function HistoricalForecastChart({ forecast, history }: HistoricalForecastChartProps) {
  const points = toChartPoints(history, forecast);

  if (points.length === 0) {
    return null;
  }

  const maxValue = Math.max(...points.map((point) => point.upper ?? point.visits), 1);
  const minForecastIndex = points.findIndex((point) => point.type === "forecast");
  const forecastStartX =
    minForecastIndex >= 0
      ? PADDING + (minForecastIndex * (CHART_WIDTH - PADDING * 2)) / Math.max(points.length - 1, 1)
      : null;

  const confidenceBandPath = buildConfidenceBand(points, maxValue);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Historical + Forecast Visits</h2>
      <p className="mt-1 text-xs text-slate-500">Historical monthly visitation and forecasted weekly trends for the selected park.</p>
      <div className="mt-3 rounded-md border border-slate-100 p-2">
        <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} className="h-72 w-full" role="img" aria-label="Historical and forecast visits line chart">
          <line x1={PADDING} y1={CHART_HEIGHT - PADDING} x2={CHART_WIDTH - PADDING} y2={CHART_HEIGHT - PADDING} className="stroke-slate-300" strokeWidth="1" />
          <line x1={PADDING} y1={PADDING} x2={PADDING} y2={CHART_HEIGHT - PADDING} className="stroke-slate-300" strokeWidth="1" />

          {confidenceBandPath ? <path d={confidenceBandPath} className="fill-emerald-500/15" /> : null}
          <path d={buildPath(points, maxValue, "history")} className="fill-none stroke-slate-600" strokeWidth="2.5" />
          <path d={buildPath(points, maxValue, "forecast")} className="fill-none stroke-emerald-600" strokeWidth="2.5" strokeDasharray="7 5" />

          {forecastStartX ? (
            <>
              <line x1={forecastStartX} y1={PADDING} x2={forecastStartX} y2={CHART_HEIGHT - PADDING} className="stroke-slate-400" strokeWidth="1" strokeDasharray="3 4" />
              <text x={Math.min(forecastStartX + 8, CHART_WIDTH - PADDING)} y={PADDING + 14} className="fill-slate-500 text-[10px]">
                Forecast begins
              </text>
            </>
          ) : null}

          {points.map((point, index) => {
            if (index % 5 !== 0 && index !== points.length - 1) {
              return null;
            }

            const [x] = pointToCoordinate(point.visits, index, points.length, maxValue);
            return (
              <text key={`${point.label}-${index}`} x={x} y={CHART_HEIGHT - 8} textAnchor="middle" className="fill-slate-500 text-[11px]">
                {point.label}
              </text>
            );
          })}
        </svg>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-600">
        <span className="inline-flex items-center gap-1">
          <span className="h-0.5 w-4 bg-slate-600" /> Historical (monthly)
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-0.5 w-4 border-t-2 border-dashed border-emerald-600" /> Forecast (weekly)
        </span>
        {confidenceBandPath ? (
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-4 rounded-sm bg-emerald-500/20" /> Forecast confidence range
          </span>
        ) : null}
        <span className="ml-auto text-slate-500">Peak weekly/monthly volume: {formatVisits(maxValue)}</span>
      </div>
    </section>
  );
}
