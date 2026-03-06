import { AlertResponse } from "@/types/park-dashboard";

const severityColor: Record<AlertResponse["severity"], string> = {
  yellow: "bg-yellow-50 border-yellow-300 text-yellow-900",
  orange: "bg-orange-50 border-orange-200 text-orange-900",
  red: "bg-red-50 border-red-200 text-red-900",
};

interface AlertBannerProps {
  alerts: AlertResponse[];
}

export function AlertBanner({ alerts }: AlertBannerProps) {
  const activeAlerts = alerts.filter((alert) => alert.is_active);
  if (activeAlerts.length === 0) {
    return null;
  }

  const primaryAlert = activeAlerts[0];

  return (
    <div className={`rounded-xl border p-4 shadow-sm ${severityColor[primaryAlert.severity]}`}>
      <p className="text-xs font-semibold uppercase tracking-wide">{`${primaryAlert.severity.toUpperCase()} Alert`}</p>
      <h2 className="mt-1 text-lg font-semibold">{primaryAlert.title}</h2>
      <p className="mt-1 text-sm">{primaryAlert.message}</p>
    </div>
  );
}
