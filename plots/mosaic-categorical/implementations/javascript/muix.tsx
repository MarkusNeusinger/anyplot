// anyplot.ai
// mosaic-categorical: Mosaic Plot for Categorical Association Analysis
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-02
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const OUTCOME_SLOT = { Survived: 0, "Did not survive": 4 }; // semantic palette slots: survival green, death matte red
const GAP_X = 0.018; // share of the full width left open between neighbouring columns
const GAP_Y = 2; // percentage points left open between stacked tiles
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 48;
const Y_AXIS_W = 84;
const MARGIN = { top: 12, right: 48, bottom: 112, left: 24 };

// Columns: set these to your data's column names
const CLASS = "Passenger class"; // role: category_1
const OUTCOME = "Outcome"; // role: category_2
const PASSENGERS = "Passengers"; // role: frequency

// Data: replace this block with your own records, one object per row
// Titanic passengers by cabin class and survival (crew excluded)
const data = [
  { [CLASS]: "1st Class", [OUTCOME]: "Survived", [PASSENGERS]: 203 },
  { [CLASS]: "1st Class", [OUTCOME]: "Did not survive", [PASSENGERS]: 122 },
  { [CLASS]: "2nd Class", [OUTCOME]: "Survived", [PASSENGERS]: 118 },
  { [CLASS]: "2nd Class", [OUTCOME]: "Did not survive", [PASSENGERS]: 167 },
  { [CLASS]: "3rd Class", [OUTCOME]: "Survived", [PASSENGERS]: 178 },
  { [CLASS]: "3rd Class", [OUTCOME]: "Did not survive", [PASSENGERS]: 528 },
];

// Plot: reads only data and the constants above
const classes = [...new Set(data.map((d) => d[CLASS]))];
const outcomes = [...new Set(data.map((d) => d[OUTCOME]))];

// Semantic slots first; every other outcome takes the unused palette positions in order
const freeSlots = t.palette.map((_, i) => i).filter((i) => !outcomes.some((o) => OUTCOME_SLOT[o] === i));
const outcomeColor = new Map();
let nextFree = 0;
for (const outcome of outcomes) {
  if (outcome in OUTCOME_SLOT) {
    outcomeColor.set(outcome, t.palette[OUTCOME_SLOT[outcome]]);
  } else {
    outcomeColor.set(outcome, t.palette[freeSlots[nextFree]]);
    nextFree += 1;
  }
}

// Contingency table; a row without a frequency counts once (raw observations, as the spec allows)
const counts = new Map(classes.map((c) => [c, new Map(outcomes.map((o) => [o, 0]))]));
for (const d of data) {
  const row = counts.get(d[CLASS]);
  row.set(d[OUTCOME], row.get(d[OUTCOME]) + (d[PASSENGERS] ?? 1));
}
const classTotals = classes.map((c) => [...counts.get(c).values()].reduce((a, b) => a + b, 0));
const outcomeTotals = outcomes.map((o) => classes.reduce((sum, c) => sum + counts.get(c).get(o), 0));
const grandTotal = classTotals.reduce((a, b) => a + b, 0);

// Pearson chi-square test of independence
let chiSquare = 0;
classes.forEach((c, i) => {
  outcomes.forEach((o, j) => {
    const expected = (classTotals[i] * outcomeTotals[j]) / grandTotal;
    if (expected > 0) chiSquare += (counts.get(c).get(o) - expected) ** 2 / expected;
  });
});
const degreesOfFreedom = (classes.length - 1) * (outcomes.length - 1);

// Mosaic layout: column width = marginal share of the class (x in 0..1),
// tile height = conditional share of the outcome within the class (y in 0..100 %). The gaps
// between stacked tiles come out of the column first and the shares are scaled into what is
// left, so every tile keeps its proportion and no small share collapses to nothing
let cursor = 0;
const columns = classes.map((c, i) => {
  const x0 = cursor;
  cursor += classTotals[i] / grandTotal;
  const drawn = outcomes.filter((o) => counts.get(c).get(o) > 0);
  const usable = 100 - (drawn.length - 1) * GAP_Y;
  let level = 0;
  const tiles = drawn.map((o, k) => {
    const y0 = level + (k > 0 ? GAP_Y : 0);
    level = y0 + (counts.get(c).get(o) / classTotals[i]) * usable;
    return { outcome: o, y0, y1: level };
  });
  return { label: c, total: classTotals[i], x0, x1: cursor, tiles };
});

const TITLE = "Titanic Survival by Class · mosaic-categorical · javascript · muix · anyplot.ai";
const SUBTITLE = `${PASSENGERS}: ${grandTotal.toLocaleString("en-US")} · ${classes.length} × ${outcomes.length} table · Pearson χ² = ${chiSquare.toFixed(1)}, df = ${degreesOfFreedom}`;

function MosaicTiles() {
  const xScale = useXScale("x");
  const yScale = useYScale("y");
  const { left, top, width, height } = useDrawingArea();
  const bottom = top + height;

  return (
    <g>
      {columns.map((col) => {
        const px0 = xScale(col.x0 + GAP_X / 2);
        const px1 = xScale(col.x1 - GAP_X / 2);
        const mid = (px0 + px1) / 2;
        return (
          <g key={col.label}>
            {col.tiles.map((tile) => (
              <rect
                key={tile.outcome}
                x={px0}
                y={yScale(tile.y1)}
                width={Math.max(0, px1 - px0)}
                height={yScale(tile.y0) - yScale(tile.y1)}
                fill={outcomeColor.get(tile.outcome)}
              />
            ))}
            <text x={mid} y={bottom + 28} textAnchor="middle" fontSize={16} fontWeight={600} fill={t.ink}>
              {col.label}
            </text>
            <text x={mid} y={bottom + 52} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
              n = {col.total.toLocaleString("en-US")} ({((col.total / grandTotal) * 100).toFixed(1)}%)
            </text>
          </g>
        );
      })}
      <text x={left + width / 2} y={bottom + 92} textAnchor="middle" fontSize={16} fill={t.ink}>
        {CLASS} (column width ∝ {PASSENGERS})
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <div style={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: 24, fontSize: 15 }}>
        <span style={{ color: t.ink, fontWeight: 600 }}>{OUTCOME}</span>
        {outcomes.map((o) => (
          <span key={o} style={{ display: "flex", alignItems: "center", gap: 8, color: t.inkSoft }}>
            <span style={{ width: 16, height: 16, borderRadius: 3, backgroundColor: outcomeColor.get(o) }} />
            {o}
          </span>
        ))}
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H - SUBTITLE_H - LEGEND_H}
        margin={MARGIN}
        series={[]}
        xAxis={[{ id: "x", scaleType: "linear", min: 0, max: 1, position: "none" }]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: 0,
            max: 100,
            width: Y_AXIS_W,
            label: `${OUTCOME} within ${CLASS} (%)`,
            valueFormatter: (v) => `${v}%`,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
        skipAnimation
      >
        <MosaicTiles />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>
    </div>
  );
}
