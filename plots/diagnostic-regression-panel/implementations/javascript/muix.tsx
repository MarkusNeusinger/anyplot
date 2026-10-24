// anyplot.ai
// diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-05
//# anyplot-orientation: square

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif";

// Constants
const LOWESS_GRID_COUNT = 36;
const LOWESS_SPAN = 0.5;
const TOP_INFLUENTIAL_COUNT = 3;
const COOK_LEVELS = [0.5, 1.0];
const COOK_GRID_COUNT = 80;
const AXIS_PAD_RATIO = 0.08;
const MARKER_SIZE = 6.5;

const acklamA = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.38357751867269e2, -3.066479806614716e1, 2.506628277459239];
const acklamB = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1];
const acklamC = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
const acklamD = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416];

// Columns: set these to your data's column names
const OBS_ID = "Observation"; // role: extra
const FITTED = "Fitted values"; // role: fitted
const RESIDUALS = "Residuals"; // role: residuals
const STD_RESIDUALS = "Standardized residuals"; // role: std_residuals
const LEVERAGE = "Leverage"; // role: leverage
const COOKS_D = "Cook's distance"; // role: cooks_d

// Data: replace this block with your own records
const data = (() => {
  const sampleSize = 56;
  const modelParams = 2;
  let seed = 20260905;
  const doses: number[] = [];
  for (let i = 0; i < sampleSize; i++) {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const u = seed / 0x7fffffff;
    doses.push(4 + 92 * (i / (sampleSize - 1)) + (u - 0.5) * 3);
  }
  doses.sort((a, b) => a - b);

  const responses = doses.map((d) => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const u1 = Math.max(seed / 0x7fffffff, 1e-9);
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const u2 = seed / 0x7fffffff;
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    const trend = 18 + 2.9 * d - 0.012 * d * d;
    const noiseScale = 2.5 + 0.11 * d;
    return trend + z * noiseScale;
  });

  responses[10] += 34;
  doses[sampleSize - 2] = 118;
  responses[sampleSize - 2] -= 46;

  const doseMean = doses.reduce((a, b) => a + b, 0) / sampleSize;
  const responseMean = responses.reduce((a, b) => a + b, 0) / sampleSize;
  const sxx = doses.reduce((acc, d) => acc + (d - doseMean) ** 2, 0);
  const sxy = doses.reduce((acc, d, i) => acc + (d - doseMean) * (responses[i] - responseMean), 0);
  const olsSlope = sxy / sxx;
  const olsIntercept = responseMean - olsSlope * doseMean;

  const rawFitted = doses.map((d) => olsIntercept + olsSlope * d);
  const rawResiduals = responses.map((y, i) => y - rawFitted[i]);
  const rss = rawResiduals.reduce((acc, r) => acc + r * r, 0);
  const sigmaHat = Math.sqrt(rss / (sampleSize - modelParams));

  return doses.map((d, i) => {
    const h = 1 / sampleSize + (d - doseMean) ** 2 / sxx;
    const stdRes = rawResiduals[i] / (sigmaHat * Math.sqrt(1 - h));
    const cooks = (stdRes * stdRes * h) / (modelParams * (1 - h));
    return {
      [OBS_ID]: i + 1,
      [FITTED]: Number(rawFitted[i].toFixed(4)),
      [RESIDUALS]: Number(rawResiduals[i].toFixed(4)),
      [STD_RESIDUALS]: Number(stdRes.toFixed(4)),
      [LEVERAGE]: Number(h.toFixed(5)),
      [COOKS_D]: Number(cooks.toFixed(5)),
    };
  });
})();

// Plot: reads only data and the constants above
const n = data.length;
const fitted = data.map((r) => Number(r[FITTED]));
const residuals = data.map((r) => Number(r[RESIDUALS]));
const stdResiduals = data.map((r) => Number(r[STD_RESIDUALS]));
const leverage = data.map((r) => Number(r[LEVERAGE]));
const cooksD = data.map((r) => Number(r[COOKS_D]));
const scaleLocation = stdResiduals.map((r) => Math.sqrt(Math.abs(r)));
const p = Math.round(leverage.reduce((a, b) => a + b, 0));

