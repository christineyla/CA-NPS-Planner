"use client";

import { useState } from "react";

import { formatVisits } from "@/lib/formatters";
import { ForecastWeek, VisitationHistoryPoint } from "@/types/park-dashboard";

interface HistoricalForecastChartProps {
  forecast: ForecastWeek[];
  history: VisitationHistoryPoint[];
}

type PointType = "history" | "forecast";

interface ChartPoint {
  date: Date;
  endDate: Date | null;
  label: string;
  visits: number;
  displayLabel: string;
  type: PointType;
  lower: number | null;
  upper: number | null;
}

const CHART_WIDTH = 900;
const CHART_HEIGHT = 260;
const LEFT_PADDING = 62;
const RIGHT_PADDING = 62;
const TOP_PADDING = 20;
const BOTTOM_PADDING = 38;
const X_AXIS_LABEL_ROTATION_DEGREES = -24;

function formatLabel(date: Date): string {
  return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

function formatWeekRange(startDate: Date, endDate: Date | null): string {
  if (!endDate) {
    return startDate.toLocaleDateString("en-US", { month: "short", year: "numeric" });
  }

  return `${startDate.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  })} - ${endDate.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`;
}

function getWeeksInMonth(date: Date): number {
  const year = date.getFullYear();
  const month = date.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  return daysInMonth / 7;
}

function toChartPoints(history: VisitationHistoryPoint[], forecast: ForecastWeek[]): ChartPoint[] {
  const historyPoints = history.map((entry) => {
    const date = new Date(entry.observation_month);
    const weeklyEquivalentVisits = entry.visits / getWeeksInMonth(date);

    return {
      date,
      endDate: null,
      label: formatLabel(date),
      visits: weeklyEquivalentVisits,
      displayLabel: "Historical (weekly-equivalent from monthly total)",
      type: "history" as const,
      lower: null,
      upper: null,
    };
  });

  const forecastPoints = forecast.slice(0, 26).map((week) => {
    const date = new Date(week.week_start);
    return {
      date,
      endDate: new Date(week.week_end),
      label: formatLabel(date),
      visits: week.predicted_visits,
      displayLabel: "Forecast",
      type: "forecast" as const,
      lower: week.predicted_visits_lower ?? null,
      upper: week.predicted_visits_upper ?? null,
    };
  });

  return [...historyPoints, ...forecastPoints].sort((a, b) => a.date.getTime() - b.date.getTime());
}

function pointToCoordinate(value: number, index: number, count: number, maxValue: number): [number, number] {
  const x = LEFT_PADDING + (index * (CHART_WIDTH - LEFT_PADDING - RIGHT_PADDING)) / Math.max(count - 1, 1);
  const y = CHART_HEIGHT - BOTTOM_PADDING - (value / maxValue) * (CHART_HEIGHT - TOP_PADDING - BOTTOM_PADDING);
  return [x, y];
}

function shouldRenderXAxisLabel(points: ChartPoint[], pointIndex: number, forecastStartIndex: number): boolean {
  const point = points[pointIndex];
  if (!point) {
    return false;
  }

  if (pointIndex === points.length - 1) {
    return true;
  }

  const isHistoryPoint = point.type === "history";
  if (isHistoryPoint) {
    if (pointIndex === 0) {
      return true;
    }

    const month = point.date.getMonth();
    const isQuarterStart = month % 3 === 0;
    const isFinalHistoryPoint = forecastStartIndex > 0 && pointIndex === forecastStartIndex - 1;
    return isQuarterStart || isFinalHistoryPoint;
  }

  const previousForecastPoint = points.slice(0, pointIndex).reverse().find((candidate) => candidate.type === "forecast");
  if (!previousForecastPoint) {
    return true;
  }

  const isNewMonth =
    point.date.getMonth() !== previousForecastPoint.date.getMonth() ||
    point.date.getFullYear() !== previousForecastPoint.date.getFullYear();

  if (!isNewMonth) {
    return false;
  }

  const shouldThinFarRightLabels = pointIndex > points.length - 7;

  if (shouldThinFarRightLabels) {
    return point.date.getMonth() % 2 === 0;
  }

  return true;
}

function buildPath(points: ChartPoint[], maxValue: number, type: PointType): string {
  const filtered = points
    .map((point, index) => ({ point, index }))
    .filter(({ point }) => point.type === type);

  return filtered
    .map(({ point, index }, pathIndex) => {
      const [x, y] = pointToCoordinate(point.visits, index, points.length, maxValue);
      return `${pathIndex === 0 ? "M" : "L"}${x} ${y}`;
    })
    .join(" ");
}

function buildConfidenceBand(points: ChartPoint[], maxValue: number): string | null {
  const forecast = points
    .map((point, index) => ({ point, index }))
    .filter(({ point }) => point.type === "forecast" && point.lower !== null && point.upper !== null);

  if (forecast.length < 2) {
    return null;
  }

  const upperPath = forecast
    .map(({ point, index }, pathIndex) => {
      const [x, y] = pointToCoordinate(point.upper ?? point.visits, index, points.length, maxValue);
      return `${pathIndex === 0 ? "M" : "L"}${x} ${y}`;
    })
    .join(" ");

  const lowerPath = forecast
    .slice()
    .reverse()
    .map(({ point, index }) => {
      const [x, y] = pointToCoordinate(point.lower ?? point.visits, index, points.length, maxValue);
      return `L${x} ${y}`;
    })
    .join(" ");

  return `${upperPath} ${lowerPath} Z`;
}

export function HistoricalForecastChart({ forecast, history }: HistoricalForecastChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const points = toChartPoints(history, forecast);

  if (points.length === 0) {
    return null;
  }

  const maxValue = Math.max(...points.map((point) => point.upper ?? point.visits), 1);
  const minForecastIndex = points.findIndex((point) => point.type === "forecast");
  const forecastStartX =
    minForecastIndex >= 0
      ? LEFT_PADDING + (minForecastIndex * (CHART_WIDTH - LEFT_PADDING - RIGHT_PADDING)) / Math.max(points.length - 1, 1)
      : null;

  const confidenceBandPath = buildConfidenceBand(points, maxValue);
  const positionedPoints = points.map((point, index) => ({ point, index, coordinates: pointToCoordinate(point.visits, index, points.length, maxValue) }));
  const activePoint = activeIndex !== null ? positionedPoints[activeIndex] : null;

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Historical + Forecast Visits</h2>
      <p className="mt-1 text-xs text-slate-500">Historical monthly visitation shown as weekly-equivalent values with forecasted weekly trends for the selected park.</p>
      <div className="mt-3 rounded-md border border-slate-100 p-2">
        <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} className="h-72 w-full" role="img" aria-label="Historical and forecast visits line chart">
          <line
            x1={LEFT_PADDING}
            y1={CHART_HEIGHT - BOTTOM_PADDING}
            x2={CHART_WIDTH - RIGHT_PADDING}
            y2={CHART_HEIGHT - BOTTOM_PADDING}
            className="stroke-slate-300"
            strokeWidth="1"
          />
          <line x1={LEFT_PADDING} y1={TOP_PADDING} x2={LEFT_PADDING} y2={CHART_HEIGHT - BOTTOM_PADDING} className="stroke-slate-300" strokeWidth="1" />

          {forecastStartX ? (
            <rect
              x={forecastStartX}
              y={TOP_PADDING}
              width={CHART_WIDTH - RIGHT_PADDING - forecastStartX}
              height={CHART_HEIGHT - TOP_PADDING - BOTTOM_PADDING}
              className="fill-emerald-500/5"
            />
          ) : null}

          <text
            x={14}
            y={CHART_HEIGHT / 2}
            transform={`rotate(-90 14 ${CHART_HEIGHT / 2})`}
            textAnchor="middle"
            className="fill-slate-600 text-[11px]"
          >
            Visits
          </text>

          {confidenceBandPath ? <path d={confidenceBandPath} className="fill-emerald-500/15" /> : null}
          <path d={buildPath(points, maxValue, "history")} className="fill-none stroke-slate-600" strokeWidth="2.5" />
          <path d={buildPath(points, maxValue, "forecast")} className="fill-none stroke-emerald-600" strokeWidth="2.5" strokeDasharray="7 5" />

          {forecastStartX ? (
            <>
              <line x1={forecastStartX} y1={TOP_PADDING} x2={forecastStartX} y2={CHART_HEIGHT - BOTTOM_PADDING} className="stroke-slate-400" strokeWidth="1" strokeDasharray="3 4" />
              <text x={Math.min(forecastStartX + 8, CHART_WIDTH - RIGHT_PADDING)} y={TOP_PADDING + 14} className="fill-slate-500 text-[10px]">
                Forecast begins
              </text>
            </>
          ) : null}

          {positionedPoints.map(({ point, index, coordinates }, pointIndex) => {
            if (!shouldRenderXAxisLabel(points, pointIndex, minForecastIndex)) {
              return null;
            }

            const [x] = coordinates;
            return (
              <text
                key={`${point.label}-${index}`}
                x={x}
                y={CHART_HEIGHT - 8}
                textAnchor="middle"
                transform={`rotate(${X_AXIS_LABEL_ROTATION_DEGREES} ${x} ${CHART_HEIGHT - 8})`}
                className="fill-slate-500 text-[11px]"
              >
                {point.label}
              </text>
            );
          })}

          {positionedPoints.map(({ index, coordinates }) => {
            const [x, y] = coordinates;
            return (
              <circle
                key={`point-${index}`}
                cx={x}
                cy={y}
                r={10}
                fill="transparent"
                onMouseEnter={() => setActiveIndex(index)}
                onMouseLeave={() => setActiveIndex(null)}
              />
            );
          })}

          {activePoint ? (
            <>
              <circle cx={activePoint.coordinates[0]} cy={activePoint.coordinates[1]} r={3.2} className="fill-slate-900" />
              <foreignObject
                x={Math.min(activePoint.coordinates[0] + 10, CHART_WIDTH - RIGHT_PADDING - 180)}
                y={Math.max(activePoint.coordinates[1] - 66, TOP_PADDING)}
                width={176}
                height={94}
              >
                <div className="rounded-md border border-slate-200 bg-white/95 px-2 py-1 text-[11px] leading-4 text-slate-700 shadow-lg backdrop-blur-sm">
                  <p className="font-medium text-slate-900">{formatWeekRange(activePoint.point.date, activePoint.point.endDate)}</p>
                  <p>{activePoint.point.displayLabel}</p>
                  <p>Visits: {formatVisits(activePoint.point.visits)}</p>
                  {activePoint.point.type === "forecast" && activePoint.point.lower !== null && activePoint.point.upper !== null ? (
                    <p>
                      Range: {formatVisits(activePoint.point.lower)} - {formatVisits(activePoint.point.upper)}
                    </p>
                  ) : null}
                </div>
              </foreignObject>
            </>
          ) : null}
        </svg>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-600">
        <span className="inline-flex items-center gap-1">
          <span className="h-0.5 w-4 bg-slate-600" /> Historical (weekly-equivalent)
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-0.5 w-4 border-t-2 border-dashed border-emerald-600" /> Forecast (weekly)
        </span>
        {confidenceBandPath ? (
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-4 rounded-sm bg-emerald-500/20" /> Forecast confidence range
          </span>
        ) : null}
        <span className="ml-auto text-slate-500">Peak displayed weekly volume: {formatVisits(maxValue)}</span>
      </div>
    </section>
  );
}
