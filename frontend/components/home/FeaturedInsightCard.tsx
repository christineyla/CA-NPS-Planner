import Link from "next/link";

interface FeaturedInsightCardProps {
  title: string;
  parkName: string;
  parkId: number;
  metricLabel: string;
  metricValue: string;
  subtext: string;
}

export function FeaturedInsightCard({
  title,
  parkName,
  parkId,
  metricLabel,
  metricValue,
  subtext,
}: FeaturedInsightCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <h3 className="mt-2 text-lg font-semibold text-slate-900">{parkName}</h3>
      <p className="mt-3 text-sm text-slate-600">{subtext}</p>
      <div className="mt-4 flex items-end justify-between">
        <div>
          <p className="text-xs text-slate-500">{metricLabel}</p>
          <p className="text-2xl font-bold text-emerald-700">{metricValue}</p>
        </div>
        <Link
          href={`/parks/${parkId}`}
          className="text-sm font-medium text-emerald-700 hover:text-emerald-900 hover:underline"
        >
          View dashboard
        </Link>
      </div>
    </article>
  );
}
