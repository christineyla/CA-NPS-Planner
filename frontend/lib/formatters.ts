export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function formatDateRange(start: string, end: string): string {
  return `${formatDate(start)} - ${formatDate(end)}`;
}

export function formatScore(score: number): string {
  return `${Math.round(score)}/100`;
}

export function formatVisits(visits: number): string {
  return new Intl.NumberFormat("en-US").format(visits);
}
