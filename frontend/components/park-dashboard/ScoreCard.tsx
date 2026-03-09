import { formatScore } from "@/lib/formatters";

interface ScoreCardProps {
  label: string;
  score: number;
  accentClass: string;
  backgroundClass?: string;
  borderClass?: string;
  subtitle?: string;
}

export function ScoreCard({ label, score, accentClass, backgroundClass = "bg-white", borderClass = "border-slate-200", subtitle }: ScoreCardProps) {
  return (
    <article className={`rounded-xl border p-4 shadow-sm ${backgroundClass} ${borderClass}`}>
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-3xl font-bold ${accentClass}`}>{formatScore(score)}</p>
      {subtitle ? <p className="mt-1 text-xs text-slate-600">{subtitle}</p> : null}
    </article>
  );
}
