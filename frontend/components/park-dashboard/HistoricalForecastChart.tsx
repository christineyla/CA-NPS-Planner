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
  label: string;
  visits: number;
  type: PointType;
  lower: number | null;
  upper: number | null;
}

interface TooltipSummary {
  historical: number | null;
  predicted: number | null;
}

const CHART_WIDTH = 900;
const CHART_HEIGHT = 410;
const LEFT_PADDING = 72;
const RIGHT_PADDING = 44;
const TOP_PADDING = 24;
const FORECAST_LABEL_OFFSET = 12;
const BOTTOM_PADDING = 72;
const X_AXIS_LABEL_ROTATION_DEGREES = -18;
const MIN_X_LABEL_SPACING = 88;
const MIN_FORECAST_WIDTH_RATIO = 0.16;
const MAX_FORECAST_WIDTH_RATIO = 0.26;

function formatLabel(date: Date): string {
  return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

function formatTooltipDate(point: ChartPoint): string {
  return point.date.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });
}

function toMonthKey(date: Date): string {
  return `${date.getFullYear()}-${date.getMonth()}`;
}

function buildTooltipSummary(history: VisitationHistoryPoint[], forecast: ForecastWeek[]): Map<string, TooltipSummary> {
  const summary = new Map<string, TooltipSummary>();

  history.forEach((entry) => {
    const monthDate = new Date(entry.observation_month);
    const key = toMonthKey(monthDate);
    const current = summary.get(key) ?? { historical: null, predicted: null };

    summary.set(key, {
      ...current,
      historical: entry.visits,
    });
  });

  forecast.forEach((week) => {
    const weekDate = new Date(week.week_start);
    const key = toMonthKey(weekDate);
    const current = summary.get(key) ?? { historical: null, predicted: null };

    summary.set(key, {
      ...current,
      predicted: (current.predicted ?? 0) + week.predicted_visits,
    });
  });

  return summary;
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
      label: formatLabel(date),
      visits: weeklyEquivalentVisits,
      type: "history" as const,
      lower: null,
      upper: null,
    };
  });

  const forecastPoints = forecast.slice(0, 26).map((week) => {
    const date = new Date(week.week_start);
    return {
      date,
      label: formatLabel(date),
      visits: week.predicted_visits,
      type: "forecast" as const,
      lower: week.predicted_visits_lower ?? null,
      upper: week.predicted_visits_upper ?? null,
    };
  });

  return [...historyPoints, ...forecastPoints].sort((a, b) => a.date.getTime() - b.date.getTime());
}

function resolveForecastWidthRatio(points: ChartPoint[], forecastStartIndex: number): number {
  if (forecastStartIndex <= 0 || forecastStartIndex >= points.length - 1) {
    return MIN_FORECAST_WIDTH_RATIO;
  }

  const firstHistory = points[0]?.date.getTime();
  const firstForecast = points[forecastStartIndex]?.date.getTime();
  const lastForecast = points[points.length - 1]?.date.getTime();

  if (!firstHistory || !firstForecast || !lastForecast || firstForecast <= firstHistory) {
    return MIN_FORECAST_WIDTH_RATIO;
  }

  const historicalDuration = firstForecast - firstHistory;
  const forecastDuration = Math.max(lastForecast - firstForecast, 1);
  const durationRatio = forecastDuration / historicalDuration;

  return Math.min(
    MAX_FORECAST_WIDTH_RATIO,
    Math.max(MIN_FORECAST_WIDTH_RATIO, durationRatio + 0.04),
  );
}

function pointXCoordinate(
  index: number,
  count: number,
  forecastStartIndex: number,
  forecastWidthRatio: number,
): number {
  const drawableWidth = CHART_WIDTH - LEFT_PADDING - RIGHT_PADDING;

  if (forecastStartIndex <= 0 || forecastStartIndex >= count) {
    return LEFT_PADDING + (index * drawableWidth) / Math.max(count - 1, 1);
  }

  const historyCount = forecastStartIndex;
  const forecastCount = count - forecastStartIndex;
  const forecastWidth = drawableWidth * forecastWidthRatio;
  const historyWidth = drawableWidth - forecastWidth;

  if (index < forecastStartIndex) {
    return LEFT_PADDING + (index * historyWidth) / Math.max(historyCount - 1, 1);
  }

  const forecastIndex = index - forecastStartIndex;
  return LEFT_PADDING + historyWidth + (forecastIndex * forecastWidth) / Math.max(forecastCount - 1, 1);
}

