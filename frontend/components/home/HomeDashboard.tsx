"use client";

import { useMemo, useRef, useState } from "react";

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

function selectBestWeatherInThirtyDays(parks: ParkListItem[], forecasts: ForecastWeek[][]): WeeklyInsight | null {
  const thirtyDaysOut = new Date();
  thirtyDaysOut.setDate(thirtyDaysOut.getDate() + 30);

  let winner: WeeklyInsight | null = null;

  parks.forEach((park, index) => {
    forecasts[index]?.forEach((week) => {
      const weekStart = new Date(week.week_start);
      if (weekStart > thirtyDaysOut) {
        return;
      }

      if (winner === null || week.weather_score > winner.week.weather_score) {
        winner = { park, week };
      }
    });
  });

  return winner;
}


function buildTripScoreExplanation(tripScore: number | null): string {
  if (tripScore === null) {
    return "Balanced crowd, weather, and access signals support this recommendation.";
  }

  if (tripScore >= 75) {
    return "Low crowds and comfortable weather make this a strong week to visit.";
  }

  if (tripScore >= 60) {
    return "This park combines manageable visitation with favorable near-term conditions.";
  }

  return "A steadier mix of access, weather, and crowds makes this park a practical pick.";
}

function buildCrowdInsightExplanation(crowdScore: number): string {
  if (crowdScore <= 30) {
    return "Lower crowd pressure than other parks over the next 30 days.";
  }

  return "This park still trends less crowded than nearby alternatives this month.";
}

function buildWeatherInsightExplanation(weatherScore: number, crowdScore: number): string {
  if (weatherScore >= 75 && crowdScore <= 45) {
    return "This park combines relatively low visitation with improving seasonal conditions.";
  }

  if (weatherScore >= 75) {
    return "Comfort-focused weather conditions lift this week above other near-term options.";
  }

  return "Weather trends remain comparatively favorable for planning in the coming weeks.";
}

export function HomeDashboard({ parks, mapData, dashboardData }: HomeDashboardProps) {
  const [selectedParkId, setSelectedParkId] = useState<number>(parks[0]?.id ?? 1);
  const analyticsSectionRef = useRef<HTMLElement | null>(null);

  const selectParkAndScroll = (parkId: number) => {
    setSelectedParkId(parkId);

    analyticsSectionRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const bestParkThisWeek = useMemo(
    () =>
      parks
        .filter((park) => park.trip_score !== null)
        .sort((a, b) => (b.trip_score ?? 0) - (a.trip_score ?? 0))[0],
    [parks],
  );

  const lowestCrowdThirtyDays = useMemo(
    () => selectLowestCrowdInThirtyDays(parks, dashboardData.map((park) => park.forecast)),
    [dashboardData, parks],
  );

  const bestWeatherThirtyDays = useMemo(
    () => selectBestWeatherInThirtyDays(parks, dashboardData.map((park) => park.forecast)),
    [dashboardData, parks],
  );

  const selectedDashboard = dashboardData.find((park) => park.park.id === selectedParkId) ?? dashboardData[0];

  return (
    <main className="min-h-screen bg-[#F7F4EE]">
      <div className="mx-auto max-w-6xl space-y-6 px-6 py-10">
        <header className="max-w-3xl space-y-3">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">
            California National Park Visitation Planner
          </h1>
          <p className="text-lg text-slate-600">
            Discover lower-crowd travel windows across California&apos;s national parks using weekly forecast guidance,
            weather expectations, and accessibility signals.
          </p>
        </header>

        <section className="space-y-6 rounded-3xl border border-[#D5CCBF] bg-[#EFE9DD] p-6 shadow-sm md:p-8">
          <div>
            <h2 className="mb-3 text-xl font-semibold text-slate-900">Featured insights</h2>
            <p className="mb-3 text-sm text-slate-600">
              Click any insight card to load that park in the analytics section below.
            </p>
            <div className="grid gap-4 md:grid-cols-3">
              {bestParkThisWeek ? (
                <FeaturedInsightCard
                  title="Best park to visit this week"
                  parkName={bestParkThisWeek.name}
                  metricLabel="Trip score"
                  metricValue={formatScore(bestParkThisWeek.trip_score ?? 0)}
                  subtext="Top overall balance of lower crowds, favorable weather, and access this week."
                  explanation={buildTripScoreExplanation(bestParkThisWeek.trip_score)}
                  onSelectPark={() => selectParkAndScroll(bestParkThisWeek.id)}
                />
              ) : null}

              {lowestCrowdThirtyDays ? (
                <FeaturedInsightCard
                  title="Lowest crowd score in next 30 days"
                  parkName={lowestCrowdThirtyDays.park.name}
                  metricLabel="Crowd score"
                  metricValue={formatScore(lowestCrowdThirtyDays.week.crowd_score)}
                  subtext={`Week of ${formatDateRange(lowestCrowdThirtyDays.week.week_start, lowestCrowdThirtyDays.week.week_end)} has the lightest projected crowds.`}
                  explanation={buildCrowdInsightExplanation(lowestCrowdThirtyDays.week.crowd_score)}
                  onSelectPark={() => selectParkAndScroll(lowestCrowdThirtyDays.park.id)}
                />
              ) : null}

              {bestWeatherThirtyDays ? (
                <FeaturedInsightCard
                  title="Best weather score in next 30 days"
                  parkName={bestWeatherThirtyDays.park.name}
                  metricLabel="Weather score"
                  metricValue={formatScore(bestWeatherThirtyDays.week.weather_score)}
                  subtext={`Week of ${formatDateRange(bestWeatherThirtyDays.week.week_start, bestWeatherThirtyDays.week.week_end)} has the strongest expected weather comfort.`}
                  explanation={buildWeatherInsightExplanation(bestWeatherThirtyDays.week.weather_score, bestWeatherThirtyDays.week.crowd_score)}
                  onSelectPark={() => selectParkAndScroll(bestWeatherThirtyDays.park.id)}
                />
              ) : null}
            </div>
          </div>

          <CaliforniaParkMap parks={mapData} selectedParkId={selectedParkId} onSelectPark={setSelectedParkId} />
        </section>

        <section
          ref={analyticsSectionRef}
          className="space-y-6 rounded-3xl border border-[#D7CFC2] bg-[#E7EEDF] p-6 shadow-sm md:p-8"
        >
          <section className="rounded-xl border border-[#C7BFB3] bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Selected park analytics</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Select a park from the dropdown or map to update the dashboard below.
                </p>
              </div>
              <label className="text-sm font-medium text-slate-700">
                Park selector
                <select
                  className="ml-3 rounded-md border border-[#C7BFB3] bg-white px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3F6B4F]"
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
              </div>
              <ParkAnalyticsContent data={selectedDashboard} />
            </section>
          ) : null}
        </section>
      </div>
    </main>
  );
}
