import type {
  BestWeeksResponse,
  FeaturedCard,
  ForecastWeek,
  HomePageData,
  ParkListItem,
  ParksMapDataItem,
} from "@/types/parks";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const fallbackMapData: ParksMapDataItem[] = [
  { park_id: 1, name: "Yosemite National Park", slug: "yosemite", latitude: 37.8651, longitude: -119.5383, crowd_score: null, crowd_level: null },
  { park_id: 2, name: "Joshua Tree National Park", slug: "joshua-tree", latitude: 33.8734, longitude: -115.901, crowd_score: null, crowd_level: null },
  { park_id: 3, name: "Death Valley National Park", slug: "death-valley", latitude: 36.5054, longitude: -117.0794, crowd_score: null, crowd_level: null },
  { park_id: 4, name: "Sequoia National Park", slug: "sequoia", latitude: 36.4864, longitude: -118.5658, crowd_score: null, crowd_level: null },
  { park_id: 5, name: "Kings Canyon National Park", slug: "kings-canyon", latitude: 36.8879, longitude: -118.5551, crowd_score: null, crowd_level: null },
];

async function fetchJson<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    next: { revalidate: 60 },
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${endpoint} (${response.status})`);
  }

  return (await response.json()) as T;
}

function formatDateRange(week: ForecastWeek): string {
  const start = new Date(week.week_start).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
  const end = new Date(week.week_end).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
  return `${start}–${end}`;
}

export async function getHomePageData(): Promise<HomePageData> {
  const parksResult = await Promise.allSettled([
    fetchJson<ParkListItem[]>("/parks"),
    fetchJson<ParksMapDataItem[]>("/parks/map-data"),
  ]);

  const parks = parksResult[0].status === "fulfilled" ? parksResult[0].value : [];
  const mapData = parksResult[1].status === "fulfilled" ? parksResult[1].value : fallbackMapData;

  if (parks.length === 0) {
    return {
      mapData,
      featuredCards: [
        {
          title: "Best park to visit this week",
          parkName: "Data unavailable",
          metricLabel: "Trip score",
          metricValue: "--",
          detail: "Connect the frontend to the backend API to see live recommendations.",
        },
        {
          title: "Hidden gem week recommendation",
          parkName: "Data unavailable",
          metricLabel: "Crowd / Weather",
          metricValue: "--",
          detail: "No hidden gem data available.",
        },
        {
          title: "Lowest crowd score in next 30 days",
          parkName: "Data unavailable",
          metricLabel: "Crowd score",
          metricValue: "--",
          detail: "No forecast data available.",
        },
      ],
    };
  }

  const bestParkThisWeek = [...parks]
    .filter((park) => park.trip_score !== null)
    .sort((a, b) => (b.trip_score ?? 0) - (a.trip_score ?? 0))[0];

  const perParkData = await Promise.all(
    parks.map(async (park) => {
      const [bestWeeks, forecast] = await Promise.allSettled([
        fetchJson<BestWeeksResponse>(`/parks/${park.id}/best-weeks`),
        fetchJson<ForecastWeek[]>(`/parks/${park.id}/forecast`),
      ]);

      return {
        park,
        bestWeeks: bestWeeks.status === "fulfilled" ? bestWeeks.value : null,
        forecast: forecast.status === "fulfilled" ? forecast.value : [],
      };
    }),
  );

  const hiddenGemCandidate = perParkData
    .flatMap(({ park, bestWeeks }) =>
      (bestWeeks?.hidden_gem_weeks ?? []).map((week) => ({ parkName: park.name, week })),
    )
    .sort((a, b) => b.week.trip_score - a.week.trip_score)[0];

  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() + 30);

  const lowestCrowdCandidate = perParkData
    .flatMap(({ park, forecast }) =>
      forecast
        .filter((week) => new Date(week.week_start) <= cutoff)
        .map((week) => ({ parkName: park.name, week })),
    )
    .sort((a, b) => a.week.crowd_score - b.week.crowd_score)[0];

  const featuredCards: FeaturedCard[] = [
    {
      title: "Best park to visit this week",
      parkName: bestParkThisWeek?.name ?? "Unavailable",
      metricLabel: "Trip score",
      metricValue: bestParkThisWeek?.trip_score ? bestParkThisWeek.trip_score.toFixed(1) : "--",
      detail: bestParkThisWeek?.crowd_score
        ? `Current crowd score: ${bestParkThisWeek.crowd_score.toFixed(1)}`
        : "Crowd score unavailable",
    },
    {
      title: "Hidden gem week recommendation",
      parkName: hiddenGemCandidate?.parkName ?? "Unavailable",
      metricLabel: "Week",
      metricValue: hiddenGemCandidate ? formatDateRange(hiddenGemCandidate.week) : "--",
      detail: hiddenGemCandidate
        ? `Crowd ${hiddenGemCandidate.week.crowd_score.toFixed(1)} · Weather ${hiddenGemCandidate.week.weather_score.toFixed(1)}`
        : "No hidden gem week found",
    },
    {
      title: "Lowest crowd score in next 30 days",
      parkName: lowestCrowdCandidate?.parkName ?? "Unavailable",
      metricLabel: "Crowd score",
      metricValue: lowestCrowdCandidate ? lowestCrowdCandidate.week.crowd_score.toFixed(1) : "--",
      detail: lowestCrowdCandidate ? formatDateRange(lowestCrowdCandidate.week) : "No near-term forecast available",
    },
  ];

  return {
    featuredCards,
    mapData,
  };
}
