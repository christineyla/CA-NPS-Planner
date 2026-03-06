export type ParkListItem = {
  id: number;
  name: string;
  slug: string;
  state: string;
  latitude: number;
  longitude: number;
  accessibility_score: number;
  crowd_score: number | null;
  trip_score: number | null;
};

export type ParksMapDataItem = {
  park_id: number;
  name: string;
  slug: string;
  latitude: number;
  longitude: number;
  crowd_score: number | null;
  crowd_level: "low" | "moderate" | "busy" | "extreme" | null;
};

export type ForecastWeek = {
  week_start: string;
  week_end: string;
  predicted_visits: number;
  crowd_score: number;
  weather_score: number;
  accessibility_score: number;
  trip_score: number;
};

export type BestWeeksResponse = {
  top_weeks: ForecastWeek[];
  hidden_gem_weeks: ForecastWeek[];
};

export type FeaturedCard = {
  title: string;
  parkName: string;
  metricLabel: string;
  metricValue: string;
  detail: string;
};

export type HomePageData = {
  featuredCards: FeaturedCard[];
  mapData: ParksMapDataItem[];
};
