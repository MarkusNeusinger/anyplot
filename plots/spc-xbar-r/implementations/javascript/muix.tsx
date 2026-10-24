// anyplot.ai
// spc-xbar-r: Statistical Process Control Chart (X-bar/R)
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 92/100 | Created: 2026-06-20

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const A2 = 0.577;
const D3 = 0.0;
const D4 = 2.115;
const ML = { left: 108, right: 90, top: 24, bottom: 12 };
const MR = { left: 108, right: 90, top: 12, bottom: 68 };

// Columns: set these to your data's column names
const SAMPLE_ID = "Sample Number"; // role: sample_id
const SAMPLE_MEAN = "Sample Mean (mm)"; // role: sample_mean
const SAMPLE_RANGE = "Range (mm)"; // role: sample_range

// Data: replace this block with your own records
const data = [
  { [SAMPLE_ID]: 1, [SAMPLE_MEAN]: 25.012, [SAMPLE_RANGE]: 0.098 },
  { [SAMPLE_ID]: 2, [SAMPLE_MEAN]: 24.978, [SAMPLE_RANGE]: 0.115 },
  { [SAMPLE_ID]: 3, [SAMPLE_MEAN]: 25.003, [SAMPLE_RANGE]: 0.087 },
  { [SAMPLE_ID]: 4, [SAMPLE_MEAN]: 24.995, [SAMPLE_RANGE]: 0.132 },
  { [SAMPLE_ID]: 5, [SAMPLE_MEAN]: 25.021, [SAMPLE_RANGE]: 0.121 },
  { [SAMPLE_ID]: 6, [SAMPLE_MEAN]: 24.963, [SAMPLE_RANGE]: 0.108 },
  { [SAMPLE_ID]: 7, [SAMPLE_MEAN]: 25.008, [SAMPLE_RANGE]: 0.094 },
  { [SAMPLE_ID]: 8, [SAMPLE_MEAN]: 25.082, [SAMPLE_RANGE]: 0.141 },
  { [SAMPLE_ID]: 9, [SAMPLE_MEAN]: 25.034, [SAMPLE_RANGE]: 0.119 },
  { [SAMPLE_ID]: 10, [SAMPLE_MEAN]: 24.987, [SAMPLE_RANGE]: 0.127 },
  { [SAMPLE_ID]: 11, [SAMPLE_MEAN]: 24.991, [SAMPLE_RANGE]: 0.103 },
  { [SAMPLE_ID]: 12, [SAMPLE_MEAN]: 25.018, [SAMPLE_RANGE]: 0.278 },
  { [SAMPLE_ID]: 13, [SAMPLE_MEAN]: 24.955, [SAMPLE_RANGE]: 0.091 },
  { [SAMPLE_ID]: 14, [SAMPLE_MEAN]: 25.007, [SAMPLE_RANGE]: 0.138 },
  { [SAMPLE_ID]: 15, [SAMPLE_MEAN]: 24.982, [SAMPLE_RANGE]: 0.116 },
  { [SAMPLE_ID]: 16, [SAMPLE_MEAN]: 24.918, [SAMPLE_RANGE]: 0.143 },
  { [SAMPLE_ID]: 17, [SAMPLE_MEAN]: 25.044, [SAMPLE_RANGE]: 0.088 },
  { [SAMPLE_ID]: 18, [SAMPLE_MEAN]: 24.976, [SAMPLE_RANGE]: 0.112 },
  { [SAMPLE_ID]: 19, [SAMPLE_MEAN]: 25.013, [SAMPLE_RANGE]: 0.097 },
  { [SAMPLE_ID]: 20, [SAMPLE_MEAN]: 25.001, [SAMPLE_RANGE]: 0.125 },
  { [SAMPLE_ID]: 21, [SAMPLE_MEAN]: 24.968, [SAMPLE_RANGE]: 0.136 },
  { [SAMPLE_ID]: 22, [SAMPLE_MEAN]: 25.075, [SAMPLE_RANGE]: 0.109 },
  { [SAMPLE_ID]: 23, [SAMPLE_MEAN]: 24.993, [SAMPLE_RANGE]: 0.145 },
  { [SAMPLE_ID]: 24, [SAMPLE_MEAN]: 25.006, [SAMPLE_RANGE]: 0.102 },
  { [SAMPLE_ID]: 25, [SAMPLE_MEAN]: 24.974, [SAMPLE_RANGE]: 0.118 },
];

// Plot: reads only data and the constants above
const sampleIds = data.map((row) => Number(row[SAMPLE_ID]));
const sampleMeans = data.map((row) => Number(row[SAMPLE_MEAN]));
const sampleRanges = data.map((row) => Number(row[SAMPLE_RANGE]));
const nSubgroups = data.length;

const xbarBar = sampleMeans.reduce((s, v) => s + v, 0) / nSubgroups;
const rBar = sampleRanges.reduce((s, v) => s + v, 0) / nSubgroups;

const xbarUcl = xbarBar + A2 * rBar;
const xbarLcl = xbarBar - A2 * rBar;
const xbarUwl = xbarBar + (2 / 3) * A2 * rBar;
const xbarLwl = xbarBar - (2 / 3) * A2 * rBar;

const rUcl = D4 * rBar;
const rLcl = D3 * rBar;
const rUwl = (2 / 3) * D4 * rBar;

const xMin = Math.min(...sampleIds) - 0.5;
const xMax = Math.max(...sampleIds) + 0.5;
const xbarYMin = 24.88;
const xbarYMax = 25.12;
const rYMin = 0;
const rYMax = 0.32;

