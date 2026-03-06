"use client";

import { useState } from "react";

import { formatScore } from "@/lib/formatters";
import { AccessibilityResponse } from "@/types/park-dashboard";

interface AccessibilityDetailsModalProps {
  accessibility: AccessibilityResponse;
}

export function AccessibilityDetailsModal({ accessibility }: AccessibilityDetailsModalProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        type="button"
        onClick={() => setIsOpen(true)}
      >
        Accessibility Details
      </button>

      {isOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-lg">
            <div className="flex items-start justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Accessibility Details</h2>
              <button
                className="text-slate-500 hover:text-slate-700"
                type="button"
                onClick={() => setIsOpen(false)}
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <ul className="mt-4 space-y-2 text-sm text-slate-700">
              <li>
                <span className="font-semibold text-slate-900">Nearest major airport:</span> {accessibility.nearest_major_airport}
              </li>
              <li>
                <span className="font-semibold text-slate-900">Distance to nearest airport:</span>{" "}
                {accessibility.distance_to_nearest_airport_miles} miles
              </li>
              <li>
                <span className="font-semibold text-slate-900">Nearest city:</span> {accessibility.nearest_city}
              </li>
              <li>
                <span className="font-semibold text-slate-900">Distance / drive from nearest city:</span>{" "}
                {accessibility.distance_from_nearest_city}
              </li>
              <li>
                <span className="font-semibold text-slate-900">Road access:</span> {accessibility.road_access_description}
              </li>
              <li>
                <span className="font-semibold text-slate-900">Seasonal access:</span> {accessibility.seasonal_access_description}
              </li>
            </ul>
            <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm font-semibold text-emerald-800">
              Total accessibility score: {formatScore(accessibility.accessibility_score)}
            </p>
          </div>
        </div>
      ) : null}
    </>
  );
}
