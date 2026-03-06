import Link from "next/link";

import { CaliforniaParkMap } from "@/components/home/CaliforniaParkMap";
import { FeaturedInsightCard } from "@/components/home/FeaturedInsightCard";
import { formatDateRange, formatScore } from "@/lib/formatters";
import { getParkBestWeeks, getParkForecast, getParks, getParksMapData } from "@/lib/parks-api";
import { ForecastWeek, ParkListItem } from "@/types/park-dashboard";

interface WeeklyInsight {
  park: ParkListItem;
  week: ForecastWeek;
}

const FALLBACK_PARK_LINKS = [
  { id: 1, name: "Yosemite National Park" },
  { id: 2, name: "Joshua Tree National Park" },
  { id: 3, name: "Death Valley National Park" },
  { id: 4, name: "Sequoia National Park" },
  { id: 5, name: "Kings Canyon National Park" },
];

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

export default async function HomePage() {
  try {
    const parks = await getParks();

    const [mapData, bestWeeksByPark, forecastsByPark] = await Promise.all([
      getParksMapData(),
      Promise.all(parks.map((park) => getParkBestWeeks(park.id))),
      Promise.all(parks.map((park) => getParkForecast(park.id))),
    ]);

    const bestParkThisWeek = parks
      .filter((park) => park.trip_score !== null)
      .sort((a, b) => (b.trip_score ?? 0) - (a.trip_score ?? 0))[0];

    const hiddenGemCandidates = parks.flatMap((park, index) =>
      bestWeeksByPark[index].hidden_gem_weeks.map((week) => ({ park, week })),
    );

    const hiddenGemRecommendation = hiddenGemCandidates.sort(
      (a, b) => b.week.trip_score - a.week.trip_score,
    )[0];

    const lowestCrowdThirtyDays = selectLowestCrowdInThirtyDays(parks, forecastsByPark);

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

        <CaliforniaParkMap parks={mapData} />

        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Park dashboards</h2>
          <p className="mt-1 text-sm text-slate-600">Jump directly into each park&apos;s detailed 26-week forecast and visit planning tools.</p>
          <ul className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {parks.map((park) => (
              <li key={park.id}>
                <Link className="text-emerald-700 hover:text-emerald-900 hover:underline" href={`/parks/${park.id}`}>
                  {park.name}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </main>
    );
  } catch {
    return (
      <main className="mx-auto min-h-screen max-w-4xl p-8">
        <h1 className="text-3xl font-semibold">California National Park Visitation Planner</h1>
        <p className="mt-3 text-slate-700">
          Live insight data is temporarily unavailable. You can still open park dashboards:
        </p>
        <ul className="mt-4 space-y-2">
          {FALLBACK_PARK_LINKS.map((park) => (
            <li key={park.id}>
              <Link className="text-emerald-700 hover:text-emerald-900 hover:underline" href={`/parks/${park.id}`}>
                {park.name}
              </Link>
            </li>
          ))}
        </ul>
      </main>
    );
  }
}
