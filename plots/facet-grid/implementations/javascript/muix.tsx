// anyplot.ai
// facet-grid: Faceted Grid Plot
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";

const t = window.ANYPLOT_TOKENS;
const FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif";
const TITLE = "facet-grid · javascript · muix · anyplot.ai";

// Constants
const X_COL = "Bill Length (mm)";
const Y_COL = "Bill Depth (mm)";
const ROW_FACET = "Sex";
const COL_FACET = "Species";

const AXIS_PAD_SHARE = 0.08;
const MARKER_SIZE = 6.5;
const MARKER_COLOR = `${t.palette[0]}CC`;

// Data: penguin bill measurements across species and sex (6 facets × 45 observations = 270 rows)
const facetSpecs = [
  { col: "Adelie", row: "Female", xMean: 37.3, xStd: 1.6, yMean: 17.6, yStd: 0.9, n: 45 },
  { col: "Chinstrap", row: "Female", xMean: 46.6, xStd: 3.0, yMean: 17.6, yStd: 0.9, n: 45 },
  { col: "Gentoo", row: "Female", xMean: 45.6, xStd: 2.0, yMean: 14.2, yStd: 0.8, n: 45 },
  { col: "Adelie", row: "Male", xMean: 40.4, xStd: 2.0, yMean: 19.1, yStd: 1.0, n: 45 },
  { col: "Chinstrap", row: "Male", xMean: 51.5, xStd: 1.6, yMean: 19.3, yStd: 0.8, n: 45 },
  { col: "Gentoo", row: "Male", xMean: 49.5, xStd: 2.6, yMean: 15.7, yStd: 0.9, n: 45 },
];

let lcgState = 42 >>> 0;
const data: {
  [X_COL]: number;
  [Y_COL]: number;
  [ROW_FACET]: string;
  [COL_FACET]: string;
}[] = [];

for (const spec of facetSpecs) {
  for (let i = 0; i < spec.n; i++) {
    lcgState = (lcgState * 1664525 + 1013904223) >>> 0;
    const u1 = Math.max(lcgState / 4294967296, 1e-9);
    lcgState = (lcgState * 1664525 + 1013904223) >>> 0;
    const u2 = lcgState / 4294967296;
    const zX = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);

    lcgState = (lcgState * 1664525 + 1013904223) >>> 0;
    const u3 = Math.max(lcgState / 4294967296, 1e-9);
    lcgState = (lcgState * 1664525 + 1013904223) >>> 0;
    const u4 = lcgState / 4294967296;
    const zY = Math.sqrt(-2 * Math.log(u3)) * Math.cos(2 * Math.PI * u4);

    data.push({
      [COL_FACET]: spec.col,
      [ROW_FACET]: spec.row,
      [X_COL]: Number((spec.xMean + spec.xStd * zX).toFixed(2)),
      [Y_COL]: Number((spec.yMean + spec.yStd * zY).toFixed(2)),
    });
  }
}

// Derived facet levels in order of first appearance
const colFacets: string[] = [];
const rowFacets: string[] = [];
for (const row of data) {
  if (!colFacets.includes(row[COL_FACET])) colFacets.push(row[COL_FACET]);
  if (!rowFacets.includes(row[ROW_FACET])) rowFacets.push(row[ROW_FACET]);
}

// Shared axis domain across all facets
const allX = data.map((r) => r[X_COL]);
const allY = data.map((r) => r[Y_COL]);
const minX = Math.min(...allX);
const maxX = Math.max(...allX);
const minY = Math.min(...allY);
const maxY = Math.max(...allY);
const xPad = (maxX - minX || 1) * AXIS_PAD_SHARE;
const yPad = (maxY - minY || 1) * AXIS_PAD_SHARE;
const xDomainMin = minX - xPad;
const xDomainMax = maxX + xPad;
const yDomainMin = minY - yPad;
const yDomainMax = maxY + yPad;

// Grouped points per (rowFacet, colFacet) cell
const facets = rowFacets.map((rowVal) =>
  colFacets.map((colVal) => {
    const subset = data.filter((r) => r[ROW_FACET] === rowVal && r[COL_FACET] === colVal);
    return {
      rowVal,
      colVal,
      points: subset.map((r, idx) => ({ id: idx, x: r[X_COL], y: r[Y_COL] })),
    };
  })
);

