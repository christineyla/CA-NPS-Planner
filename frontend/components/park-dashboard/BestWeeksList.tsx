import { formatDateRange, formatScore } from "@/lib/formatters";
import { getCrowdScoreLabel, getWeatherScoreLabel } from "@/lib/scoreLabels";
import { ForecastWeek } from "@/types/park-dashboard";

interface BestWeeksListProps {
  weeks: ForecastWeek[];
}

export function BestWeeksList({ weeks }: BestWeeksListProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Best Weeks to Visit</h2>
      <ol className="mt-3 space-y-2">
        {weeks.map((week) => (
          <li
            key={`${week.week_start}-${week.week_end}`}
            className="rounded-lg border border-slate-100 bg-slate-50 p-3"
          >
            <p className="text-sm font-medium text-slate-800">
              {formatDateRange(week.week_start, week.week_end)}
            </p>
            <p className="text-xs text-slate-600">Trip score: {formatScore(week.trip_score)}</p>
            <p className="mt-1 text-xs text-slate-500">
              Crowd outlook: {getCrowdScoreLabel(week.crowd_score)} · Weather outlook: {getWeatherScoreLabel(week.weather_score)}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}
