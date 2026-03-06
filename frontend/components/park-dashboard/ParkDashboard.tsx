import { ParkDashboardData } from "@/types/park-dashboard";

import { ParkAnalyticsContent } from "./ParkAnalyticsContent";

interface ParkDashboardProps {
  data: ParkDashboardData;
}

export function ParkDashboard({ data }: ParkDashboardProps) {
  return (
    <main className="mx-auto max-w-6xl space-y-4 p-6">
      <ParkAnalyticsContent data={data} />
    </main>
  );
}
