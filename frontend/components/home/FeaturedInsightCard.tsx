interface FeaturedInsightCardProps {
  title: string;
  parkName: string;
  metricLabel: string;
  metricValue: string;
  subtext: string;
  onSelectPark: () => void;
}

export function FeaturedInsightCard({
  title,
  parkName,
  metricLabel,
  metricValue,
  subtext,
  onSelectPark,
}: FeaturedInsightCardProps) {
  return (
    <button
      type="button"
      onClick={onSelectPark}
      className="w-full rounded-xl border border-[#C7BFB3] bg-white p-5 text-left shadow-sm transition hover:border-[#3F6B4F]/50 hover:shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3F6B4F]"
      aria-label={`Select ${parkName} and view park analytics`}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <h3 className="mt-2 text-lg font-semibold text-slate-900">{parkName}</h3>
      <p className="mt-3 text-sm text-slate-600">{subtext}</p>
      <div className="mt-4 flex items-end justify-between">
        <div>
          <p className="text-xs text-slate-500">{metricLabel}</p>
          <p className="text-2xl font-bold text-[#3F6B4F]">{metricValue}</p>
        </div>
        <p className="text-xs font-medium text-slate-500">Click to open in analytics</p>
      </div>
    </button>
  );
}
