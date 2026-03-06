import Link from "next/link";

import { HomeDashboard } from "@/components/home/HomeDashboard";
import { getParkDashboardData, getParks, getParksMapData } from "@/lib/parks-api";

const FALLBACK_PARK_LINKS = [
  { id: 1, name: "Yosemite National Park" },
  { id: 2, name: "Joshua Tree National Park" },
  { id: 3, name: "Death Valley National Park" },
  { id: 4, name: "Sequoia National Park" },
  { id: 5, name: "Kings Canyon National Park" },
];

export default async function HomePage() {
  try {
    const parks = await getParks();

    const [mapData, dashboardData] = await Promise.all([
      getParksMapData(),
      Promise.all(parks.map((park) => getParkDashboardData(park.id))),
    ]);

    return <HomeDashboard parks={parks} mapData={mapData} dashboardData={dashboardData} />;
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