// Layout constants
const TITLE_H = 68;
const Y_LABEL_W = 38;
const X_LABEL_H = 36;
const COL_STRIP_H = 38;
const ROW_STRIP_W = 42;
const GAP = 10;
const TICK_LABEL_STYLE = { fontSize: 14, fill: t.inkSoft, fontFamily: FONT };
const PANEL_MARGIN = { left: 8, right: 16, top: 12, bottom: 8 };

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;
  const nCols = colFacets.length;
  const nRows = rowFacets.length;

  const padRight = 18;
  const padBottom = 10;
  const gridW = W - Y_LABEL_W - ROW_STRIP_W - padRight - nCols * GAP;
  const gridH = H - TITLE_H - X_LABEL_H - COL_STRIP_H - padBottom - nRows * GAP;
  const panelW = Math.floor(gridW / nCols);
  const panelH = Math.floor(gridH / nRows);

  return (
    <div
      style={{
        width: W,
        height: H,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          height: TITLE_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</span>
        <span style={{ fontSize: 14, color: t.inkSoft }}>
          {X_COL} vs {Y_COL} · faceted by {COL_FACET} ({nCols}) × {ROW_FACET} ({nRows}), n = {data.length}
        </span>
      </div>

      <div style={{ flex: 1, display: "flex" }}>
        <div style={{ width: Y_LABEL_W, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span
            style={{
              transform: "rotate(-90deg)",
              whiteSpace: "nowrap",
              fontSize: 16,
              fontWeight: 600,
              color: t.ink,
            }}
          >
            {Y_COL}
          </span>
        </div>

        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: `repeat(${nCols}, ${panelW}px) ${ROW_STRIP_W}px`,
              gridTemplateRows: `${COL_STRIP_H}px repeat(${nRows}, ${panelH}px)`,
              columnGap: GAP,
              rowGap: GAP,
            }}
          >
            {colFacets.map((colVal, c) => (
              <div
                key={`col-${colVal}`}
                style={{
                  gridColumn: c + 1,
                  gridRow: 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: t.elevatedBg,
                  border: `1px solid ${t.grid}`,
                  borderRadius: 4,
                  color: t.ink,
                  fontSize: 15,
                  fontWeight: 600,
                }}
              >
                <span>
                  {COL_FACET}: {colVal}
                </span>
              </div>
            ))}
            <div style={{ gridColumn: nCols + 1, gridRow: 1 }} />

            {rowFacets.map((rowVal, r) =>
              colFacets.map((colVal, c) => {
                const facet = facets[r][c];
                const isLeftCol = c === 0;
                const isBottomRow = r === nRows - 1;
                return (
                  <div
                    key={`${colVal}-${rowVal}`}
                    style={{
                      gridColumn: c + 1,
                      gridRow: r + 2,
                      border: `1px solid ${t.grid}`,
                      borderRadius: 4,
                      boxSizing: "border-box",
                    }}
                  >
                    <ChartsContainer
                      width={panelW}
                      height={panelH}
                      skipAnimation
                      margin={PANEL_MARGIN}
                      xAxis={[
                        {
                          id: "x",
                          scaleType: "linear",
                          min: xDomainMin,
                          max: xDomainMax,
                          height: 34,
                          tickLabelStyle: TICK_LABEL_STYLE,
                          valueFormatter: (v: number) => (isBottomRow ? String(v) : ""),
                        },
                      ]}
                      yAxis={[
                        {
                          id: "y",
                          scaleType: "linear",
                          min: yDomainMin,
                          max: yDomainMax,
                          width: 44,
                          tickLabelStyle: TICK_LABEL_STYLE,
                          valueFormatter: (v: number) => (isLeftCol ? String(v) : ""),
                        },
                      ]}
                      series={
                        facet.points.length > 0
                          ? [
                              {
                                id: `${colVal}-${rowVal}`,
                                type: "scatter" as const,
                                color: MARKER_COLOR,
                                markerSize: MARKER_SIZE,
                                data: facet.points,
                              },
                            ]
                          : []
                      }
                      sx={{ "& .MuiScatter-mark": { stroke: t.pageBg, strokeWidth: 1 } }}
                    >
                      <ChartsGrid horizontal vertical sx={{ "& .MuiChartsGrid-line": { stroke: t.grid } }} />
                      <ScatterPlot />
                      <ChartsYAxis axisId="y" />
                      <ChartsXAxis axisId="x" />
                    </ChartsContainer>
                  </div>
                );
              })
            )}

            {rowFacets.map((rowVal, r) => (
              <div
                key={`row-${rowVal}`}
                style={{
                  gridColumn: nCols + 1,
                  gridRow: r + 2,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: t.elevatedBg,
                  border: `1px solid ${t.grid}`,
                  borderRadius: 4,
                  color: t.ink,
                  fontSize: 15,
                  fontWeight: 600,
                }}
              >
                <span style={{ transform: "rotate(90deg)", whiteSpace: "nowrap" }}>
                  {ROW_FACET}: {rowVal}
                </span>
              </div>
            ))}
          </div>

          <div style={{ height: X_LABEL_H, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ fontSize: 16, fontWeight: 600, color: t.ink }}>{X_COL}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
