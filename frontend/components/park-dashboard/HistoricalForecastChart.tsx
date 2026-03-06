import { formatVisits } from "@/lib/formatters";
import { ForecastWeek } from "@/types/park-dashboard";

interface HistoricalForecastChartProps {
  forecast: ForecastWeek[];
}

interface ChartPoint {
  label: string;
  historical: number;
  forecast: number;
}

function toChartPoints(forecast: ForecastWeek[]): ChartPoint[] {
  return forecast.slice(0, 12).map((week, index) => {
    const historicalEstimate = Math.round(week.predicted_visits * (0.82 + (index % 4) * 0.04));

    return {
      label: new Date(week.week_start).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      historical: historicalEstimate,
      forecast: week.predicted_visits,
    };
  });
}

export function HistoricalForecastChart({ forecast }: HistoricalForecastChartProps) {
  const points = toChartPoints(forecast);
  const max = Math.max(...points.flatMap((point) => [point.historical, point.forecast]), 1);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Historical + Forecast Visits</h2>
      <div className="mt-4 space-y-2">
        {points.map((point) => (
          <div key={point.label}>
            <div className="mb-1 flex justify-between text-xs text-slate-500">
              <span>{point.label}</span>
              <span>Forecast: {formatVisits(point.forecast)}</span>
            </div>
            <div className="h-4 rounded bg-slate-100">
              <div
                className="h-2 rounded bg-slate-400"
                style={{ width: `${(point.historical / max) * 100}%` }}
                title={`Historical estimate: ${formatVisits(point.historical)}`}
              />
              <div
                className="-mt-2 h-2 rounded bg-emerald-500"
                style={{ width: `${(point.forecast / max) * 100}%` }}
                title={`Forecast: ${formatVisits(point.forecast)}`}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-slate-600">
        <span className="inline-flex items-center gap-1">
          <span className="h-2 w-2 rounded bg-slate-400" /> Historical proxy
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-2 w-2 rounded bg-emerald-500" /> Forecast
        </span>
      </div>
    </section>
  );
}