function pointToCoordinate(
  value: number,
  index: number,
  count: number,
  maxValue: number,
  forecastStartIndex: number,
  forecastWidthRatio: number,
): [number, number] {
  const x = pointXCoordinate(index, count, forecastStartIndex, forecastWidthRatio);
  const y =
    CHART_HEIGHT -
    BOTTOM_PADDING -
    (value / maxValue) * (CHART_HEIGHT - TOP_PADDING - BOTTOM_PADDING);
  return [x, y];
}

function shouldRenderXAxisLabel(
  points: ChartPoint[],
  pointIndex: number,
  forecastStartIndex: number,
): boolean {
  const point = points[pointIndex];
  if (!point) {
    return false;
  }

  const isFirstPoint = pointIndex === 0;
  const isLastPoint = pointIndex === points.length - 1;
  if (isFirstPoint || isLastPoint) {
    return true;
  }

  if (point.type === "history") {
    const monthsFromStart =
      (point.date.getFullYear() - points[0].date.getFullYear()) * 12 +
      (point.date.getMonth() - points[0].date.getMonth());

    const isQuarterStart = monthsFromStart % 3 === 0;
    if (!isQuarterStart) {
      return false;
    }

    const isNearForecastBoundary =
      forecastStartIndex > 0 && pointIndex >= Math.max(0, forecastStartIndex - 2);
    return !isNearForecastBoundary;
  }

  const previousForecastPoint = points
    .slice(0, pointIndex)
    .reverse()
    .find((candidate) => candidate.type === "forecast");
  if (!previousForecastPoint) {
    return true;
  }

  const isNewMonth =
    point.date.getMonth() !== previousForecastPoint.date.getMonth() ||
    point.date.getFullYear() !== previousForecastPoint.date.getFullYear();

  if (!isNewMonth) {
    return false;
  }

  const monthsFromForecastStart =
    forecastStartIndex >= 0
      ? (point.date.getFullYear() - points[forecastStartIndex].date.getFullYear()) * 12 +
        (point.date.getMonth() - points[forecastStartIndex].date.getMonth())
      : 0;

  return monthsFromForecastStart % 2 === 0;
}

function buildPath(
  points: ChartPoint[],
  maxValue: number,
  type: PointType,
  forecastStartIndex: number,
  forecastWidthRatio: number,
): string {
  const filtered = points
    .map((point, index) => ({ point, index }))
    .filter(({ point }) => point.type === type);

  return filtered
    .map(({ point, index }, pathIndex) => {
      const [x, y] = pointToCoordinate(
        point.visits,
        index,
        points.length,
        maxValue,
        forecastStartIndex,
        forecastWidthRatio,
      );
      return `${pathIndex === 0 ? "M" : "L"}${x} ${y}`;
    })
    .join(" ");
}

function buildConfidenceBand(
  points: ChartPoint[],
  maxValue: number,
  forecastStartIndex: number,
  forecastWidthRatio: number,
): string | null {
  const forecast = points
    .map((point, index) => ({ point, index }))
    .filter(
      ({ point }) => point.type === "forecast" && point.lower !== null && point.upper !== null,
    );

  if (forecast.length < 2) {
    return null;
  }

  const upperPath = forecast
    .map(({ point, index }, pathIndex) => {
      const [x, y] = pointToCoordinate(
        point.upper ?? point.visits,
        index,
        points.length,
        maxValue,
        forecastStartIndex,
        forecastWidthRatio,
      );
      return `${pathIndex === 0 ? "M" : "L"}${x} ${y}`;
    })
    .join(" ");

  const lowerPath = forecast
    .slice()
    .reverse()
    .map(({ point, index }) => {
      const [x, y] = pointToCoordinate(
        point.lower ?? point.visits,
        index,
        points.length,
        maxValue,
        forecastStartIndex,
        forecastWidthRatio,
      );
      return `L${x} ${y}`;
    })
    .join(" ");

  return `${upperPath} ${lowerPath} Z`;
}

