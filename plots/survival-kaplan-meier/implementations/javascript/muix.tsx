// anyplot.ai
// survival-kaplan-meier: Kaplan-Meier Survival Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-09
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Reliability engineering: time-to-failure of a machine bearing, comparing a
// standard design against a reinforced design under the same test protocol.
const GROUP_SIZE = 50;
const OBSERVATION_WINDOW = 36; // months — study ends here (administrative censoring)

// Small fixed-seed LCG — the browser has no seeded RNG.
function createRng(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rng = createRng(424242);

function sampleExponential(rate: number) {
  return -Math.log(1 - rng()) / rate;
}

// Simulates a cohort under two competing risks: mechanical failure (the event
// of interest) and early dropout (e.g. unit pulled from service for an
// unrelated reason). Anyone still running at OBSERVATION_WINDOW is censored.
function generateGroup(failureRatePerMonth: number, dropoutRatePerMonth: number) {
  const observations = [];
  for (let i = 0; i < GROUP_SIZE; i += 1) {
    const failureTime = sampleExponential(failureRatePerMonth);
    const dropoutTime = sampleExponential(dropoutRatePerMonth);
    const time = Math.min(failureTime, dropoutTime, OBSERVATION_WINDOW);
    const event = failureTime <= dropoutTime && failureTime <= OBSERVATION_WINDOW ? 1 : 0;
    observations.push({ time, event });
  }
  return observations;
}

const standardObservations = generateGroup(0.045, 0.01);
const reinforcedObservations = generateGroup(0.022, 0.01);

// Kaplan-Meier estimator with Greenwood's formula for the 95% CI. Returns the
// step points: survival holds at each value from its own time onward.
function kaplanMeier(observations: { time: number; event: number }[]) {
  const sorted = [...observations].sort((a, b) => a.time - b.time);
  const eventTimes = Array.from(new Set(sorted.map((o) => o.time))).sort((a, b) => a - b);

  let atRisk = sorted.length;
  let survival = 1;
  let varianceSum = 0;
  const points = [{ time: 0, survival: 1, lower: 1, upper: 1, censored: false }];

  eventTimes.forEach((time) => {
    const atThisTime = sorted.filter((o) => o.time === time);
    const deaths = atThisTime.filter((o) => o.event === 1).length;

    if (deaths > 0) {
      survival *= 1 - deaths / atRisk;
      const denom = atRisk * (atRisk - deaths);
      if (denom > 0) varianceSum += deaths / denom;
    }

    const standardError = survival * Math.sqrt(varianceSum);
    points.push({
      time,
      survival,
      lower: Math.max(0, survival - 1.96 * standardError),
      upper: Math.min(1, survival + 1.96 * standardError),
      censored: deaths === 0,
    });

    atRisk -= atThisTime.length;
  });

  return points;
}

const standardCurve = kaplanMeier(standardObservations);
const reinforcedCurve = kaplanMeier(reinforcedObservations);

// Both curves are re-sampled onto one shared, sorted time grid (forward-fill,
// matching step-function semantics) so they can share a single x-axis.
const timeGrid = Array.from(
  new Set([...standardCurve, ...reinforcedCurve].map((p) => p.time)),
).sort((a, b) => a - b);

function alignToGrid(points: typeof standardCurve, grid: number[]) {
  let cursor = 0;
  return grid.map((time) => {
    while (cursor + 1 < points.length && points[cursor + 1].time <= time) cursor += 1;
    const current = points[cursor];
    return {
      time,
      survival: current.survival,
      lower: current.lower,
      upper: current.upper,
      censored: current.censored && current.time === time,
    };
  });
}

const standardAligned = alignToGrid(standardCurve, timeGrid);
const reinforcedAligned = alignToGrid(reinforcedCurve, timeGrid);

// Each group contributes 3 series: an invisible base (stacked to the CI lower
// bound) + a filled delta on top of it (renders as the CI band from lower to
// upper), then the visible KM step line. Only the step line gets a `label`,
// so the band helpers are automatically excluded from the legend. The base's
// fill is knocked out via the `& .MuiAreaElement-series-{id}` sx rules below
// (MUI X always applies its own opaque "brighter" tint to an area fill, so a
// transparent/rgba `color` on the series itself is not enough to hide it).
function buildGroupSeries(key: string, label: string, color: string, aligned: typeof standardAligned) {
  return [
    {
      id: `${key}-ci-base`,
      data: aligned.map((p) => p.lower),
      stack: `ci-${key}`,
      area: true,
      curve: "stepAfter" as const,
      color,
      showMark: false,
      disableHighlight: true,
    },
    {
      id: `${key}-ci-band`,
      data: aligned.map((p) => Math.max(0, p.upper - p.lower)),
      stack: `ci-${key}`,
      area: true,
      curve: "stepAfter" as const,
      color,
      showMark: false,
      disableHighlight: true,
    },
    {
      id: `${key}-survival`,
      data: aligned.map((p) => p.survival),
      curve: "stepAfter" as const,
      color,
      label,
      showMark: ({ index }: { index: number }) => aligned[index].censored,
    },
  ];
}

const series = [
  ...buildGroupSeries("standard", `Standard design (n=${GROUP_SIZE})`, t.palette[0], standardAligned),
  ...buildGroupSeries("reinforced", `Reinforced design (n=${GROUP_SIZE})`, t.palette[1], reinforcedAligned),
];

const TITLE = "survival-kaplan-meier · javascript · muix · anyplot.ai";

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const paddingX = 40;
  const paddingY = 28;
  const headerHeight = 76;

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        boxSizing: "border-box",
        padding: `${paddingY}px ${paddingX}px`,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box sx={{ height: headerHeight, flexShrink: 0 }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: "text.primary", lineHeight: 1.3 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ fontSize: 14, color: "text.secondary", mt: "4px" }}>
          Shaded bands are 95% confidence intervals · open circles mark units censored while still in service
        </Typography>
      </Box>
      <LineChart
        width={size.width - paddingX * 2}
        height={size.height - paddingY * 2 - headerHeight}
        series={series}
        xAxis={[
          {
            data: timeGrid,
            scaleType: "linear",
            min: 0,
            max: OBSERVATION_WINDOW,
            label: "Time in service (months)",
            labelStyle: { fontSize: 15 },
            tickLabelStyle: { fontSize: 13 },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: 1,
            label: "Survival probability",
            labelStyle: { fontSize: 15 },
            tickLabelStyle: { fontSize: 13 },
            valueFormatter: (v: number) => `${Math.round(v * 100)}%`,
          },
        ]}
        grid={{ horizontal: true }}
        margin={{ top: 8, right: 24, bottom: 56, left: 78 }}
        skipAnimation
        slotProps={{
          legend: {
            position: { vertical: "top", horizontal: "right" },
            labelStyle: { fontSize: 14 },
          },
        }}
        sx={{
          "& .MuiLineElement-root": { strokeWidth: 3 },
          "& .MuiMarkElement-root": { strokeWidth: 3 },
          "& .MuiAreaElement-series-standard-ci-base": { fill: "none" },
          "& .MuiAreaElement-series-reinforced-ci-base": { fill: "none" },
          "& .MuiAreaElement-series-standard-ci-band": { fillOpacity: 0.16 },
          "& .MuiAreaElement-series-reinforced-ci-band": { fillOpacity: 0.16 },
        }}
      />
    </Box>
  );
}
