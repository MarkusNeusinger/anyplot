// anyplot.ai
// survival-kaplan-meier: Kaplan-Meier Survival Plot
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 87/100 | Updated: 2026-10-23
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const Z_95 = 1.96; // normal quantile for the 95% confidence interval

// Columns: set these to your data's column names
const TIME = "Time in service (months)"; // role: time
const EVENT = "Failure"; // role: event
const GROUP = "Bearing design"; // role: group

// Data: replace this block with your own records, one object per observation
// Reliability engineering: time-to-failure of a machine bearing, standard vs
// reinforced design. Each unit either fails, is pulled from service early for
// an unrelated reason, or is still running when the 36-month study ends.
let seed = 424242;
const rng = () => {
  seed = (seed * 1664525 + 1013904223) >>> 0; // fixed-seed LCG — the browser has no seeded RNG
  return seed / 4294967296;
};
const data: Record<string, string | number>[] = [];
[
  { design: "Standard design", failureRate: 0.045 },
  { design: "Reinforced design", failureRate: 0.022 },
].forEach(({ design, failureRate }) => {
  for (let i = 0; i < 50; i += 1) {
    const failureTime = -Math.log(1 - rng()) / failureRate;
    const dropoutTime = -Math.log(1 - rng()) / 0.01;
    const time = Math.min(failureTime, dropoutTime, 36);
    const failed = failureTime <= dropoutTime && failureTime <= 36;
    data.push({ [TIME]: time, [EVENT]: failed ? 1 : 0, [GROUP]: design });
  }
});

// Plot: reads only data and the constants above
const groups = [...new Set(data.map((d) => d[GROUP] as string))];
const timeGrid = [...new Set([0, ...data.map((d) => d[TIME] as number)])].sort((a, b) => a - b);
const maxTime = timeGrid[timeGrid.length - 1];

// Kaplan-Meier product-limit estimate with Greenwood's 95% CI, evaluated on the
// shared time grid. Step-function semantics: a value holds from its time onward.
const curves = groups.map((group) => {
  const rows = data.filter((d) => d[GROUP] === group);
  let atRisk = rows.length;
  let survival = 1;
  let varianceSum = 0;
  const points = timeGrid.map((time) => {
    const atThisTime = rows.filter((d) => d[TIME] === time);
    const deaths = atThisTime.filter((d) => d[EVENT] === 1).length;
    if (deaths > 0) {
      survival *= 1 - deaths / atRisk;
      if (atRisk > deaths) varianceSum += deaths / (atRisk * (atRisk - deaths));
    }
    atRisk -= atThisTime.length;
    const standardError = survival * Math.sqrt(varianceSum);
    return {
      survival,
      lower: Math.max(0, survival - Z_95 * standardError),
      upper: Math.min(1, survival + Z_95 * standardError),
      censored: atThisTime.length > deaths,
    };
  });
  return { group, n: rows.length, points };
});

// Each group contributes 3 series: an invisible base (stacked to the CI lower
// bound) + a filled delta on top of it (renders as the CI band from lower to
// upper), then the visible KM step line. Only the step line gets a `label`,
// so the band helpers are automatically excluded from the legend. The base's
// fill and both helpers' outlines are knocked out via the
// `.MuiLineChart-area/line[data-series=…]` sx rules below (MUI X always
// paints an area fill opaque, so a transparent `color` is not enough).
const series = curves.flatMap(({ group, n, points }, i) => [
  {
    id: `ci-base-${i}`,
    data: points.map((p) => p.lower),
    stack: `ci-${i}`,
    area: true,
    curve: "stepAfter" as const,
    color: t.palette[i],
    showMark: false,
    disableHighlight: true,
  },
  {
    id: `ci-band-${i}`,
    data: points.map((p) => Math.max(0, p.upper - p.lower)),
    stack: `ci-${i}`,
    area: true,
    curve: "stepAfter" as const,
    color: t.palette[i],
    showMark: false,
    disableHighlight: true,
  },
  {
    id: `survival-${i}`,
    data: points.map((p) => p.survival),
    curve: "stepAfter" as const,
    color: t.palette[i],
    label: `${group} (n=${n})`,
    shape: "circle" as const,
    showMark: ({ index }: { index: number }) => points[index].censored,
  },
]);

const bandStyles = Object.fromEntries(
  curves.flatMap((_, i) => [
    [`& .MuiLineChart-area[data-series="ci-base-${i}"]`, { fill: "none" }],
    [`& .MuiLineChart-area[data-series="ci-band-${i}"]`, { fill: t.palette[i], fillOpacity: 0.16 }],
    [`& .MuiLineChart-line[data-series="ci-base-${i}"]`, { display: "none" }],
    [`& .MuiLineChart-line[data-series="ci-band-${i}"]`, { display: "none" }],
  ]),
);

const TITLE = "survival-kaplan-meier · javascript · muix · anyplot.ai";

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
        height={size.height - paddingY * 2 - headerHeight - 40}
        series={series}
        xAxis={[
          {
            data: timeGrid,
            scaleType: "linear",
            min: 0,
            max: maxTime,
            label: TIME,
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
            height: 52,
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: 1,
            label: "Survival probability",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
            width: 84,
            valueFormatter: (v: number) => `${Math.round(v * 100)}%`,
          },
        ]}
        grid={{ horizontal: true }}
        margin={{ top: 8, right: 24, bottom: 8, left: 16 }}
        skipAnimation
        slotProps={{
          legend: {
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 15 },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiLineChart-mark": { strokeWidth: 2.5 },
          ...bandStyles,
        }}
      />
    </Box>
  );
}
