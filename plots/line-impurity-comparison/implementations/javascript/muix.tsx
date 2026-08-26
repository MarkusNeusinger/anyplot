// anyplot.ai
// line-impurity-comparison: Gini Impurity vs Entropy Comparison
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-08-26

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (theoretical splitting-criterion curves over p in [0, 1]) --------
// 101 points (step 0.01) so p=0.5 lands exactly on a sample — needed to mark
// the shared peak on both curves, not just at the reference line.
const POINT_COUNT = 101;
const probabilities = Array.from({ length: POINT_COUNT }, (_, i) => i / (POINT_COUNT - 1));

// Gini impurity: 2p(1-p) peaks at 0.5 (p=0.5). Scaled x2 so it shares the
// same [0, 1] range as entropy and the two curves can be read off one axis.
const giniScaled = probabilities.map((p) => 4 * p * (1 - p));

// Binary entropy in bits: -p*log2(p) - (1-p)*log2(1-p), already in [0, 1].
// The 0*log2(0) term is undefined at p=0 and p=1, taken as its limit of 0.
function binaryEntropy(p: number): number {
  if (p <= 0 || p >= 1) return 0;
  return -p * Math.log2(p) - (1 - p) * Math.log2(1 - p);
}
const entropy = probabilities.map(binaryEntropy);

const TITLE_HEIGHT = 60;

// --- Chart (default-exported component — the harness mounts it) -----------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box
      sx={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        paddingTop: "20px",
      }}
    >
      <Typography
        sx={{
          color: t.ink,
          fontSize: 22,
          fontWeight: 500,
          textAlign: "center",
          lineHeight: 1.2,
        }}
      >
        line-impurity-comparison · javascript · muix · anyplot.ai
      </Typography>
      <LineChart
        width={width}
        height={height - TITLE_HEIGHT}
        skipAnimation
        colors={[t.palette[0], t.palette[1]]}
        series={[
          {
            id: "gini",
            data: giniScaled,
            label: "Gini impurity ×2 — 4p(1−p)",
            showMark: (params) => params.position === 0.5,
            curve: "natural",
            area: true,
          },
          {
            id: "entropy",
            data: entropy,
            label: "Entropy — −p·log₂p − (1−p)·log₂(1−p)",
            showMark: (params) => params.position === 0.5,
            curve: "natural",
            area: true,
          },
        ]}
        xAxis={[
          {
            data: probabilities,
            scaleType: "linear",
            label: "Probability of Class 1 (p)",
            min: 0,
            max: 1,
            valueFormatter: (v: number) => v.toFixed(2),
            tickInterval: [0, 0.25, 0.5, 0.75, 1],
          },
        ]}
        yAxis={[
          {
            label: "Impurity (normalized)",
            min: 0,
            max: 1.05,
          },
        ]}
        grid={{ horizontal: true }}
        margin={{ left: 90, right: 40, top: 30, bottom: 80 }}
        sx={{
          "& .MuiChartsAxis-tickLabel": { fontSize: "14px" },
          "& .MuiChartsAxis-label": { fontSize: "16px" },
          "& .MuiChartsLegend-label": { fontSize: "14px" },
          "& .MuiLineElement-root": { strokeWidth: 3.5 },
          // Two low-opacity area fills, gini drawn under entropy: where they
          // overlap (0..gini(p)) the fills blend, while the uncovered band
          // above (gini(p)..entropy(p)) reads as a single lavender wash —
          // visually calling out where the two criteria diverge most.
          "& .MuiAreaElement-series-gini": { fillOpacity: 0.22 },
          "& .MuiAreaElement-series-entropy": { fillOpacity: 0.16 },
          "& .MuiMarkElement-root": { strokeWidth: 2.5 },
        }}
      >
        <ChartsReferenceLine
          x={0.5}
          label="Max impurity at p = 0.5"
          labelAlign="end"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
          labelStyle={{ fill: t.inkSoft, fontSize: 13 }}
        />
      </LineChart>
    </Box>
  );
}