export function HistoricalForecastChart({ forecast, history }: HistoricalForecastChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const points = toChartPoints(history, forecast);
  const tooltipSummary = buildTooltipSummary(history, forecast);

  if (points.length === 0) {
    return null;
  }

  const maxValue = Math.max(...points.map((point) => point.upper ?? point.visits), 1);
  const minForecastIndex = points.findIndex((point) => point.type === "forecast");
  const forecastWidthRatio = resolveForecastWidthRatio(points, minForecastIndex);
  const forecastStartX =
    minForecastIndex >= 0
      ? pointXCoordinate(minForecastIndex, points.length, minForecastIndex, forecastWidthRatio)
      : null;

  const confidenceBandPath = buildConfidenceBand(
    points,
    maxValue,
    minForecastIndex,
    forecastWidthRatio,
  );
  const positionedPoints = points.map((point, index) => ({
    point,
    index,
    coordinates: pointToCoordinate(
      point.visits,
      index,
      points.length,
      maxValue,
      minForecastIndex,
      forecastWidthRatio,
    ),
  }));
  const activePoint = activeIndex !== null ? positionedPoints[activeIndex] : null;
  const activeSummary = activePoint ? tooltipSummary.get(toMonthKey(activePoint.point.date)) : null;
  const historicalVisits = activeSummary?.historical ?? null;
  const predictedVisits = activeSummary?.predicted ?? null;
  const horizontalDrawingWidth = CHART_WIDTH - LEFT_PADDING - RIGHT_PADDING;
  const estimatedLabelCount = Math.max(2, Math.floor(horizontalDrawingWidth / MIN_X_LABEL_SPACING));
  const shouldRotateXAxisLabels = points.length > estimatedLabelCount + 2;

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Historical + Forecast Visits</h2>
      <p className="mt-1 text-xs text-slate-500">
        Weekly-equivalent historical visitation is shown on the left, with projected weekly
        visitation trends on the right.
      </p>
      <div className="mt-3 rounded-md border border-slate-100 p-2">
        <svg
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
          className="h-[420px] w-full"
          role="img"
          aria-label="Historical and forecast visits line chart"
        >
          <line
            x1={LEFT_PADDING}
            y1={CHART_HEIGHT - BOTTOM_PADDING}
            x2={CHART_WIDTH - RIGHT_PADDING}
            y2={CHART_HEIGHT - BOTTOM_PADDING}
            className="stroke-slate-300"
            strokeWidth="1"
          />
          <line
            x1={LEFT_PADDING}
            y1={TOP_PADDING}
            x2={LEFT_PADDING}
            y2={CHART_HEIGHT - BOTTOM_PADDING}
            className="stroke-slate-300"
            strokeWidth="1"
          />

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

          {confidenceBandPath ? (
            <path d={confidenceBandPath} className="fill-emerald-500/15" />
          ) : null}
          <path
            d={buildPath(points, maxValue, "history", minForecastIndex, forecastWidthRatio)}
            className="fill-none stroke-slate-600"
            strokeWidth="2.5"
          />
          <path
            d={buildPath(points, maxValue, "forecast", minForecastIndex, forecastWidthRatio)}
            className="fill-none stroke-emerald-600"
            strokeWidth="2.5"
            strokeDasharray="7 5"
          />

          {forecastStartX ? (
            <>
              <line
                x1={forecastStartX}
                y1={TOP_PADDING}
                x2={forecastStartX}
                y2={CHART_HEIGHT - BOTTOM_PADDING}
                className="stroke-slate-400"
                strokeWidth="1"
                strokeDasharray="3 4"
              />
              <text
                x={Math.min(forecastStartX + FORECAST_LABEL_OFFSET, CHART_WIDTH - RIGHT_PADDING)}
                y={TOP_PADDING + 18}
                className="fill-slate-500 text-[10px]"
              >
                Forecast trend starts
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
                y={CHART_HEIGHT - 12}
                textAnchor={
                  pointIndex === 0 ? "start" : pointIndex === points.length - 1 ? "end" : "middle"
                }
                transform={
                  shouldRotateXAxisLabels
                    ? `rotate(${X_AXIS_LABEL_ROTATION_DEGREES} ${x} ${CHART_HEIGHT - 12})`
                    : undefined
                }
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
              <circle
                cx={activePoint.coordinates[0]}
                cy={activePoint.coordinates[1]}
                r={3.2}
                className="fill-slate-900"
              />
              <foreignObject
                x={Math.min(activePoint.coordinates[0] + 10, CHART_WIDTH - RIGHT_PADDING - 180)}
                y={Math.max(activePoint.coordinates[1] - 66, TOP_PADDING)}
                width={176}
                height={94}
              >
                <div className="rounded-md border border-slate-200 bg-white/95 px-2 py-1 text-[11px] leading-4 text-slate-700 shadow-lg backdrop-blur-sm">
                  <p className="font-medium text-slate-900">
                    {formatTooltipDate(activePoint.point)}
                  </p>
                  {historicalVisits !== null ? (
                    <p>Historical: {formatVisits(historicalVisits)}</p>
                  ) : null}
                  {predictedVisits !== null ? (
                    <p>Predicted: {formatVisits(predictedVisits)}</p>
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
          <span className="h-0.5 w-4 border-t-2 border-dashed border-emerald-600" /> Forecast
          (weekly)
        </span>
        {confidenceBandPath ? (
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-4 rounded-sm bg-emerald-500/20" /> Forecast confidence range
          </span>
        ) : null}
        <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 text-[11px] text-slate-500">
          <span className="font-medium text-slate-600">Peak weekly volume</span>
          <span>{formatVisits(maxValue)}</span>
        </span>
      </div>
    </section>
  );
}
