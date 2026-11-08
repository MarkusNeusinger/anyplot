// anyplot.ai
// line-load-duration: Load Duration Curve for Energy Systems
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-10
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// Planning tiers from low to high load, each with the capacity line that tops it. The curve
// meets the base line only at its right end, so that label sits left, on the intermediate fill.
const TIERS = [
  { region: "Base load", capacity: "Base capacity", labelAlign: "start" },
  { region: "Intermediate load", capacity: "Intermediate capacity", labelAlign: "end" },
  { region: "Peak load", capacity: "Peak capacity", labelAlign: "end" },
];
const PEAK_HOURS_SHARE = 0.1; // peak load: the load exceeded in fewer than 10 % of all hours
const Y_HEAD_SHARE = 0.1; // headroom above the annual peak for the capacity labels
const INK_SWITCH_LUMINANCE = 0.19; // fills brighter than this take the dark ink
const FILL_OPACITY = 0.85;

// Columns: set these to your data's column names
const HOUR = "Duration (hours, ranked by load)"; // role: hour
const LOAD = "Power demand (MW)"; // role: load_mw

// Data: replace this block with your own records, one object per row
// Synthetic hourly demand of a mid-sized utility over one year, ranked from the highest hour to the lowest.
const data = Array.from({ length: 8760 }, (_, h) => ({
  [HOUR]: h,
  [LOAD]: Math.round((400 + 800 * (1 - h / 8759) ** 0.65) * 10) / 10,
}));

// Plot: reads only data and the constants above
// Durations ascending and loads descending: a monotone curve for ranked or calendar-ordered input alike.
const durations = data.map((d) => d[HOUR]).sort((a, b) => a - b);
const loads = data.map((d) => d[LOAD]).sort((a, b) => b - a);
const n = loads.length;
const peakLoad = loads[0];
const minLoad = loads[n - 1];
const baseCap = minLoad; // base capacity: the always-on load, exceeded in every hour of the year
const interCap = loads[Math.floor(n * PEAK_HOURS_SHARE)];
const capacities = [baseCap, interCap, peakLoad];

// Three stacked bands whose top edge is the load duration curve
const bands = [
  loads.map((v) => Math.min(v, baseCap)),
  loads.map((v) => Math.min(Math.max(v - baseCap, 0), interCap - baseCap)),
  loads.map((v) => Math.max(v - interCap, 0)),
];

const loadUnit = LOAD.match(/\(([^)]+)\)/)?.[1] ?? "";
const fmt = (v: number) => Math.round(v).toLocaleString("en-US");
const step = (durations[n - 1] - durations[0]) / (n - 1);
const energy = loads.reduce((s, v) => s + v, 0) * step;
const loadFactor = (energy / (peakLoad * step * n)) * 100;

// Ordered tiers take steps of the sequential ramp. Text on a fill takes the ink that the luminance of
// the visible fill calls for: the tier colour at FILL_OPACITY over the page.
const seqRgb = t.seq.map((hex: string) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)));
const pageRgb = [1, 3, 5].map((i) => parseInt(t.pageBg.slice(i, i + 2), 16));
const tierRgb = TIERS.map((_, i) =>
  seqRgb[0].map((c: number, k: number) => Math.round(c + ((seqRgb[1][k] - c) * i) / (TIERS.length - 1))),
);
const tierColors = tierRgb.map((rgb) => `rgb(${rgb.join(", ")})`);
const tierInks = tierRgb.map((rgb) => {
  const [r, g, b] = rgb
    .map((c: number, k: number) => (c * FILL_OPACITY + pageRgb[k] * (1 - FILL_OPACITY)) / 255)
    .map((c: number) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > INK_SWITCH_LUMINANCE ? "#1A1A17" : "#FAF8F1";
});

// Region label anchors: the middle of the hours each band covers; the peak sliver is labelled beside its end.
const aboveBase = loads.filter((v) => v > baseCap).length;
const aboveInter = loads.filter((v) => v > interCap).length;
const baseIdx = Math.floor(n / 2);
const interIdx = Math.floor(aboveBase / 2);
const regionLabels = [
  { x: durations[baseIdx], y: bands[0][baseIdx] / 2, anchor: "middle", dx: 0, fill: tierInks[0] },
  { x: durations[interIdx], y: baseCap + bands[1][interIdx] / 2, anchor: "middle", dx: 0, fill: tierInks[1] },
  { x: durations[Math.min(n - 1, aboveInter)], y: (interCap + peakLoad) / 2, anchor: "start", dx: 16, fill: t.ink },
];

const TITLE = "line-load-duration · javascript · muix · anyplot.ai";
const SUBTITLE = `${n.toLocaleString("en-US")} hourly loads ranked from highest to lowest · peak ${fmt(peakLoad)} ${loadUnit} · minimum ${fmt(minLoad)} ${loadUnit} · load factor ${loadFactor.toFixed(1)} %`;
const HEADER_H = 80;

// Region names inside their bands and the energy total, placed in data coordinates
function Annotations() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const { left, width } = useDrawingArea();
  const energyY = yScale((baseCap + interCap) / 2);
  return (
    <g>
      {regionLabels.map((lab, i) => (
        <text
          key={TIERS[i].region}
          x={xScale(lab.x) + lab.dx}
          y={yScale(lab.y)}
          textAnchor={lab.anchor}
          dominantBaseline="central"
          fontSize={16}
          fontWeight={700}
          fill={lab.fill}
        >
          {TIERS[i].region}
        </text>
      ))}
      <text x={left + width - 16} y={energyY} textAnchor="end" fontSize={16} fontWeight={600} fill={t.ink}>
        Total energy {(energy / 1e6).toFixed(2)} million {loadUnit}h
      </text>
      <text x={left + width - 16} y={energyY + 22} textAnchor="end" fontSize={14} fill={t.inkSoft}>
        area under the curve
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 112px", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        margin={{ top: 12, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: durations,
            scaleType: "linear",
            min: durations[0],
            max: durations[n - 1],
            tickNumber: 10,
            label: HOUR,
            height: 64,
            valueFormatter: fmt,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: peakLoad * (1 + Y_HEAD_SHARE),
            tickNumber: 7,
            label: LOAD,
            width: 88,
            valueFormatter: fmt,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={TIERS.map((tier, i) => ({
          id: `tier-${i}`,
          data: bands[i],
          label: tier.region,
          color: tierColors[i],
          stack: "load",
          area: true,
          showMark: false,
          curve: "linear",
        }))}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: FILL_OPACITY },
          "& .MuiLineChart-line": { strokeWidth: 0 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        {/* Gridlines drawn after the fills so they stay readable across the bands */}
        <ChartsGrid horizontal />
        {capacities.map((cap, i) => (
          <ChartsReferenceLine
            key={TIERS[i].capacity}
            y={cap}
            label={`${TIERS[i].capacity} ${fmt(cap)} ${loadUnit}`}
            labelAlign={TIERS[i].labelAlign}
            spacing={{ x: 16, y: 6 }}
            lineStyle={{ stroke: t.inkSoft, strokeDasharray: "8 5", strokeWidth: 1.75 }}
            // A label at the left end sits on the next band's fill; at the right end, on the page.
            labelStyle={{ fontSize: 15, fill: TIERS[i].labelAlign === "start" ? tierInks[i + 1] : t.ink }}
          />
        ))}
        <Annotations />
      </LineChart>
    </div>
  );
}
