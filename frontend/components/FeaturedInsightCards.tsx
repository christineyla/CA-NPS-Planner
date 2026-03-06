import type { FeaturedCard } from "@/types/parks";

type FeaturedInsightCardsProps = {
  cards: FeaturedCard[];
};

export function FeaturedInsightCards({ cards }: FeaturedInsightCardsProps) {
  return (
    <section aria-label="Featured recommendations" className="grid gap-4 md:grid-cols-3">
      {cards.map((card) => (
        <article key={card.title} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Featured</p>
          <h2 className="mt-2 text-lg font-semibold text-slate-900">{card.title}</h2>
          <p className="mt-3 text-sm font-medium text-slate-600">{card.parkName}</p>
          <div className="mt-2">
            <p className="text-xs text-slate-500">{card.metricLabel}</p>
            <p className="text-2xl font-bold text-slate-900">{card.metricValue}</p>
          </div>
          <p className="mt-3 text-sm text-slate-600">{card.detail}</p>
        </article>
      ))}
    </section>
  );
}
