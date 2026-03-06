import { formatDateRange } from "@/lib/formatters";
import { CalendarWeek, ForecastWeek } from "@/types/park-dashboard";

interface CrowdCalendarProps {
  calendar: CalendarWeek[];
  forecast: ForecastWeek[];
}

interface CalendarMonthGroup {
  monthKey: string;
  monthLabel: string;
  weeks: CalendarWeek[];
}

const monthLabelFormatter = new Intl.DateTimeFormat("en-US", {
  month: "long",
  year: "numeric",
});

export function CrowdCalendar({ calendar, forecast }: CrowdCalendarProps) {
  const scoreByWeek = new Map(forecast.map((week) => [week.week_start, week]));

  const monthGroups = calendar.reduce<CalendarMonthGroup[]>((groups, week) => {
    const weekDate = new Date(week.week_start);
    const monthKey = `${weekDate.getFullYear()}-${weekDate.getMonth()}`;
    const monthLabel = monthLabelFormatter.format(weekDate);
    const currentGroup = groups[groups.length - 1];

    if (!currentGroup || currentGroup.monthKey !== monthKey) {
      groups.push({ monthKey, monthLabel, weeks: [week] });
      return groups;
    }

    currentGroup.weeks.push(week);
    return groups;
  }, []);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Crowd Calendar (6 months)</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {monthGroups.map((monthGroup) => (
          <section key={monthGroup.monthKey} className="rounded-lg border border-slate-200/90 bg-slate-50/70 p-3">
            <h3 className="border-b border-slate-200 pb-2 text-sm font-semibold text-slate-800">{monthGroup.monthLabel}</h3>
            <div className="mt-3 space-y-2">
              {monthGroup.weeks.map((week) => {
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
        ))}
      </div>
    </section>
  );
}
