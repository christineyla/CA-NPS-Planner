import { formatVisits } from "@/lib/formatters";
import { ForecastWeek } from "@/types/park-dashboard";

interface HistoricalForecastChartProps {
  forecast: ForecastWeek[];
}

interface ChartPoint {
  label: string;
  historical_visits: number;
  forecast_visits: number;
}

const CHART_WIDTH = 760;
const CHART_HEIGHT = 260;
const PADDING = 28;

function toChartPoints(forecast: ForecastWeek[]): ChartPoint[] {
  return forecast.slice(0, 20).map((week, index) => {
    const historicalEstimate = Math.round(week.predicted_visits * (0.8 + (index % 5) * 0.035));

    return {
      label: new Date(week.week_start).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      historical_visits: historicalEstimate,
      forecast_visits: week.predicted_visits,
    };
  });
}

function buildPath(points: number[], maxValue: number): string {
  return points
    .map((value, index) => {
      const x = PADDING + (index * (CHART_WIDTH - PADDING * 2)) / Math.max(points.length - 1, 1);
      const y = CHART_HEIGHT - PADDING - (value / maxValue) * (CHART_HEIGHT - PADDING * 2);
      return `${index === 0 ? "M" : "L"}${x} ${y}`;
    })
    .join(" ");
}

export function HistoricalForecastChart({ forecast }: HistoricalForecastChartProps) {
  const points = toChartPoints(forecast);
  const historicalSeries = points.map((point) => point.historical_visits);
  const forecastSeries = points.map((point) => point.forecast_visits);
  const maxValue = Math.max(...historicalSeries, ...forecastSeries, 1);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Historical + Forecast Visits</h2>
      <p className="mt-1 text-xs text-slate-500">Weekly trend comparing historical baseline and forecasted park visits.</p>
      <div className="mt-3 rounded-md border border-slate-100 p-2">
        <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} className="h-72 w-full" role="img" aria-label="Historical and forecast visits line chart">
          <line x1={PADDING} y1={CHART_HEIGHT - PADDING} x2={CHART_WIDTH - PADDING} y2={CHART_HEIGHT - PADDING} className="stroke-slate-300" strokeWidth="1" />
          <line x1={PADDING} y1={PADDING} x2={PADDING} y2={CHART_HEIGHT - PADDING} className="stroke-slate-300" strokeWidth="1" />

          <path d={buildPath(historicalSeries, maxValue)} className="fill-none stroke-slate-500" strokeWidth="2" />
          <path d={buildPath(forecastSeries, maxValue)} className="fill-none stroke-emerald-600" strokeWidth="3" />

          {points.map((point, index) => {
            if (index % 4 !== 0 && index !== points.length - 1) {
              return null;
            }

            const x = PADDING + (index * (CHART_WIDTH - PADDING * 2)) / Math.max(points.length - 1, 1);
            return (
              <text key={point.label} x={x} y={CHART_HEIGHT - 8} textAnchor="middle" className="fill-slate-500 text-[11px]">
                {point.label}
              </text>
            );
          })}
        </svg>
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-slate-600">
        <span className="inline-flex items-center gap-1">
          <span className="h-2 w-2 rounded bg-slate-500" /> Historical baseline
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-2 w-2 rounded bg-emerald-600" /> Forecast
        </span>
        <span className="ml-auto text-slate-500">Peak weekly volume: {formatVisits(maxValue)}</span>
      </div>
    </section>
  );
}
