import { formatDateRange } from "@/lib/formatters";
import { CalendarWeek, ForecastWeek } from "@/types/park-dashboard";

interface CrowdCalendarProps {
  calendar: CalendarWeek[];
  forecast: ForecastWeek[];
}

export function CrowdCalendar({ calendar, forecast }: CrowdCalendarProps) {
  const scoreByWeek = new Map(forecast.map((week) => [week.week_start, week]));

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Crowd Calendar (26 Weeks)</h2>
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
        {calendar.map((week) => {
          const weekScores = scoreByWeek.get(week.week_start);
          const tooltip = weekScores
            ? `Crowd ${Math.round(week.crowd_score)}, Weather ${Math.round(
                weekScores.weather_score,
              )}, Trip ${Math.round(weekScores.trip_score)}`
            : `Crowd ${Math.round(week.crowd_score)}`;

          return (
            <div
              key={week.forecast_id}
              className="rounded-md border border-slate-200 p-2 text-xs text-slate-700"
              style={{ backgroundColor: week.color_hex }}
              title={tooltip}
            >
              <p className="font-semibold">{week.crowd_level}</p>
              <p>{formatDateRange(week.week_start, week.week_end)}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
