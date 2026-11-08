// anyplot.ai
// spc-xbar-r: Statistical Process Control Chart (X-bar/R)
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// Control chart constants by subgroup size n (ASTM E2587): A2 for the X-bar limits, D3 and D4 for the R limits
const CONTROL_CONSTANTS = {
  2: { A2: 1.88, D3: 0, D4: 3.267 },
  3: { A2: 1.023, D3: 0, D4: 2.574 },
  4: { A2: 0.729, D3: 0, D4: 2.282 },
  5: { A2: 0.577, D3: 0, D4: 2.114 },
  6: { A2: 0.483, D3: 0, D4: 2.004 },
  7: { A2: 0.419, D3: 0.076, D4: 1.924 },
  8: { A2: 0.373, D3: 0.136, D4: 1.864 },
  9: { A2: 0.337, D3: 0.184, D4: 1.816 },
  10: { A2: 0.308, D3: 0.223, D4: 1.777 },
};
const WARNING_SIGMA_SHARE = 2 / 3; // warning limits at 2 of the 3 sigma that the control limits span
const RANGE_FLOOR = 0; // a subgroup range is never negative
const Y_PAD_SHARE = 0.1;
const IN_CONTROL_LABEL = "In control";
const OUT_OF_CONTROL_LABEL = "Beyond control limits";

// Columns: set these to your data's column names
const SAMPLE = "Sample number"; // role: sample_id
const MEAN = "Mean diameter (mm)"; // role: sample_mean
const RANGE = "Diameter range (mm)"; // role: sample_range
const SUBGROUP_SIZE = "Subgroup size"; // role: extra

// Data: replace this block with your own records, one object per row
// CNC shaft diameters, 25 subgroups of five consecutive parts each
const data = [
  [25.012, 0.098], [24.978, 0.115], [25.003, 0.087], [24.995, 0.132], [25.021, 0.121],
  [24.963, 0.108], [25.008, 0.094], [25.082, 0.141], [25.034, 0.119], [24.987, 0.127],
  [24.991, 0.103], [25.018, 0.278], [24.955, 0.091], [25.007, 0.138], [24.982, 0.116],
  [24.918, 0.143], [25.044, 0.088], [24.976, 0.112], [25.013, 0.097], [25.001, 0.125],
  [24.968, 0.136], [25.075, 0.109], [24.993, 0.145], [25.006, 0.102], [24.974, 0.118],
].map(([mean, range], i) => ({ [SAMPLE]: i + 1, [MEAN]: mean, [RANGE]: range, [SUBGROUP_SIZE]: 5 }));

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[SAMPLE] - b[SAMPLE]);
const samples = rows.map((d) => d[SAMPLE]);
const subgroupSize = Math.round(rows.reduce((acc, d) => acc + d[SUBGROUP_SIZE], 0) / rows.length);
const { A2, D3, D4 } = CONTROL_CONSTANTS[subgroupSize];

const means = rows.map((d) => d[MEAN]);
const ranges = rows.map((d) => d[RANGE]);
const grandMean = means.reduce((a, b) => a + b, 0) / means.length;
const meanRange = ranges.reduce((a, b) => a + b, 0) / ranges.length;
const xbarSigma = (A2 * meanRange) / 3;
const rangeSigma = ((D4 - 1) * meanRange) / 3;
const decimals = Math.max(...[...means, ...ranges].map((v) => (String(v).split(".")[1] ?? "").length));

const panels = [
  {
    id: "xbar",
    label: MEAN,
    values: means,
    center: grandMean,
    ucl: grandMean + A2 * meanRange,
    lcl: grandMean - A2 * meanRange,
    uwl: grandMean + 3 * WARNING_SIGMA_SHARE * xbarSigma,
    lwl: grandMean - 3 * WARNING_SIGMA_SHARE * xbarSigma,
    floor: -Infinity,
  },
  {
    id: "range",
    label: RANGE,
    values: ranges,
    center: meanRange,
    ucl: D4 * meanRange,
    lcl: D3 * meanRange,
    uwl: meanRange + 3 * WARNING_SIGMA_SHARE * rangeSigma,
    lwl: Math.max(RANGE_FLOOR, meanRange - 3 * WARNING_SIGMA_SHARE * rangeSigma),
    floor: RANGE_FLOOR,
  },
].map((p) => {
  const extent = [...p.values, p.ucl, p.lcl];
  const pad = (Math.max(...extent) - Math.min(...extent)) * Y_PAD_SHARE;
  return {
    ...p,
    yMin: Math.max(p.floor, Math.min(...extent) - pad),
    yMax: Math.max(...extent) + pad,
    outside: p.values.map((v) => v > p.ucl || v < p.lcl),
    limits: [
      { key: "ucl", name: "UCL", value: p.ucl, control: true },
      { key: "uwl", name: "+2σ", value: p.uwl, control: false },
      { key: "center", name: "CL", value: p.center, control: false },
      { key: "lwl", name: "−2σ", value: p.lwl, control: false },
      { key: "lcl", name: "LCL", value: p.lcl, control: true },
    ],
  };
});
const outsideCounts = panels.map((p) => p.outside.filter(Boolean).length);

