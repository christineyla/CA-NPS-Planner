import {
  AccessibilityResponse,
  AlertResponse,
  BestWeeksResponse,
  CalendarWeek,
  ForecastWeek,
  ParkDashboardData,
  ParkDetail,
} from "@/types/park-dashboard";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function fetchApi<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed (${response.status}) for ${path}`);
  }

  return (await response.json()) as T;
}

export async function getParkDashboardData(parkId: number): Promise<ParkDashboardData> {
  const [park, forecast, bestWeeks, calendar, alerts, accessibility] = await Promise.all([
    fetchApi<ParkDetail>(`/parks/${parkId}`),
    fetchApi<ForecastWeek[]>(`/parks/${parkId}/forecast`),
    fetchApi<BestWeeksResponse>(`/parks/${parkId}/best-weeks`),
    fetchApi<CalendarWeek[]>(`/parks/${parkId}/calendar`),
    fetchApi<AlertResponse[]>(`/parks/${parkId}/alerts`),
    fetchApi<AccessibilityResponse>(`/parks/${parkId}/accessibility`),
  ]);

  return {
    park,
    forecast,
    bestWeeks,
    calendar,
    alerts,
    accessibility,
  };
}
