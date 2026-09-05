// anyplot.ai
// pdp-basic: Partial Dependence Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;
const muted = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ---------------------------------------
// Tiny fixed-seed LCG — the browser has no seeded RNG.
function makeLcg(seed: number) {
  let state = seed >>> 0;
  return function next() {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

const rng = makeLcg(20260905);
const GRID_POINTS = 61;
const SPEND_MIN = 5;
const SPEND_MAX = 65;

// Simulated PartialDependenceDisplay output for a GradientBoostingRegressor
// predicting weekly units sold from weekly marketing spend, averaging over
// every other feature in the model.
const spend = Array.from(
  { length: GRID_POINTS },
  (_, i) => SPEND_MIN + (i * (SPEND_MAX - SPEND_MIN)) / (GRID_POINTS - 1),
);

const rawPrediction = spend.map((x) => {
  const saturating = 620 / (1 + Math.exp(-(x - 32) / 7));
  const modelWiggle = (rng() - 0.5) * 16;
  return saturating + modelWiggle;
});

// Center at zero so the curve reads as "effect relative to the average
// prediction" rather than an absolute (and arbitrary-looking) sales count.
const meanPrediction =
  rawPrediction.reduce((sum, v) => sum + v, 0) / rawPrediction.length;
const partialDependence = rawPrediction.map((v) => v - meanPrediction);

// Confidence band widens toward both ends of the spend range, where training
// samples are sparser and the model's average prediction is less certain.
const ciHalfWidth = spend.map((x) => 9 + 0.5 * Math.abs(x - 32));
const ciLowerBound = partialDependence.map((v, i) => v - ciHalfWidth[i]);
const ciBandWidth = ciHalfWidth.map((halfWidth) => 2 * halfWidth);

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const CHART_TOP = 64;

  const title = "pdp-basic · javascript · muix · anyplot.ai";
  const titleSize =
    title.length > 67 ? Math.round((22 * 67) / title.length) : 22;

  // MUI X's built-in y-axis title sits at a fixed, small offset from the
  // axis line — too small to clear wide 4-digit tick numbers, so it renders
  // the axis label as its own rotated element in a reserved strip instead.
  const Y_LABEL_W = 44;
  const yAxisLabel = "Partial dependence (Δ units sold/week)";

  return (
    <Box sx={{ position: "relative", width: W, height: H, bgcolor: t.pageBg }}>
      <Box sx={{ position: "absolute", top: 20, left: 56, right: 56 }}>
        <Typography sx={{ color: t.ink, fontSize: titleSize, fontWeight: 500 }}>
          {title}
        </Typography>
      </Box>
      <Box
        sx={{
          position: "absolute",
          top: CHART_TOP,
          left: 0,
          width: Y_LABEL_W,
          bottom: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Typography
          sx={{
            color: t.ink,
            fontSize: 16,
            whiteSpace: "nowrap",
            transform: "rotate(-90deg)",
          }}
        >
          {yAxisLabel}
        </Typography>
      </Box>
      <Box
        sx={{
          position: "absolute",
          top: CHART_TOP,
          left: Y_LABEL_W,
          right: 0,
          bottom: 0,
        }}
      >
        <LineChart
          width={W - Y_LABEL_W}
          height={H - CHART_TOP}
          skipAnimation
          series={[
            {
              id: "ci-lower",
              data: ciLowerBound,
              color: muted,
              curve: "monotoneX",
              area: true,
              stack: "ci",
              showMark: false,
              valueFormatter: () => null,
            },
            {
              id: "ci-band",
              data: ciBandWidth,
              label: "95% confidence interval",
              color: muted,
              curve: "monotoneX",
              area: true,
              stack: "ci",
              showMark: false,
              valueFormatter: (value: number | null) =>
                value == null ? null : `±${(value / 2).toFixed(0)} units/week`,
            },
            {
              id: "pdp",
              data: partialDependence,
              label: "Partial dependence",
              color: t.palette[0],
              curve: "monotoneX",
              area: false,
              showMark: false,
              valueFormatter: (value: number | null) =>
                value == null
                  ? null
                  : `${value >= 0 ? "+" : ""}${value.toFixed(0)} units/week`,
            },
          ]}
          xAxis={[
            {
              data: spend,
              scaleType: "linear",
              label: "Weekly marketing spend ($1,000s)",
              labelStyle: { fontSize: 16 },
              tickLabelStyle: { fontSize: 14 },
              valueFormatter: (value: number) => `$${value.toFixed(0)}k`,
            },
          ]}
          yAxis={[
            {
              tickLabelStyle: { fontSize: 14 },
            },
          ]}
          grid={{ horizontal: true }}
          slotProps={{ legend: { labelStyle: { fontSize: 14 } } }}
          sx={{
            "& .MuiLineElement-series-pdp": { strokeWidth: 3.5 },
            "& .MuiLineElement-series-ci-band": { strokeWidth: 0 },
            "& .MuiLineElement-series-ci-lower": { strokeWidth: 0 },
            "& .MuiAreaElement-series-ci-lower": { fill: "none" },
            "& .MuiAreaElement-series-ci-band": { fillOpacity: 0.22 },
          }}
        >
          <ChartsReferenceLine
            y={0}
            label="average prediction"
            labelAlign="end"
            labelStyle={{ fontSize: 13, fill: muted }}
            lineStyle={{ stroke: muted, strokeDasharray: "6 4" }}
          />
        </LineChart>
      </Box>
    </Box>
  );
}
