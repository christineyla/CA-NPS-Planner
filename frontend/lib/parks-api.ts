import {
  AccessibilityResponse,
  AlertResponse,
  BestWeeksResponse,
  CalendarWeek,
  ForecastWeek,
  ParkDashboardData,
  ParkDetail,
  ParkListItem,
  ParksMapDataItem,
  VisitationHistoryPoint,
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

export function getParks(): Promise<ParkListItem[]> {
  return fetchApi<ParkListItem[]>("/parks");
}

export function getParksMapData(): Promise<ParksMapDataItem[]> {
  return fetchApi<ParksMapDataItem[]>("/parks/map-data");
}

export function getParkBestWeeks(parkId: number): Promise<BestWeeksResponse> {
  return fetchApi<BestWeeksResponse>(`/parks/${parkId}/best-weeks`);
}

export function getParkForecast(parkId: number): Promise<ForecastWeek[]> {
  return fetchApi<ForecastWeek[]>(`/parks/${parkId}/forecast`);
}

export async function getParkDashboardData(parkId: number): Promise<ParkDashboardData> {
  const [park, forecast, history, bestWeeks, calendar, alerts, accessibility] = await Promise.all([
    fetchApi<ParkDetail>(`/parks/${parkId}`),
    fetchApi<ForecastWeek[]>(`/parks/${parkId}/forecast`),
    fetchApi<VisitationHistoryPoint[]>(`/parks/${parkId}/visitation-history`),
    fetchApi<BestWeeksResponse>(`/parks/${parkId}/best-weeks`),
    fetchApi<CalendarWeek[]>(`/parks/${parkId}/calendar`),
    fetchApi<AlertResponse[]>(`/parks/${parkId}/alerts`),
    fetchApi<AccessibilityResponse>(`/parks/${parkId}/accessibility`),
  ]);

  return {
    park,
    forecast,
    history,
    bestWeeks,
    calendar,
    alerts,
    accessibility,
  };
}


export function getValidationExportUrl(): string {
  return `${API_BASE_URL}/parks/validation/export`;
}
