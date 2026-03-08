import { formatScore } from "@/lib/formatters";

interface ScoreCardProps {
  label: string;
  score: number;
  accentClass: string;
  subtitle?: string;
}

export function ScoreCard({ label, score, accentClass, subtitle }: ScoreCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-3xl font-bold ${accentClass}`}>{formatScore(score)}</p>
      {subtitle ? <p className="mt-1 text-xs text-slate-600">{subtitle}</p> : null}
    </article>
  );
}