const influentialIndices = cooksD
  .map((cooks, idx) => ({ idx, cooks }))
  .sort((a, b) => b.cooks - a.cooks)
  .slice(0, TOP_INFLUENTIAL_COUNT)
  .map((item) => item.idx);

const qqRanked = stdResiduals.map((v, i) => ({ v, origIdx: i })).sort((a, b) => a.v - b.v);
const theoreticalQuantiles = new Array<number>(n);
const sortedStdResiduals = new Array<number>(n);
const qqRankByOrigIdx = new Array<number>(n);

qqRanked.forEach(({ v, origIdx }, rank) => {
  const pr = (rank + 0.5) / n;
  const low = 0.02425;
  let z = 0;
  if (pr < low) {
    const q = Math.sqrt(-2 * Math.log(pr));
    z =
      (((((acklamC[0] * q + acklamC[1]) * q + acklamC[2]) * q + acklamC[3]) * q + acklamC[4]) * q + acklamC[5]) /
      ((((acklamD[0] * q + acklamD[1]) * q + acklamD[2]) * q + acklamD[3]) * q + 1);
  } else if (pr > 1 - low) {
    const q = Math.sqrt(-2 * Math.log(1 - pr));
    z =
      -(((((acklamC[0] * q + acklamC[1]) * q + acklamC[2]) * q + acklamC[3]) * q + acklamC[4]) * q + acklamC[5]) /
      ((((acklamD[0] * q + acklamD[1]) * q + acklamD[2]) * q + acklamD[3]) * q + 1);
  } else {
    const q = pr - 0.5;
    const r = q * q;
    z =
      ((((((acklamA[0] * r + acklamA[1]) * r + acklamA[2]) * r + acklamA[3]) * r + acklamA[4]) * r + acklamA[5]) * q) /
      (((((acklamB[0] * r + acklamB[1]) * r + acklamB[2]) * r + acklamB[3]) * r + acklamB[4]) * r + 1);
  }
  theoreticalQuantiles[rank] = z;
  sortedStdResiduals[rank] = v;
  qqRankByOrigIdx[origIdx] = rank;
});

const fittedMin = Math.min(...fitted);
const fittedMax = Math.max(...fitted);
const fittedSpan = fittedMax - fittedMin;
const fittedAxisMin = fittedMin - fittedSpan * AXIS_PAD_RATIO;
const fittedAxisMax = fittedMax + fittedSpan * AXIS_PAD_RATIO;

const fittedGrid = Array.from(
  { length: LOWESS_GRID_COUNT },
  (_, i) => fittedMin + (fittedSpan * i) / (LOWESS_GRID_COUNT - 1),
);

const lowessK = Math.max(3, Math.round(LOWESS_SPAN * n));
const residLowess: number[] = [];
const scaleLocLowess: number[] = [];

for (const x0 of fittedGrid) {
  const dists = fitted.map((xi) => Math.abs(xi - x0));
  const bandwidth = [...dists].sort((a, b) => a - b)[Math.min(lowessK - 1, n - 1)];
  let sw = 0;
  let swx = 0;
  let swxx = 0;
  let swyRes = 0;
  let swxyRes = 0;
  let swySL = 0;
  let swxySL = 0;
  for (let i = 0; i < n; i++) {
    const u = dists[i] / bandwidth;
    if (u >= 1) continue;
    const w = (1 - u ** 3) ** 3;
    sw += w;
    swx += w * fitted[i];
    swxx += w * fitted[i] * fitted[i];
    swyRes += w * residuals[i];
    swxyRes += w * fitted[i] * residuals[i];
    swySL += w * scaleLocation[i];
    swxySL += w * fitted[i] * scaleLocation[i];
  }
  const denom = sw * swxx - swx * swx;
  const b1Res = (sw * swxyRes - swx * swyRes) / denom;
  const b0Res = (swyRes - b1Res * swx) / sw;
  residLowess.push(b0Res + b1Res * x0);

  const b1SL = (sw * swxySL - swx * swySL) / denom;
  const b0SL = (swySL - b1SL * swx) / sw;
  scaleLocLowess.push(b0SL + b1SL * x0);
}

const residMin = Math.min(...residuals, ...residLowess);
const residMax = Math.max(...residuals, ...residLowess);
const residSpan = residMax - residMin;
const residAxisMin = residMin - residSpan * AXIS_PAD_RATIO;
const residAxisMax = residMax + residSpan * AXIS_PAD_RATIO;

