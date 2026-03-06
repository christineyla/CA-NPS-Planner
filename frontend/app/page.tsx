import Link from "next/link";

const PARK_LINKS = [
  { id: 1, name: "Yosemite National Park" },
  { id: 2, name: "Joshua Tree National Park" },
  { id: 3, name: "Death Valley National Park" },
  { id: 4, name: "Sequoia National Park" },
  { id: 5, name: "Kings Canyon National Park" },
];

export default function HomePage() {
  return (
    <main className="mx-auto min-h-screen max-w-4xl p-8">
      <h1 className="text-3xl font-semibold">California National Park Visitation Planner</h1>
      <p className="mt-3 text-slate-700">Open a park dashboard:</p>
      <ul className="mt-4 space-y-2">
        {PARK_LINKS.map((park) => (
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