const xMin = Math.min(...samples) - 0.5;
const xMax = Math.max(...samples) + 0.5;

const TITLE = "spc-xbar-r · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length} subgroups of n = ${subgroupSize} · A2 = ${A2}, D3 = ${D3}, D4 = ${D4} · points beyond the limits: X̄ ${outsideCounts[0]}, R ${outsideCounts[1]}`;
const HEADER_H = 92;
const X_AXIS_H = 62;
const MARGIN = { top: 14, right: 150, bottom: 10, left: 24 };
const Y_AXIS_W = 96;
const MARKER_R = 5;
const OUTSIDE_R = 8;

function ControlLayer({ panel }) {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, width } = useDrawingArea();
  return (
    <g>
      {panel.values.map((v, i) => (
        <circle
          key={samples[i]}
          cx={xScale(samples[i])}
          cy={yScale(v)}
          r={panel.outside[i] ? OUTSIDE_R : MARKER_R}
          fill={panel.outside[i] ? t.palette[4] : t.palette[0]}
          stroke={t.pageBg}
          strokeWidth={panel.outside[i] ? 2.5 : 1.5}
        />
      ))}
      {panel.limits.map((l) => (
        <text
          key={l.key}
          x={left + width + 10}
          y={yScale(l.value)}
          dominantBaseline="middle"
          fontSize={14}
          fontWeight={l.control ? 600 : 400}
          fill={l.control ? t.ink : t.inkSoft}
        >
          {`${l.name} ${l.value.toFixed(decimals)}`}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const plotH = (height - HEADER_H - X_AXIS_H - 2 * (MARGIN.top + MARGIN.bottom)) / 2;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 28, fontSize: 15, color: t.inkSoft }}>
          <span>{SUBTITLE}</span>
          {[
            { label: IN_CONTROL_LABEL, color: t.palette[0], r: MARKER_R },
            { label: OUT_OF_CONTROL_LABEL, color: t.palette[4], r: OUTSIDE_R },
          ].map((item) => (
            <span key={item.label} style={{ display: "flex", alignItems: "center", gap: 8, color: t.ink }}>
              <svg width={18} height={18}>
                <circle cx={9} cy={9} r={item.r} fill={item.color} />
              </svg>
              {item.label}
            </span>
          ))}
        </div>
      </div>
      {panels.map((panel, index) => {
        const isBottom = index === panels.length - 1;
        return (
          <ChartsContainer
            key={panel.id}
            width={width}
            height={plotH + MARGIN.top + MARGIN.bottom + (isBottom ? X_AXIS_H : 0)}
            margin={MARGIN}
            skipAnimation
            series={[
              { type: "line", id: panel.id, data: panel.values, color: t.palette[0], showMark: false, curve: "linear" },
            ]}
            xAxis={[
              {
                data: samples,
                scaleType: "linear",
                min: xMin,
                max: xMax,
                tickMinStep: 1,
                position: isBottom ? "bottom" : "none",
                label: SAMPLE,
                height: X_AXIS_H,
                tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
                labelStyle: { fontSize: 16, fill: t.ink },
              },
            ]}
            yAxis={[
              {
                min: panel.yMin,
                max: panel.yMax,
                tickNumber: 5,
                label: panel.label,
                width: Y_AXIS_W,
                tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
                labelStyle: { fontSize: 16, fill: t.ink },
              },
            ]}
            sx={{
              "& .MuiLineChart-line": { strokeWidth: 2 },
              "& .MuiChartsGrid-line": { stroke: t.grid },
            }}
          >
            <ChartsGrid vertical />
            {panel.limits.map((l) => (
              <ChartsReferenceLine
                key={l.key}
                y={l.value}
                lineStyle={
                  l.key === "center"
                    ? { stroke: t.inkSoft, strokeWidth: 2.5 }
                    : l.control
                      ? { stroke: t.ink, strokeWidth: 2, strokeDasharray: "10 6" }
                      : { stroke: t.inkSoft, strokeWidth: 1.5, strokeDasharray: "4 5", opacity: 0.75 }
                }
              />
            ))}
            <LinePlot skipAnimation />
            <ControlLayer panel={panel} />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsContainer>
        );
      })}
    </div>
  );
}