const qqDataMin = Math.min(...theoreticalQuantiles);
const qqDataMax = Math.max(...theoreticalQuantiles);
const qqXSpan = qqDataMax - qqDataMin;
const qqXMin = qqDataMin - qqXSpan * AXIS_PAD_RATIO;
const qqXMax = qqDataMax + qqXSpan * AXIS_PAD_RATIO;

const stdResMin = Math.min(...stdResiduals);
const stdResMax = Math.max(...stdResiduals);
const stdResSpan = stdResMax - stdResMin;
const stdResAxisMin = stdResMin - stdResSpan * AXIS_PAD_RATIO;
const stdResAxisMax = stdResMax + stdResSpan * AXIS_PAD_RATIO;
const p4SymLim = Math.max(Math.abs(stdResAxisMin), Math.abs(stdResAxisMax));

const slMin = Math.min(...scaleLocation, ...scaleLocLowess);
const slMax = Math.max(...scaleLocation, ...scaleLocLowess);
const slSpan = slMax - slMin;
const slAxisMin = Math.max(0, slMin - slSpan * AXIS_PAD_RATIO);
const slAxisMax = slMax + slSpan * AXIS_PAD_RATIO;

const levMin = Math.min(...leverage);
const levMax = Math.max(...leverage);
const levSpan = levMax - levMin;
const levAxisMin = Math.max(0, levMin - levSpan * AXIS_PAD_RATIO);
const levAxisMax = levMax + levSpan * (AXIS_PAD_RATIO * 1.6);

const cookHStart = Math.max(levAxisMin, levSpan * 0.02);
const cookGrid = Array.from(
  { length: COOK_GRID_COUNT },
  (_, i) => cookHStart + ((levAxisMax - cookHStart) * i) / (COOK_GRID_COUNT - 1),
);

const POINT_COLOR = t.palette[0];
const SMOOTH_COLOR = t.palette[2];
const CONTOUR_COLOR = t.inkSoft;
const REF_LINE_STYLE = { stroke: t.inkSoft, strokeWidth: 1.5, strokeDasharray: "6 5", opacity: 0.75 };
const AXIS_LABEL_STYLE = { fill: t.ink, fontSize: 15, fontWeight: 600, fontFamily: FONT };
const TICK_LABEL_STYLE = { fill: t.inkSoft, fontSize: 14, fontFamily: FONT };
const CHART_MARGIN = { top: 14, right: 26, bottom: 54, left: 74 };

interface LabelPoint {
  x: number;
  y: number;
  text: string;
}

interface PanelOverlayProps {
  points: LabelPoint[];
  qqLine?: boolean;
  cookContours?: boolean;
  clipId: string;
}

