import Link from "next/link";
import { notFound } from "next/navigation";

import { ParkDashboard } from "@/components/park-dashboard/ParkDashboard";
import { getParkDashboardData } from "@/lib/parks-api";

interface ParkDetailPageProps {
  params: {
    parkId: string;
  };
}

export default async function ParkDetailPage({ params }: ParkDetailPageProps) {
  const parkId = Number(params.parkId);
  if (!Number.isInteger(parkId) || parkId <= 0) {
    notFound();
  }

  try {
    const data = await getParkDashboardData(parkId);

    return (
      <>
        <div className="mx-auto max-w-6xl px-6 pt-6">
          <Link href="/" className="text-sm text-slate-600 hover:text-slate-900">
            ← Back to homepage
          </Link>
        </div>
        <ParkDashboard data={data} />
      </>
    );
  } catch {
    return (
      <main className="mx-auto max-w-3xl p-6">
        <h1 className="text-2xl font-semibold text-slate-900">Park dashboard unavailable</h1>
        <p className="mt-2 text-slate-600">
          We could not load park data from the backend API. Verify that the FastAPI service is
          running and NEXT_PUBLIC_API_BASE_URL is configured.
        </p>
      </main>
    );
  }
}
