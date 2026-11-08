// anyplot.ai
// line-retention-cohort: User Retention Curve by Cohort
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { LinePlot } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const TARGET = 20; // benchmark retention in percent
const Y_DOMAIN_MAX = 100; // retention runs from 0 to 100 percent
const Y_HEAD_SHARE = 0.03; // headroom so the 100 % starts keep their full stroke
const WIDTH_OLDEST = 1.75; // older cohorts draw thinner and fainter, the newest at full weight
const WIDTH_NEWEST = 3.25;
const OPACITY_OLDEST = 0.75;

// Columns: set these to your data's column names
const WEEK = "Weeks since signup"; // role: time_period
const RETENTION = "Retained users (%)"; // role: retention_rate
const COHORT = "Signup cohort"; // role: cohort
const COHORT_SIZE = "Cohort size (users)"; // role: cohort_size

// Data: replace this block with your own records, one object per row
// A SaaS product's five monthly signup cohorts, tracked weekly for 12 weeks; newer cohorts retain better.
const data = (() => {
  let s = 42 >>> 0;
  const rand = () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
  const cohorts = [
    ["Jan 2025", 1245],
    ["Feb 2025", 1089],
    ["Mar 2025", 1312],
    ["Apr 2025", 987],
    ["May 2025", 1567],
  ];
  return cohorts.flatMap(([label, size], i) => {
    const floor = 17 + i * 3.5;
    return Array.from({ length: 12 }, (_, w) => {
      if (w === 0) return { [COHORT]: label, [COHORT_SIZE]: size, [WEEK]: 0, [RETENTION]: 100 };
      const smooth = floor + (100 - floor) * Math.exp(-0.45 * w);
      const jitter = (rand() - 0.5) * 1.6;
      return { [COHORT]: label, [COHORT_SIZE]: size, [WEEK]: w, [RETENTION]: Math.round(Math.max(floor - 2, smooth + jitter) * 10) / 10 };
    });
  });
})();

// Plot: reads only data and the constants above
const cohorts = [...new Set(data.map((d) => d[COHORT]))];
const weeks = [...new Set(data.map((d) => d[WEEK]))].sort((a, b) => a - b);

// Recency from the signup period in each cohort label ("Jan 2025"); labels that are not
// dates fall back to their order of appearance.
const parsed = cohorts.map((c) => Date.parse(`1 ${c}`));
const signupKey = parsed.every(Number.isFinite) ? parsed : cohorts.map((_, i) => i);
const lines = cohorts.map((cohort, i) => {
  const rows = data.filter((d) => d[COHORT] === cohort);
  const rank = signupKey.filter((k) => k < signupKey[i]).length; // 0 = oldest signup
  const recency = cohorts.length > 1 ? rank / (cohorts.length - 1) : 1;
  return {
    id: `cohort-${i}`,
    label: `${cohort} (n = ${rows[0][COHORT_SIZE].toLocaleString("en-US")})`,
    color: t.palette[i],
    size: rows[0][COHORT_SIZE],
    width: WIDTH_OLDEST + (WIDTH_NEWEST - WIDTH_OLDEST) * recency,
    opacity: OPACITY_OLDEST + (1 - OPACITY_OLDEST) * recency,
    values: weeks.map((w) => rows.find((d) => d[WEEK] === w)?.[RETENTION] ?? null),
  };
});
const finals = lines.map((l) => l.values.filter((v) => v != null).at(-1));
const unit = RETENTION.match(/\(([^)]+)\)/)?.[1] ?? "";

const TITLE = "line-retention-cohort · javascript · muix · anyplot.ai";
const SUBTITLE = `${cohorts.length} cohorts · ${lines.reduce((s, l) => s + l.size, 0).toLocaleString("en-US")} users · ${weeks.length} observations each · last-period retention ${Math.min(...finals).toFixed(1)}${unit} to ${Math.max(...finals).toFixed(1)}${unit}`;
const HEADER_H = 80;
const LEGEND_H = 44;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 100px", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_H - LEGEND_H}
        margin={{ top: 12, right: 48, bottom: 16, left: 24 }}
        skipAnimation
        series={lines.map((line) => ({
          type: "line",
          id: line.id,
          data: line.values,
          label: line.label,
          color: line.color,
          curve: "monotoneX",
          showMark: false,
          labelMarkType: "line",
          valueFormatter: (v: number | null) => (v == null ? "" : `${v.toFixed(1)}${unit}`),
        }))}
        xAxis={[
          {
            data: weeks,
            scaleType: "linear",
            min: weeks[0],
            max: weeks[weeks.length - 1],
            tickInterval: weeks,
            valueFormatter: (v: number) => `${v}`,
            label: WEEK,
            height: 64,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: Y_DOMAIN_MAX * (1 + Y_HEAD_SHARE),
            tickNumber: 11,
            label: RETENTION,
            width: 72,
            disableLine: true,
            disableTicks: true,
            valueFormatter: (v: number) => `${v}${unit}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "end" }} legendDirection="horizontal">
          <ChartsLegend
            sx={{
              fontSize: 16,
              color: t.ink,
              columnGap: 3,
              pr: 5,
              "& .MuiChartsLegend-mark": { width: 28 },
              // Each swatch carries its line's width and opacity, so the legend explains the recency encoding
              ...Object.fromEntries(
                lines.map((line) => [
                  `& .MuiChartsLegend-item[data-series="${line.id}"] .MuiChartsLegend-mark path`,
                  { strokeWidth: line.width, strokeOpacity: line.opacity },
                ]),
              ),
            }}
          />
          <ChartsSurface
            sx={{
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              ...Object.fromEntries(
                lines.map((line) => [
                  `& .MuiLineChart-line[data-series="${line.id}"]`,
                  { strokeWidth: line.width, strokeOpacity: line.opacity },
                ]),
              ),
            }}
          >
            <ChartsGrid horizontal />
            {/* The target line sits behind the curves */}
            <ChartsReferenceLine
              y={TARGET}
              label={`Target ${TARGET}${unit}`}
              labelAlign="start"
              spacing={{ x: 12, y: 8 }}
              lineStyle={{ stroke: t.inkSoft, strokeDasharray: "7 5", strokeWidth: 1.75 }}
              labelStyle={{ fontSize: 15, fill: t.ink }}
            />
            <LinePlot skipAnimation />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
