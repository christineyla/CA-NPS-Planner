import { formatDateRange } from "@/lib/formatters";
import { ForecastWeek } from "@/types/park-dashboard";

interface HiddenGemBadgesProps {
  weeks: ForecastWeek[];
}

export function HiddenGemBadges({ weeks }: HiddenGemBadgesProps) {
  if (weeks.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Hidden Gem Weeks</h2>
      <div className="mt-3 flex flex-wrap gap-2">
        {weeks.map((week) => (
          <span
            key={`${week.week_start}-${week.week_end}`}
            className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800"
          >
            {formatDateRange(week.week_start, week.week_end)}
          </span>
        ))}
      </div>
    </section>
  );
}