function OOCMarkers({
  values,
  ucl,
  lcl,
}: {
  values: number[];
  ucl: number;
  lcl: number;
}) {
  const { left, width } = useDrawingArea();
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const yUcl = yScale(ucl);
  const yLcl = yScale(lcl);

  return (
    <g>
      <rect
        x={left}
        y={yUcl}
        width={width}
        height={Math.max(1, yLcl - yUcl)}
        fill={t.inkSoft}
        opacity={0.04}
      />
      {values.map((v, i) =>
        v > ucl || v < lcl ? null : (
          <circle
            key={i}
            cx={xScale(sampleIds[i])}
            cy={yScale(v)}
            r={5}
            fill={t.palette[0]}
            opacity={0.9}
          />
        ),
      )}
      {values.map((v, i) =>
        v <= ucl && v >= lcl ? null : (
          <circle
            key={`ooc-${i}`}
            cx={xScale(sampleIds[i])}
            cy={yScale(v)}
            r={8}
            fill={t.palette[4]}
            stroke={t.pageBg}
            strokeWidth={2.5}
          />
        ),
      )}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleH = 56;
  const chartH = height - titleH;
  const xbarH = Math.round(chartH * 0.54);
  const rH = chartH - xbarH;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        pt: "16px",
        boxSizing: "border-box",
      }}
    >
      <Typography
        sx={{
          color: t.ink,
          fontSize: 22,
          fontWeight: 600,
          textAlign: "center",
          lineHeight: 1.1,
          mb: "4px",
        }}
      >
        CNC Shaft Diameter · spc-xbar-r · javascript · muix · anyplot.ai
      </Typography>
      <ChartsContainer
        width={width}
        height={xbarH}
        margin={ML}
        series={[
          {
            type: "line",
            data: sampleMeans,
            color: t.palette[0],
            showMark: false,
            curve: "linear",
          },
        ]}
        xAxis={[
          {
            data: sampleIds,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            position: "none",
          },
        ]}
        yAxis={[
          {
            min: xbarYMin,
            max: xbarYMax,
            tickNumber: 5,
            width: 96,
            label: SAMPLE_MEAN,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
      >
        <ChartsReferenceLine
          y={xbarBar}
          lineStyle={{ stroke: t.inkSoft, strokeWidth: 2.5 }}
          label="X̄"
          labelAlign="end"
          labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
        />
        <ChartsReferenceLine
          y={xbarUwl}
          lineStyle={{
            stroke: t.amber,
            strokeWidth: 1.5,
            strokeDasharray: "5 4",
            opacity: 0.85,
          }}
          label="+2σ"
          labelAlign="end"
          labelStyle={{ fill: t.amber, fontSize: 14 }}
        />
        <ChartsReferenceLine
          y={xbarLwl}
          lineStyle={{
            stroke: t.amber,
            strokeWidth: 1.5,
            strokeDasharray: "5 4",
            opacity: 0.85,
          }}
          label="−2σ"
          labelAlign="end"
          labelStyle={{ fill: t.amber, fontSize: 14 }}
        />
        <ChartsReferenceLine
          y={xbarUcl}
          lineStyle={{
            stroke: t.palette[4],
            strokeWidth: 2,
            strokeDasharray: "9 5",
          }}
          label="UCL"
          labelAlign="end"
          labelStyle={{ fill: t.palette[4], fontSize: 14, fontWeight: 600 }}
        />
        <ChartsReferenceLine
          y={xbarLcl}
          lineStyle={{
            stroke: t.palette[4],
            strokeWidth: 2,
            strokeDasharray: "9 5",
          }}
          label="LCL"
          labelAlign="end"
          labelStyle={{ fill: t.palette[4], fontSize: 14, fontWeight: 600 }}
        />
        <LinePlot skipAnimation />
        <OOCMarkers values={sampleMeans} ucl={xbarUcl} lcl={xbarLcl} />
        <ChartsYAxis />
      </ChartsContainer>

      <ChartsContainer
        width={width}
        height={rH}
        margin={MR}
        series={[
          {
            type: "line",
            data: sampleRanges,
            color: t.palette[0],
            showMark: false,
            curve: "linear",
          },
        ]}
        xAxis={[
          {
            data: sampleIds,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            height: 56,
            label: SAMPLE_ID,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: rYMin,
            max: rYMax,
            tickNumber: 5,
            width: 96,
            label: SAMPLE_RANGE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
      >
        <ChartsReferenceLine
          y={rBar}
          lineStyle={{ stroke: t.inkSoft, strokeWidth: 2.5 }}
          label="R̄"
          labelAlign="end"
          labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
        />
        <ChartsReferenceLine
          y={rUwl}
          lineStyle={{
            stroke: t.amber,
            strokeWidth: 1.5,
            strokeDasharray: "5 4",
            opacity: 0.85,
          }}
          label="+2σ"
          labelAlign="end"
          labelStyle={{ fill: t.amber, fontSize: 14 }}
        />
        <ChartsReferenceLine
          y={rUcl}
          lineStyle={{
            stroke: t.palette[4],
            strokeWidth: 2,
            strokeDasharray: "9 5",
          }}
          label="UCL"
          labelAlign="end"
          labelStyle={{ fill: t.palette[4], fontSize: 14, fontWeight: 600 }}
        />
        <LinePlot skipAnimation />
        <OOCMarkers values={sampleRanges} ucl={rUcl} lcl={rLcl} />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
