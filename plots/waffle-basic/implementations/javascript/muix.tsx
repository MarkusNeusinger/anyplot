// anyplot.ai
// waffle-basic: Basic Waffle Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const GRID_SIZE = 10; // the standard 10 × 10 waffle, one square per percentage point
const CELL_GAP = 0.12; // share of each band left as the gap between squares
// Semantic exception: the other/rest category takes the neutral soft ink, the
// remaining categories the unused Imprint positions in order.
const SEMANTIC = { Other: t.inkSoft };
const TITLE = "waffle-basic · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 72;
const PAD = 32;

// Columns: set these to your data's column names
const DEPARTMENT = "Department"; // role: category
const SHARE = "Budget share (%)"; // role: value

// Data: replace this block with your own records, one object per row
// Annual budget allocation of an engineering organization by department.
const data = [
  { [DEPARTMENT]: "Engineering", [SHARE]: 34 },
  { [DEPARTMENT]: "Sales", [SHARE]: 21 },
  { [DEPARTMENT]: "Marketing", [SHARE]: 17 },
  { [DEPARTMENT]: "Operations", [SHARE]: 16 },
  { [DEPARTMENT]: "Other", [SHARE]: 12 },
];

// Plot: reads only data and the constants above
const CELLS = GRID_SIZE * GRID_SIZE;
const rows = data.filter((d) => d[SHARE] != null && d[SHARE] > 0);
const categories = [...new Set(rows.map((d) => d[DEPARTMENT]))];
const totals = categories.map((c) => rows.filter((d) => d[DEPARTMENT] === c).reduce((s, d) => s + d[SHARE], 0));
const grandTotal = totals.reduce((a, b) => a + b, 0);
const percents = totals.map((v) => (v / grandTotal) * 100);

// Largest-remainder rounding: every category gets the whole squares of its
// share, and the squares left over go to the largest fractional parts, so the
// blocks fill the grid exactly.
const exact = totals.map((v) => (v / grandTotal) * CELLS);
const counts = exact.map((e) => Math.floor(e));
const leftover = CELLS - counts.reduce((a, b) => a + b, 0);
exact
  .map((e, i) => ({ i, rest: e - counts[i] }))
  .sort((a, b) => b.rest - a.rest)
  .forEach((r, k) => {
    if (k < leftover) counts[r.i] += 1;
  });

let nextSlot = 0;
const colors = categories.map((c) => SEMANTIC[c] ?? t.palette[nextSlot++]);

// Row by row from the top left, one contiguous block per category in data order
const cells = categories
  .flatMap((_, i) => Array.from({ length: counts[i] }, () => i))
  .map((group, k) => ({ group, col: k % GRID_SIZE, row: Math.floor(k / GRID_SIZE) }));
const bands = Array.from({ length: GRID_SIZE }, (_, i) => i);
const SUBTITLE = `${CELLS} squares, one per ${100 / CELLS} % of the total · shares rounded to whole squares`;

// The community package has no waffle chart: a custom layer draws the squares
// on two band scales, one for the columns and one for the rows.
function WaffleLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const size = xScale.bandwidth();

  return (
    <g>
      {cells.map((c, k) => (
        <rect
          key={k}
          x={xScale(c.col)}
          y={yScale(c.row)}
          width={size}
          height={yScale.bandwidth()}
          rx={size * 0.14}
          fill={colors[c.group]}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const side = Math.min(width - 2 * PAD, height - TITLE_H - LEGEND_H - 2 * PAD);

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ height: TITLE_H, paddingTop: 18, boxSizing: "border-box", textAlign: "center" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <div style={{ paddingTop: PAD }}>
        <ChartsContainer
          width={side}
          height={side}
          series={[]}
          skipAnimation
          margin={0}
          xAxis={[{ id: "col", scaleType: "band", data: bands, categoryGapRatio: CELL_GAP, position: "none" }]}
          yAxis={[{ id: "row", scaleType: "band", data: bands, categoryGapRatio: CELL_GAP, position: "none" }]}
        >
          <WaffleLayer />
        </ChartsContainer>
      </div>
      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "center",
          columnGap: 32,
          rowGap: 8,
          paddingTop: 16,
          boxSizing: "border-box",
        }}
      >
        <span style={{ fontSize: 16, color: t.ink, fontWeight: 600 }}>{DEPARTMENT}</span>
        {categories.map((c, i) => (
          <div key={c} style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ width: 20, height: 20, borderRadius: 3, background: colors[i], display: "inline-block" }} />
            <span style={{ fontSize: 16, color: t.ink }}>{`${c} ${Math.round(percents[i] * 10) / 10} %`}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
