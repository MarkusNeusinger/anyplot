// anyplot.ai
// elbow-curve: Elbow Curve for K-Means Clustering
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic): K-means inertia for customer segmentation ---
const kValues = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const inertia = [1250, 690, 410, 260, 195, 165, 145, 130, 118, 108];
const optimalK = 4;

const TITLE = "elbow-curve · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;
const Y_LABEL_WIDTH = 40;

// MUI X's built-in yAxis `label` offsets from a fixed (tickFontSize + tickSize
// + 10) constant rather than the tick labels' measured width, so it collides
// with wide tick numbers (e.g. "1,300") at this fontSize — render the axis
// title as its own rotated element instead, with guaranteed dedicated space.
const yAxisLabelStyle = {
  writingMode: "vertical-rl" as const,
  transform: "rotate(180deg)",
  color: t.ink,
  fontSize: 16,
  width: Y_LABEL_WIDTH,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  return (
    <div
      style={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        backgroundColor: t.pageBg,
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          paddingLeft: 32,
        }}
      >
        <span style={{ color: t.ink, fontSize: 22, fontWeight: 500 }}>
          {TITLE}
        </span>
      </div>
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          height: height - TITLE_HEIGHT,
        }}
      >
        <span style={yAxisLabelStyle}>Inertia (WCSS)</span>
        <LineChart
          width={width - Y_LABEL_WIDTH}
          height={height - TITLE_HEIGHT}
          skipAnimation
          margin={{ top: 24, right: 48, bottom: 64, left: 80 }}
          xAxis={[
            {
              data: kValues,
              scaleType: "linear",
              label: "Number of Clusters (k)",
              tickMinStep: 1,
              labelStyle: { fontSize: 16, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            },
          ]}
          yAxis={[
            {
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            },
          ]}
          series={[
            {
              data: inertia,
              label: "Within-cluster sum of squares",
              color: t.palette[0],
              showMark: true,
              curve: "linear",
            },
          ]}
          grid={{ horizontal: true }}
          slotProps={{ legend: { hidden: true } }}
        >
          <ChartsReferenceLine
            x={optimalK}
            label={`Elbow · k=${optimalK}`}
            labelAlign="middle"
            lineStyle={{
              stroke: t.amber,
              strokeDasharray: "6 6",
              strokeWidth: 2,
            }}
            labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
          />
        </LineChart>
      </div>
    </div>
  );
}
