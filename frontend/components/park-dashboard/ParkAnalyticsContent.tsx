import { formatScore } from "@/lib/formatters";
import { ParkDashboardData } from "@/types/park-dashboard";

import { AccessibilityDetailsModal } from "./AccessibilityDetailsModal";
import { AlertBanner } from "./AlertBanner";
import { BestWeeksList } from "./BestWeeksList";
import { CrowdCalendar } from "./CrowdCalendar";
import { HiddenGemBadges } from "./HiddenGemBadges";
import { HistoricalForecastChart } from "./HistoricalForecastChart";
import { ParkSummaryPanel } from "./ParkSummaryPanel";
import { ScoreCard } from "./ScoreCard";

interface ParkAnalyticsContentProps {
  data: ParkDashboardData;
}

export function ParkAnalyticsContent({ data }: ParkAnalyticsContentProps) {
  const currentWeek = data.forecast[0];

  return (
    <div className="space-y-4">
      <AlertBanner alerts={data.alerts} />

      <div className="grid gap-4 lg:grid-cols-[2fr,1fr]">
        <ParkSummaryPanel park={data.park} />
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Accessibility score</p>
          <p className="mt-1 text-3xl font-bold text-indigo-700">
            {formatScore(data.accessibility.accessibility_score)}
          </p>
          <div className="mt-4">
            <AccessibilityDetailsModal accessibility={data.accessibility} />
          </div>
        </section>
      </div>

      {currentWeek ? (
        <section className="grid gap-4 sm:grid-cols-3">
          <ScoreCard label="Crowd Score" score={currentWeek.crowd_score} accentClass="text-rose-700" />
          <ScoreCard label="Weather Score" score={currentWeek.weather_score} accentClass="text-sky-700" />
          <ScoreCard label="Trip Score" score={currentWeek.trip_score} accentClass="text-emerald-700" />
        </section>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <HistoricalForecastChart forecast={data.forecast} history={data.history} />
        <BestWeeksList weeks={data.bestWeeks.top_weeks} />
      </div>

      <HiddenGemBadges weeks={data.bestWeeks.hidden_gem_weeks} />
      <CrowdCalendar calendar={data.calendar} forecast={data.forecast} />
    </div>
  );
}
