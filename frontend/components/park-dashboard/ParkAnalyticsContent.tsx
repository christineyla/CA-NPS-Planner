import { formatScore } from "@/lib/formatters";
import { getScoreCardLabels } from "@/lib/scoreLabels";
import { ParkDashboardData } from "@/types/park-dashboard";

import { AccessibilityDetailsModal } from "./AccessibilityDetailsModal";
import { BestWeeksList } from "./BestWeeksList";
import { CrowdCalendar } from "./CrowdCalendar";
import { HistoricalForecastChart } from "./HistoricalForecastChart";
import { ParkSummaryPanel } from "./ParkSummaryPanel";
import { ScoreCard } from "./ScoreCard";

interface ParkAnalyticsContentProps {
  data: ParkDashboardData;
}

export function ParkAnalyticsContent({ data }: ParkAnalyticsContentProps) {
  const currentWeek = data.forecast[0];
  const scoreLabels = currentWeek ? getScoreCardLabels(currentWeek) : null;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-[2fr,1fr]">
        <ParkSummaryPanel park={data.park} />
        <section
          className={`rounded-xl border p-5 shadow-sm ${
            data.accessibility.accessibility_score >= 75
              ? "border-emerald-200 bg-emerald-50"
              : data.accessibility.accessibility_score >= 55
                ? "border-sky-200 bg-sky-50"
                : "border-amber-200 bg-amber-50"
          }`}
        >
          <p className="text-sm text-slate-500">Accessibility score</p>
          <p
            className={`mt-1 text-3xl font-bold ${
              data.accessibility.accessibility_score >= 75
                ? "text-emerald-700"
                : data.accessibility.accessibility_score >= 55
                  ? "text-sky-700"
                  : "text-amber-700"
            }`}
          >
            {formatScore(data.accessibility.accessibility_score)}
          </p>
          <div className="mt-4">
            <AccessibilityDetailsModal accessibility={data.accessibility} />
          </div>
        </section>
      </div>

      {currentWeek ? (
        <section className="grid gap-4 sm:grid-cols-3">
          <ScoreCard
            label="Crowding Score"
            score={currentWeek.crowd_score}
            accentClass={
              currentWeek.crowd_score <= 35
                ? "text-sky-700"
                : currentWeek.crowd_score <= 70
                  ? "text-amber-700"
                  : "text-rose-700"
            }
            backgroundClass={
              currentWeek.crowd_score <= 35
                ? "bg-sky-50"
                : currentWeek.crowd_score <= 70
                  ? "bg-amber-50"
                  : "bg-rose-50"
            }
            borderClass={
              currentWeek.crowd_score <= 35
                ? "border-sky-200"
                : currentWeek.crowd_score <= 70
                  ? "border-amber-200"
                  : "border-rose-200"
            }
            subtitle={scoreLabels?.crowd}
          />
          <ScoreCard
            label="Weather Score"
            score={currentWeek.weather_score}
            accentClass={
              currentWeek.weather_score >= 75
                ? "text-emerald-700"
                : currentWeek.weather_score >= 55
                  ? "text-sky-700"
                  : "text-amber-700"
            }
            backgroundClass={
              currentWeek.weather_score >= 75
                ? "bg-emerald-50"
                : currentWeek.weather_score >= 55
                  ? "bg-sky-50"
                  : "bg-amber-50"
            }
            borderClass={
              currentWeek.weather_score >= 75
                ? "border-emerald-200"
                : currentWeek.weather_score >= 55
                  ? "border-sky-200"
                  : "border-amber-200"
            }
            subtitle={scoreLabels?.weather}
          />
          <ScoreCard
            label="Trip Score"
            score={currentWeek.trip_score}
            accentClass={
              currentWeek.trip_score >= 75
                ? "text-emerald-700"
                : currentWeek.trip_score >= 55
                  ? "text-sky-700"
                  : "text-amber-700"
            }
            backgroundClass={
              currentWeek.trip_score >= 75
                ? "bg-emerald-50"
                : currentWeek.trip_score >= 55
                  ? "bg-sky-50"
                  : "bg-amber-50"
            }
            borderClass={
              currentWeek.trip_score >= 75
                ? "border-emerald-200"
                : currentWeek.trip_score >= 55
                  ? "border-sky-200"
                  : "border-amber-200"
            }
            subtitle={scoreLabels?.trip}
          />
        </section>
      ) : null}

      <section className="space-y-4">
        <HistoricalForecastChart forecast={data.forecast} history={data.history} />
        <BestWeeksList weeks={data.bestWeeks.top_weeks} />
      </section>

      <CrowdCalendar calendar={data.calendar} forecast={data.forecast} />
    </div>
  );
}
