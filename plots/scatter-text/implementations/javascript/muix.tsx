// anyplot.ai
// scatter-text: Scatter Plot with Text Labels Instead of Points
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT_SIZE = 22; // px, one size for all labels, fitted to ~32 words; bold at this size is large text, so 3:1 contrast suffices in both themes
const X_PAD_SHARE = 0.07; // axis padding as a share of the data span, room for the text
const Y_PAD_SHARE = 0.08;

// Columns: set these to your data's column names
const X = "Embedding dimension 1"; // role: x
const Y = "Embedding dimension 2"; // role: y
const LABEL = "Word"; // role: label
const CLUSTER = "Topic cluster"; // role: extra

// Data: replace this block with your own records, one object per row
// Words positioned like a t-SNE / UMAP projection of a word embedding: four topic clusters.
const topics: [string, number, number, string[]][] = [
  ["Animals", 24, 76, ["tiger", "falcon", "dolphin", "panther", "sparrow", "otter", "lynx", "heron"]],
  ["Food & drink", 76, 74, ["saffron", "espresso", "truffle", "paprika", "chutney", "brioche", "sorbet", "tempeh"]],
  ["Technology", 26, 24, ["kernel", "compiler", "firmware", "latency", "endpoint", "container", "pipeline", "runtime"]],
  ["Sports", 78, 22, ["sprinter", "goalie", "referee", "marathon", "dugout", "scrimmage", "podium", "striker"]],
];
const offsets = [[-16, 9], [0, 13], [16, 9], [-19, -4], [0, 1], [19, -4], [-11, -15], [11, -15]];
let state = 20260902;
const data: Record<string, number | string>[] = [];
for (const [topic, cx, cy, words] of topics) {
  words.forEach((word, i) => {
    state = (state * 1103515245 + 12345) % 2147483648;
    const jx = (state / 2147483648 - 0.5) * 4;
    state = (state * 1103515245 + 12345) % 2147483648;
    const jy = (state / 2147483648 - 0.5) * 4;
    data.push({ [X]: cx + offsets[i][0] + jx, [Y]: cy + offsets[i][1] + jy, [LABEL]: word, [CLUSTER]: topic });
  });
}

// Plot: reads only data and the constants above
const clusters = [...new Set(data.map((d) => String(d[CLUSTER])))];

const labels = clusters.flatMap((cluster, ci) =>
  data
    .filter((d) => d[CLUSTER] === cluster)
    .map((d, i) => ({
      id: `${ci}-${i}`,
      cluster: ci,
      x: Number(d[X]),
      y: Number(d[Y]),
      text: String(d[LABEL]),
      color: t.palette[ci],
    })),
);

const xs = data.map((d) => Number(d[X]));
const ys = data.map((d) => Number(d[Y]));
const xMin = Math.min(...xs);
const xMax = Math.max(...xs);
const yMin = Math.min(...ys);
const yMax = Math.max(...ys);
const xPad = (xMax - xMin) * X_PAD_SHARE;
const yPad = (yMax - yMin) * Y_PAD_SHARE;

const title = "scatter-text · javascript · muix · anyplot.ai";
const subtitle = `${data.length} labels in ${clusters.length} clusters · each word is centered on its (x, y)`;
const HEADER_H = 84;
const LEGEND_H = 40;

function TextLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {labels.map((p) => (
        <text
          key={p.id}
          x={xScale(p.x)}
          y={yScale(p.y)}
          fill={p.color}
          fontSize={FONT_SIZE}
          fontWeight={700}
          textAnchor="middle"
          dominantBaseline="central"
          paintOrder="stroke"
          stroke={t.pageBg}
          strokeWidth={FONT_SIZE / 4}
          strokeLinejoin="round"
        >
          {p.text}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{title}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_H - LEGEND_H}
        margin={{ top: 12, right: 48, bottom: 16, left: 32 }}
        skipAnimation
        series={clusters.map((cluster, ci) => ({
          type: "scatter" as const,
          id: `cluster-${ci}`,
          label: cluster,
          color: t.palette[ci],
          data: labels.filter((p) => p.cluster === ci).map((p) => ({ x: p.x, y: p.y, id: p.id })),
        }))}
        xAxis={[
          {
            scaleType: "linear",
            min: xMin - xPad,
            max: xMax + xPad,
            label: X,
            height: 64,
            tickNumber: 8,
            disableLine: true,
            disableTicks: true,
            valueFormatter: (v: number) => v.toFixed(0),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yMin - yPad,
            max: yMax + yPad,
            label: Y,
            width: 72,
            tickNumber: 6,
            disableLine: true,
            disableTicks: true,
            valueFormatter: (v: number) => v.toFixed(0),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ horizontal: "end", vertical: "top" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 16, color: t.ink, pr: 6 }} />
          <ChartsSurface>
            <ChartsGrid horizontal vertical />
            <ChartsXAxis />
            <ChartsYAxis />
            <TextLabels />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
