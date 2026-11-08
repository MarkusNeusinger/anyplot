// anyplot.ai
// gain-curve: Cumulative Gains Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const FULL = 100; // both axes run in percent, from none to all
const PAD_SHARE = 0.015; // axis padding beyond 0 % and 100 %, so the corner points and the perfect-model plateau sit inside
const X_LABEL = "Population targeted (%)";
const Y_LABEL = "Positive cases captured (%)";
const PERFECT_LABEL = "Perfect model";
const RANDOM_LABEL = "Random selection";
const TITLE = "gain-curve · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;

// Columns: set these to your data's column names
const CONFIRMED_FRAUD = "Confirmed fraud after review"; // role: y_true
const FRAUD_SCORE = "Model fraud score"; // role: y_score

// Data: replace this block with your own records, one object per row
// 3000 card transactions that rule checks flagged for manual review: a latent risk drives fraud (about 15 %
// of the flagged transactions are confirmed by the reviewers), the model score sees that risk with noise
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (1664525 * state + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  const gaussian = () => {
    const u1 = Math.max(rand(), 1e-12);
    const u2 = rand();
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  };
  return Array.from({ length: 3000 }, () => {
    const risk = gaussian();
    const fraudProbability = 1 / (1 + Math.exp(-(1.4 * risk - 2.3)));
    const fraud = rand() < fraudProbability ? 1 : 0;
    return { [CONFIRMED_FRAUD]: fraud, [FRAUD_SCORE]: Math.round((risk + gaussian() * 0.9) * 10000) / 10000 };
  });
})();

// Plot: reads only data and the constants above
const ranked = data
  .filter((d) => Number.isFinite(d[FRAUD_SCORE]) && (d[CONFIRMED_FRAUD] === 0 || d[CONFIRMED_FRAUD] === 1))
  .sort((a, b) => b[FRAUD_SCORE] - a[FRAUD_SCORE]);
const n = ranked.length;
const positives = ranked.reduce((sum, d) => sum + d[CONFIRMED_FRAUD], 0);
const positiveRate = positives / n;

// One computed point per targeted sample, starting at the origin
const targeted = [0];
const captured = [0];
let runningPositives = 0;
ranked.forEach((d, i) => {
  runningPositives += d[CONFIRMED_FRAUD];
  targeted.push(((i + 1) / n) * FULL);
  captured.push((runningPositives / positives) * FULL);
});
const perfect = targeted.map((x) => Math.min(FULL, x / positiveRate));
const random = targeted.map((x) => x);

const subtitle = `n = ${n} · positive rate ${(positiveRate * FULL).toFixed(1)} % (${CONFIRMED_FRAUD} = 1) · ranked by ${FRAUD_SCORE}, highest first`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, pt: "20px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, mt: "6px" }}>{subtitle}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true, vertical: true }}
        margin={{ top: 16, right: 56, bottom: 16, left: 32 }}
        xAxis={[
          {
            data: targeted,
            scaleType: "linear",
            min: -PAD_SHARE * FULL,
            max: (1 + PAD_SHARE) * FULL,
            label: X_LABEL,
            height: 68,
            tickNumber: 10,
            valueFormatter: (v: number) => `${Math.round(v)}%`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: -PAD_SHARE * FULL,
            max: (1 + PAD_SHARE) * FULL,
            label: Y_LABEL,
            width: 92,
            tickNumber: 10,
            valueFormatter: (v: number) => `${Math.round(v)}%`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "model",
            data: captured,
            label: FRAUD_SCORE,
            color: t.palette[0],
            curve: "linear",
            area: true,
            showMark: false,
          },
          {
            id: "perfect",
            data: perfect,
            label: PERFECT_LABEL,
            color: t.inkSoft,
            curve: "linear",
            showMark: false,
          },
          {
            id: "random",
            data: random,
            label: RANDOM_LABEL,
            color: t.ink,
            curve: "linear",
            showMark: false,
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: {
              fontSize: 15,
              color: t.inkSoft,
              mb: "8px",
              "& .MuiChartsLegend-mark": { width: 36 },
              '& [data-series="perfect"] .MuiChartsLegend-mark path': { strokeWidth: 2, strokeDasharray: "2 5" },
              '& [data-series="random"] .MuiChartsLegend-mark path': { strokeWidth: 2, strokeDasharray: "10 7" },
            },
          },
        }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
          '& .MuiLineChart-line[data-series="model"]': { strokeWidth: 3.5 },
          '& .MuiLineChart-line[data-series="perfect"]': { strokeWidth: 2, strokeDasharray: "2 5" },
          '& .MuiLineChart-line[data-series="random"]': { strokeWidth: 2, strokeDasharray: "10 7" },
          '& .MuiLineChart-area[data-series="model"]': { fillOpacity: 0.12 },
        }}
      />
    </Box>
  );
}
