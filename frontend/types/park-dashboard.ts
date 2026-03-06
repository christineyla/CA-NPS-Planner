export interface ParkDetail {
  id: number;
  name: string;
  slug: string;
  state: string;
  latitude: number;
  longitude: number;
  airport_access_score: number;
  drive_access_score: number;
  road_access_score: number;
  seasonal_access_score: number;
  accessibility_score: number;
}

export interface ForecastWeek {
  week_start: string;
  week_end: string;
  predicted_visits: number;
  crowd_score: number;
  weather_score: number;
  accessibility_score: number;
  trip_score: number;
}

export interface BestWeeksResponse {
  top_weeks: ForecastWeek[];
  hidden_gem_weeks: ForecastWeek[];
}

export interface CalendarWeek {
  forecast_id: number;
  week_start: string;
  week_end: string;
  crowd_level: "low" | "moderate" | "busy" | "extreme";
  color_hex: string;
  crowd_score: number;
}

export interface AlertResponse {
  id: number;
  title: string;
  severity: "low" | "moderate" | "high" | "severe";
  message: string;
  starts_on: string;
  ends_on: string;
  is_active: boolean;
}

export interface AccessibilityResponse {
  airport_access_score: number;
  drive_access_score: number;
  road_access_score: number;
  seasonal_access_score: number;
  accessibility_score: number;
}

export interface ParkDashboardData {
  park: ParkDetail;
  forecast: ForecastWeek[];
  bestWeeks: BestWeeksResponse;
  calendar: CalendarWeek[];
  alerts: AlertResponse[];
  accessibility: AccessibilityResponse;
}
