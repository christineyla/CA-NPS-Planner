import { formatDateRange, formatScore } from "@/lib/formatters";
import { getCrowdScoreLabel, getWeatherScoreLabel } from "@/lib/scoreLabels";
import { ForecastWeek } from "@/types/park-dashboard";

interface BestWeeksListProps {
  weeks: ForecastWeek[];
}

function recommendationContext(index: number): string {
  if (index === 0) {
    return "Strongest overall balance of crowds and weather this season.";
  }

  if (index === 1) {
    return "A close alternative if your schedule misses the top week.";
  }

  return "Solid backup option with dependable overall conditions.";
}

export function BestWeeksList({ weeks }: BestWeeksListProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Best Weeks to Visit</h2>
      <ol className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {weeks.map((week, index) => (
          <li
            key={`${week.week_start}-${week.week_end}`}
            className="rounded-lg border border-slate-200 bg-slate-50 p-3"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-semibold text-slate-900">
                {formatDateRange(week.week_start, week.week_end)}
              </p>
              <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-slate-600">
                #{index + 1}
              </span>
            </div>

            <p className="mt-2 text-xs text-slate-600">Trip score</p>
            <p className="text-sm font-semibold text-slate-900">
              {formatScore(week.trip_score)}
            </p>

            <dl className="mt-2 space-y-1 text-xs">
              <div className="flex items-start gap-1">
                <dt className="text-slate-500">Crowd outlook:</dt>
                <dd className="font-medium text-slate-700">
                  {getCrowdScoreLabel(week.crowd_score)}
                </dd>
              </div>
              <div className="flex items-start gap-1">
                <dt className="text-slate-500">Weather outlook:</dt>
                <dd className="font-medium text-slate-700">
                  {getWeatherScoreLabel(week.weather_score)}
                </dd>
              </div>
            </dl>

            <p className="mt-2 text-[11px] text-slate-500">
              {recommendationContext(index)}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}