function PanelOverlay({ points, qqLine, cookContours, clipId }: PanelOverlayProps) {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const { left, top, width, height } = useDrawingArea();

  const positioned = points.map(({ x, y, text }) => ({
    px: xScale(x),
    py: yScale(y),
    text,
    dx: 10,
    dy: -8,
    anchor: "start" as "start" | "end",
  }));

  const rightBound = left + width;
  positioned.forEach((point, i) => {
    if (point.px > rightBound - 38) {
      point.dx = -10;
      point.anchor = "end";
    }
    for (let j = 0; j < i; j++) {
      const other = positioned[j];
      const dist = Math.hypot(point.px - other.px, point.py - other.py);
      if (dist < 28) {
        other.dx = -10;
        other.dy = -10;
        other.anchor = "end";
        point.dx = 11;
        point.dy = 15;
        point.anchor = "start";
      }
    }
  });

  return (
    <g>
      <defs>
        <clipPath id={clipId}>
          <rect x={left} y={top} width={width} height={height} />
        </clipPath>
      </defs>

      {qqLine && (
        <g clipPath={`url(#${clipId})`}>
          <line
            x1={xScale(qqXMin)}
            y1={yScale(qqXMin)}
            x2={xScale(qqXMax)}
            y2={yScale(qqXMax)}
            stroke={t.inkSoft}
            strokeWidth={1.6}
            strokeDasharray="6 5"
            opacity={0.8}
          />
        </g>
      )}

      {cookContours && (
        <g clipPath={`url(#${clipId})`}>
          {COOK_LEVELS.map((level) => {
            const posPath = cookGrid
              .map((h, idx) => {
                const v = Math.sqrt((level * p * (1 - h)) / h);
                return `${idx === 0 ? "M" : "L"}${xScale(h).toFixed(1)},${yScale(v).toFixed(1)}`;
              })
              .join(" ");
            const negPath = cookGrid
              .map((h, idx) => {
                const v = -Math.sqrt((level * p * (1 - h)) / h);
                return `${idx === 0 ? "M" : "L"}${xScale(h).toFixed(1)},${yScale(v).toFixed(1)}`;
              })
              .join(" ");

            const labelH = levAxisMax - levSpan * 0.04;
            const posLabelV = Math.sqrt((level * p * (1 - labelH)) / labelH);
            const negLabelV = -posLabelV;
            const lx = xScale(labelH) - 6;
            const lyPos = yScale(posLabelV) - 6;
            const lyNeg = yScale(negLabelV) + 15;

            return (
              <g key={level}>
                <path
                  d={posPath}
                  fill="none"
                  stroke={CONTOUR_COLOR}
                  strokeWidth={1.7}
                  strokeDasharray="5 4"
                />
                <path
                  d={negPath}
                  fill="none"
                  stroke={CONTOUR_COLOR}
                  strokeWidth={1.7}
                  strokeDasharray="5 4"
                />
                {lyPos > top + 14 && lyPos < top + height - 8 && (
                  <text
                    x={lx}
                    y={lyPos}
                    textAnchor="end"
                    fill={t.ink}
                    stroke={t.pageBg}
                    strokeWidth={3.5}
                    paintOrder="stroke"
                    style={{ fontSize: 14, fontWeight: 600, fontFamily: FONT }}
                  >
                    {level.toFixed(1)}
                  </text>
                )}
                {lyNeg > top + 14 && lyNeg < top + height - 6 && (
                  <text
                    x={lx}
                    y={lyNeg}
                    textAnchor="end"
                    fill={t.ink}
                    stroke={t.pageBg}
                    strokeWidth={3.5}
                    paintOrder="stroke"
                    style={{ fontSize: 14, fontWeight: 600, fontFamily: FONT }}
                  >
                    {level.toFixed(1)}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      )}

      {positioned.map(({ px, py, text, dx, dy, anchor }) => {
        const tx = px + dx;
        const ty = Math.max(top + 16, Math.min(top + height - 8, py + dy));
        return (
          <text
            key={text}
            x={tx}
            y={ty}
            textAnchor={anchor}
            fill={t.ink}
            stroke={t.pageBg}
            strokeWidth={3.5}
            paintOrder="stroke"
            style={{ fontSize: 14, fontWeight: 600, fontFamily: FONT }}
          >
            {text}
          </text>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const padX = 20;
  const padBottom = 14;
  const headerH = 74;
  const subTitleH = 30;
  const gap = 16;
  const rowH = Math.floor((H - headerH - padBottom - gap) / 2);
  const colW = Math.floor((W - padX * 2 - gap) / 2);
  const chartH = rowH - subTitleH;
  const chartW = colW;

  const p1Points = influentialIndices.map((i) => ({
    x: fitted[i],
    y: residuals[i],
    text: String(data[i][OBS_ID]),
  }));

  const p2Points = influentialIndices.map((i) => {
    const rank = qqRankByOrigIdx[i];
    return {
      x: theoreticalQuantiles[rank],
      y: sortedStdResiduals[rank],
      text: String(data[i][OBS_ID]),
    };
  });

  const p3Points = influentialIndices.map((i) => ({
    x: fitted[i],
    y: scaleLocation[i],
    text: String(data[i][OBS_ID]),
  }));

  const p4Points = influentialIndices.map((i) => ({
    x: leverage[i],
    y: stdResiduals[i],
    text: String(data[i][OBS_ID]),
  }));

  return (
    <div
      style={{
        width: W,
        height: H,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        padding: `0 ${padX}px ${padBottom}px ${padX}px`,
        boxSizing: "border-box",
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          height: headerH,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 700, color: t.ink }}>
          diagnostic-regression-panel · javascript · muix · anyplot.ai
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          <span>OLS diagnostics (n = {n}, p = {p})</span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                backgroundColor: POINT_COLOR,
                display: "inline-block",
              }}
            />
            {`${OBS_ID}s (top ${TOP_INFLUENTIAL_COUNT} by ${COOKS_D} labeled)`}
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span
              style={{
                width: 18,
                height: 2.5,
                backgroundColor: SMOOTH_COLOR,
                display: "inline-block",
              }}
            />
            LOWESS smoother
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span
              style={{
                width: 18,
                borderTop: `2px dashed ${CONTOUR_COLOR}`,
                display: "inline-block",
              }}
            />
            {`${COOKS_D} (${COOK_LEVELS.map((l) => l.toFixed(1)).join(", ")})`}
          </span>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: `${colW}px ${colW}px`,
          gridTemplateRows: `${rowH}px ${rowH}px`,
          columnGap: gap,
          rowGap: gap,
        }}
      >
        {/* Panel 1: Residuals vs Fitted */}
        <div style={{ width: chartW, height: rowH }}>
          <div style={{ height: subTitleH, display: "flex", alignItems: "flex-end", paddingBottom: 4, paddingLeft: 74 }}>
            <span style={{ fontSize: 16, fontWeight: 600, color: t.ink }}>{`1. ${RESIDUALS} vs ${FITTED}`}</span>
          </div>
          <ChartsContainer
            width={chartW}
            height={chartH}
            margin={CHART_MARGIN}
            skipAnimation
            xAxis={[
              {
                id: "p1x",
                scaleType: "linear",
                min: fittedAxisMin,
                max: fittedAxisMax,
                data: fittedGrid,
                height: 54,
                label: FITTED,
                labelStyle: AXIS_LABEL_STYLE,
                tickLabelStyle: TICK_LABEL_STYLE,
              },
            ]}
            yAxis={[
              {
                id: "p1y",
                scaleType: "linear",
                min: residAxisMin,
                max: residAxisMax,
                width: 74,
                label: RESIDUALS,
                labelStyle: AXIS_LABEL_STYLE,
                tickLabelStyle: TICK_LABEL_STYLE,
              },
            ]}
            series={[
              {
                id: "p1-points",
                type: "scatter",
                color: POINT_COLOR,
                markerSize: MARKER_SIZE,
                data: fitted.map((x, i) => ({ x, y: residuals[i], id: i })),
              },
              {
                id: "p1-smooth",
                type: "line",
                color: SMOOTH_COLOR,
                data: residLowess,
                showMark: false,
                curve: "natural",
              },
            ]}
          >
            <ChartsGrid horizontal vertical />
            <ChartsReferenceLine y={0} lineStyle={REF_LINE_STYLE} />
            <ScatterPlot />
            <LinePlot />
            <ChartsXAxis axisId="p1x" />
            <ChartsYAxis axisId="p1y" />
            <PanelOverlay points={p1Points} clipId="clip-p1" />
          </ChartsContainer>
        </div>

        {/* Panel 2: Normal Q-Q */}
        <div style={{ width: chartW, height: rowH }}>
          <div style={{ height: subTitleH, display: "flex", alignItems: "flex-end", paddingBottom: 4, paddingLeft: 74 }}>
            <span style={{ fontSize: 16, fontWeight: 600, color: t.ink }}>2. Normal Q-Q</span>
          </div>
          <ChartsContainer
            width={chartW}
            height={chartH}
            margin={CHART_MARGIN}
            skipAnimation
            xAxis={[
              {
                id: "p2x",
                scaleType: "linear",
                min: qqXMin,
                max: qqXMax,
                height: 54,
                label: "Theoretical quantiles",
                labelStyle: AXIS_LABEL_STYLE,
                tickLabelStyle: TICK_LABEL_STYLE,
              },
            ]}
            yAxis={[
              {
                id: "p2y",
                scaleType: "linear",
                min: stdResAxisMin,
                max: stdResAxisMax,
                width: 74,
                label: STD_RESIDUALS,
                labelStyle: AXIS_LABEL_STYLE,
                tickLabelStyle: TICK_LABEL_STYLE,
              },
            ]}
            series={[
              {
                id: "p2-points",
                type: "scatter",
                color: POINT_COLOR,
                markerSize: MARKER_SIZE,
                data: theoreticalQuantiles.map((x, i) => ({ x, y: sortedStdResiduals[i], id: i })),
              },
            ]}
          >
            <ChartsGrid horizontal vertical />
            <ScatterPlot />
            <ChartsXAxis axisId="p2x" />
            <ChartsYAxis axisId="p2y" />
            <PanelOverlay points={p2Points} qqLine clipId="clip-p2" />
          </ChartsContainer>
        </div>

        {/* Panel 3: Scale-Location */}
        <div style={{ width: chartW, height: rowH }}>
          <div style={{ height: subTitleH, display: "flex", alignItems: "flex-end", paddingBottom: 4, paddingLeft: 74 }}>
            <span style={{ fontSize: 16, fontWeight: 600, color: t.ink }}>3. Scale-Location</span>
          </div>
          <ChartsContainer
            width={chartW}
            height={chartH}
            margin={CHART_MARGIN}
            skipAnimation
            xAxis={[
              {
                id: "p3x",
                scaleType: "linear",
                min: fittedAxisMin,
                max: fittedAxisMax,
                data: fittedGrid,
                height: 54,
                label: FITTED,
                labelStyle: AXIS_LABEL_STYLE,
                tickLabelStyle: TICK_LABEL_STYLE,
              },
            ]}
            yAxis={[
              {
                id: "p3y",
                scaleType: "linear",
                min: slAxisMin,
                max: slAxisMax,
                width: 74,
                label: `√|${STD_RESIDUALS}|`,
                labelStyle: AXIS_LABEL_STYLE,
                tickLabelStyle: TICK_LABEL_STYLE,
              },
            ]}
            series={[
              {
                id: "p3-points",
                type: "scatter",
                color: POINT_COLOR,
                markerSize: MARKER_SIZE,
                data: fitted.map((x, i) => ({ x, y: scaleLocation[i], id: i })),
              },
              {
                id: "p3-smooth",
                type: "line",
                color: SMOOTH_COLOR,
                data: scaleLocLowess,
                showMark: false,
                curve: "natural",
              },
            ]}
          >
            <ChartsGrid horizontal vertical />
            <ScatterPlot />
            <LinePlot />
            <ChartsXAxis axisId="p3x" />
            <ChartsYAxis axisId="p3y" />
            <PanelOverlay points={p3Points} clipId="clip-p3" />
          </ChartsContainer>
        </div>

        {/* Panel 4: Residuals vs Leverage */}
        <div style={{ width: chartW, height: rowH }}>
          <div style={{ height: subTitleH, display: "flex", alignItems: "flex-end", paddingBottom: 4, paddingLeft: 74 }}>
            <span style={{ fontSize: 16, fontWeight: 600, color: t.ink }}>{`4. ${RESIDUALS} vs ${LEVERAGE}`}</span>
          </div>
          <ChartsContainer
            width={chartW}
            height={chartH}
            margin={CHART_MARGIN}
            skipAnimation
            xAxis={[
              {
                id: "p4x",
                scaleType: "linear",
                min: levAxisMin,
                max: levAxisMax,
                height: 54,
                label: LEVERAGE,
                labelStyle: AXIS_LABEL_STYLE,
                tickLabelStyle: TICK_LABEL_STYLE,
              },
            ]}
            yAxis={[
              {
                id: "p4y",
                scaleType: "linear",
                min: -p4SymLim,
                max: p4SymLim,
                width: 74,
                label: STD_RESIDUALS,
                labelStyle: AXIS_LABEL_STYLE,
                tickLabelStyle: TICK_LABEL_STYLE,
              },
            ]}
            series={[
              {
                id: "p4-points",
                type: "scatter",
                color: POINT_COLOR,
                markerSize: MARKER_SIZE,
                data: leverage.map((x, i) => ({ x, y: stdResiduals[i], id: i })),
              },
            ]}
          >
            <ChartsGrid horizontal vertical />
            <ChartsReferenceLine y={0} lineStyle={REF_LINE_STYLE} />
            <ScatterPlot />
            <ChartsXAxis axisId="p4x" />
            <ChartsYAxis axisId="p4y" />
            <PanelOverlay points={p4Points} cookContours clipId="clip-p4" />
          </ChartsContainer>
        </div>
      </div>
    </div>
  );
}
