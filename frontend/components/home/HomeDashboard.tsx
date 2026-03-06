"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { CaliforniaParkMap } from "@/components/home/CaliforniaParkMap";
import { FeaturedInsightCard } from "@/components/home/FeaturedInsightCard";
import { ParkAnalyticsContent } from "@/components/park-dashboard/ParkAnalyticsContent";
import { formatDateRange, formatScore } from "@/lib/formatters";
import { ForecastWeek, ParkDashboardData, ParkListItem, ParksMapDataItem } from "@/types/park-dashboard";

interface WeeklyInsight {
  park: ParkListItem;
  week: ForecastWeek;
}

interface HomeDashboardProps {
  parks: ParkListItem[];
  mapData: ParksMapDataItem[];
  dashboardData: ParkDashboardData[];
}

function selectLowestCrowdInThirtyDays(parks: ParkListItem[], forecasts: ForecastWeek[][]): WeeklyInsight | null {
  const thirtyDaysOut = new Date();
  thirtyDaysOut.setDate(thirtyDaysOut.getDate() + 30);

  let winner: WeeklyInsight | null = null;

  parks.forEach((park, index) => {
    forecasts[index]?.forEach((week) => {
      const weekStart = new Date(week.week_start);
      if (weekStart > thirtyDaysOut) {
        return;
      }

      if (winner === null || week.crowd_score < winner.week.crowd_score) {
        winner = { park, week };
      }
    });
  });

  return winner;
}

export function HomeDashboard({ parks, mapData, dashboardData }: HomeDashboardProps) {
  const [selectedParkId, setSelectedParkId] = useState<number>(parks[0]?.id ?? 1);

  const bestParkThisWeek = useMemo(
    () =>
      parks
        .filter((park) => park.trip_score !== null)
        .sort((a, b) => (b.trip_score ?? 0) - (a.trip_score ?? 0))[0],
    [parks],
  );

  const hiddenGemRecommendation = useMemo(() => {
    const hiddenGemCandidates = parks.flatMap((park, index) =>
      dashboardData[index]?.bestWeeks.hidden_gem_weeks.map((week) => ({ park, week })) ?? [],
    );

    return hiddenGemCandidates.sort((a, b) => b.week.trip_score - a.week.trip_score)[0];
  }, [dashboardData, parks]);

  const lowestCrowdThirtyDays = useMemo(
    () => selectLowestCrowdInThirtyDays(parks, dashboardData.map((park) => park.forecast)),
    [dashboardData, parks],
  );

  const selectedDashboard = dashboardData.find((park) => park.park.id === selectedParkId) ?? dashboardData[0];

  return (
    <main className="mx-auto min-h-screen max-w-6xl space-y-6 px-6 py-10">
      <header className="max-w-3xl space-y-3">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900">
          California National Park Visitation Planner
        </h1>
        <p className="text-lg text-slate-600">
          Discover lower-crowd travel windows across California&apos;s national parks using weekly forecast guidance, weather expectations, and accessibility signals.
        </p>
      </header>

      <section>
        <h2 className="mb-3 text-xl font-semibold text-slate-900">Featured insights</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {bestParkThisWeek ? (
            <FeaturedInsightCard
              title="Best park to visit this week"
              parkName={bestParkThisWeek.name}
              parkId={bestParkThisWeek.id}
              metricLabel="Trip score"
              metricValue={formatScore(bestParkThisWeek.trip_score ?? 0)}
              subtext="Top overall balance of lower crowds, favorable weather, and access this week."
            />
          ) : null}

          {hiddenGemRecommendation ? (
            <FeaturedInsightCard
              title="Hidden gem week recommendation"
              parkName={hiddenGemRecommendation.park.name}
              parkId={hiddenGemRecommendation.park.id}
              metricLabel="Recommended week"
              metricValue={formatDateRange(
                hiddenGemRecommendation.week.week_start,
                hiddenGemRecommendation.week.week_end,
              )}
              subtext={`Trip score ${formatScore(hiddenGemRecommendation.week.trip_score)} with crowd score ${formatScore(hiddenGemRecommendation.week.crowd_score)}.`}
            />
          ) : null}

          {lowestCrowdThirtyDays ? (
            <FeaturedInsightCard
              title="Lowest crowd score in next 30 days"
              parkName={lowestCrowdThirtyDays.park.name}
              parkId={lowestCrowdThirtyDays.park.id}
              metricLabel="Crowd score"
              metricValue={formatScore(lowestCrowdThirtyDays.week.crowd_score)}
              subtext={`Week of ${formatDateRange(lowestCrowdThirtyDays.week.week_start, lowestCrowdThirtyDays.week.week_end)} has the lightest projected crowds.`}
            />
          ) : null}
        </div>
      </section>

      <CaliforniaParkMap parks={mapData} selectedParkId={selectedParkId} onSelectPark={setSelectedParkId} />

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Selected park analytics</h2>
            <p className="mt-1 text-sm text-slate-600">Select a park from the dropdown or map to update the dashboard below.</p>
          </div>
          <label className="text-sm font-medium text-slate-700">
            Park selector
            <select
              className="ml-3 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
              value={selectedParkId}
              onChange={(event) => setSelectedParkId(Number(event.target.value))}
            >
              {parks.map((park) => (
                <option key={park.id} value={park.id}>
                  {park.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {selectedDashboard ? (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">{selectedDashboard.park.name} dashboard</h2>
            <Link className="text-sm text-emerald-700 hover:text-emerald-900 hover:underline" href={`/parks/${selectedDashboard.park.id}`}>
              Open direct park route
            </Link>
          </div>
          <ParkAnalyticsContent data={selectedDashboard} />
        </section>
      ) : null}
    </main>
  );
}
