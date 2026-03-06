import { CaliforniaParkMap } from "@/components/CaliforniaParkMap";
import { FeaturedInsightCards } from "@/components/FeaturedInsightCards";
import { getHomePageData } from "@/lib/api";

export default async function HomePage() {
  const { featuredCards, mapData } = await getHomePageData();

  return (
    <main className="mx-auto min-h-screen max-w-6xl space-y-8 px-6 py-10">
      <header className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">California National Park Visitation Planner</p>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900">Plan a lower-crowd California park adventure</h1>
        <p className="max-w-3xl text-slate-600">
          Explore featured recommendations and park markers generated from the planning API. Select a park on the map to inspect crowd conditions.
        </p>
      </header>

      <FeaturedInsightCards cards={featuredCards} />

      <CaliforniaParkMap markers={mapData} />
    </main>
  );
}
