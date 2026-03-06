import { ParkDetail } from "@/types/park-dashboard";

interface ParkSummaryPanelProps {
  park: ParkDetail;
}

export function ParkSummaryPanel({ park }: ParkSummaryPanelProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">{park.name}</h1>
      <p className="mt-1 text-slate-600">{park.state}</p>
      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-slate-500">Latitude</dt>
          <dd className="font-medium text-slate-800">{park.latitude.toFixed(3)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Longitude</dt>
          <dd className="font-medium text-slate-800">{park.longitude.toFixed(3)}</dd>
        </div>
      </dl>
    </section>
  );
}
