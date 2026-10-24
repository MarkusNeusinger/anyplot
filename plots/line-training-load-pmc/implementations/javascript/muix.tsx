// anyplot.ai
// line-training-load-pmc: Training Load Performance Management Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 85/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const LOAD_PAD_FRAC = 0.14;
const TSB_PAD_FRAC = 0.25;
const TSS_DOT_OPACITY = 0.55;
const TITLE = "line-training-load-pmc · javascript · muix · anyplot.ai";
const TITLE_H = 54;
const LEGEND_H = 44;

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const TSS = "Daily TSS"; // role: tss
const CTL = "CTL – Fitness (AU)"; // role: ctl
const ATL = "ATL – Fatigue (AU)"; // role: atl
const TSB = "Form / TSB (AU)"; // role: tsb
const PHASE = "Training phase"; // role: phase

// Data: replace this block with your own records
const DAYS = 180;
const START_MS = Date.UTC(2025, 1, 3);
const DAY_MS = 24 * 60 * 60 * 1000;

let seed = 42 >>> 0;
let ctl = 36;
let atl = 34;

const data: Array<Record<string, number | string>> = [];
for (let i = 0; i < DAYS; i++) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const rand = seed / 4294967295;
  const noise = (rand - 0.5) * 18;

  const week = Math.floor(i / 7);
  const dow = i % 7;

  let tss: number;
  let phase: string;
  if (week < 6) {
    phase = "Base";
    tss =
      dow === 6
        ? Math.round(Math.max(0, 22 + noise * 0.4))
        : Math.round(Math.max(0, 50 + week * 4 + (dow % 2 === 0 ? 28 : 12) + noise));
  } else if (week < 15) {
    phase = "Build";
    const buildProg = (week - 6) / 9;
    const isRec = (week - 6) % 4 === 3;
    const base = 80 + buildProg * 55;
    const variation = dow % 3 === 0 ? 50 : dow % 2 === 0 ? 28 : 12;
    tss =
      dow === 6
        ? Math.round(Math.max(0, 22 + noise * 0.4))
        : Math.round(Math.max(0, (base + variation + noise) * (isRec ? 0.5 : 1)));
  } else if (week < 22) {
    phase = "Peak";
    const isRec = (week - 15) % 4 === 3;
    tss =
      dow === 6
        ? Math.round(Math.max(0, 22 + noise * 0.4))
        : Math.round(
            Math.max(0, (120 + (dow % 2 === 0 ? 48 : 22) + noise) * (isRec ? 0.48 : 1)),
          );
  } else {
    phase = "Taper";
    const tapProg = Math.min(1, (week - 22) / 3.5);
    tss =
      dow === 6
        ? Math.round(Math.max(0, 22 + noise * 0.4))
        : Math.round(Math.max(10, 95 * (1 - tapProg * 0.72) + noise * 0.5));
  }

  const tsb = Math.round((ctl - atl) * 10) / 10;
  ctl += (tss - ctl) / 42;
  atl += (tss - atl) / 7;

  data.push({
    [DATE]: START_MS + i * DAY_MS,
    [TSS]: tss,
    [CTL]: Math.round(ctl * 10) / 10,
    [ATL]: Math.round(atl * 10) / 10,
    [TSB]: tsb,
    [PHASE]: phase,
  });
}

// Plot: reads only data and the constants above
const sortedData = [...data].sort((a, b) => Number(a[DATE]) - Number(b[DATE]));
const dates = sortedData.map((r) => new Date(Number(r[DATE])));
const tssData = sortedData.map((r) => Number(r[TSS]));
const ctlData = sortedData.map((r) => Number(r[CTL]));
const atlData = sortedData.map((r) => Number(r[ATL]));
const tsbData = sortedData.map((r) => Number(r[TSB]));

const tssScatter = sortedData.map((r, i) => ({
  x: dates[i],
  y: Number(r[TSS]),
  id: i,
}));

const finalPhaseName = String(sortedData[sortedData.length - 1][PHASE]);
const finalPhaseFirstRow = sortedData.find(
  (r) => String(r[PHASE]) === finalPhaseName,
)!;
const finalPhaseStartDate = new Date(Number(finalPhaseFirstRow[DATE]));

// CTL and ATL are averages of daily TSS, so TSS shares the load axis at its true values
const maxLoad = Math.max(...ctlData, ...atlData, ...tssData);
const loadAxisMax = maxLoad * (1 + LOAD_PAD_FRAC);

const maxAbsTsb = Math.max(...tsbData.map((v) => Math.abs(v)));
const tsbBound = maxAbsTsb * (1 + TSB_PAD_FRAC);

const unitMatch = CTL.match(/\(([^)]+)\)/);
const LOAD_UNIT = unitMatch ? unitMatch[1] : "";
const CTL_SERIES_LABEL = CTL.replace(/\s*\([^)]+\)$/, "");
const ATL_SERIES_LABEL = ATL.replace(/\s*\([^)]+\)$/, "");

const LEGEND_ITEMS = [
  { label: CTL_SERIES_LABEL, color: t.palette[0], kind: "line" as const },
  { label: ATL_SERIES_LABEL, color: t.palette[1], kind: "line" as const },
  { label: "Form (Fresh)", color: t.palette[2], kind: "area" as const },
  { label: "Form (Fatigued)", color: t.palette[4], kind: "area" as const },
  { label: `${TSS} (left axis)`, color: t.palette[3], kind: "dot" as const },
];

function TsbAreaLayer() {
  const xScale = useXScale("date") as (v: Date | number) => number;
  const yScale = useYScale("tsb") as (v: number) => number;

  const yZero = yScale(0);

  // Build exact zero-crossing polygons for positive (Fresh) and negative (Fatigued) TSB
  const posPts: Array<[number, number]> = [];
  const negPts: Array<[number, number]> = [];

  for (let i = 0; i < sortedData.length; i++) {
    const x = xScale(dates[i]);
    const val = tsbData[i];
    const y = yScale(val);

    if (i > 0) {
      const prevVal = tsbData[i - 1];
      if ((prevVal >= 0 && val < 0) || (prevVal < 0 && val >= 0)) {
        const prevX = xScale(dates[i - 1]);
        const frac = Math.abs(prevVal) / (Math.abs(prevVal) + Math.abs(val));
        const crossX = prevX + frac * (x - prevX);
        posPts.push([crossX, yZero]);
        negPts.push([crossX, yZero]);
      }
    }

    if (val >= 0) {
      posPts.push([x, y]);
      negPts.push([x, yZero]);
    } else {
      posPts.push([x, yZero]);
      negPts.push([x, y]);
    }
  }

  const firstX = xScale(dates[0]);
  const lastX = xScale(dates[dates.length - 1]);

  let posPath = `M${firstX.toFixed(1)},${yZero.toFixed(1)} `;
  for (const [px, py] of posPts) {
    posPath += `L${px.toFixed(1)},${py.toFixed(1)} `;
  }
  posPath += `L${lastX.toFixed(1)},${yZero.toFixed(1)} Z`;

  let negPath = `M${firstX.toFixed(1)},${yZero.toFixed(1)} `;
  for (const [px, py] of negPts) {
    negPath += `L${px.toFixed(1)},${py.toFixed(1)} `;
  }
  negPath += `L${lastX.toFixed(1)},${yZero.toFixed(1)} Z`;

  return (
    <g>
      <path d={posPath} fill={t.palette[2]} fillOpacity={0.3} stroke="none" />
      <path d={negPath} fill={t.palette[4]} fillOpacity={0.3} stroke="none" />
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  return (
    <Box
      sx={{
        width: W,
        height: H,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Title */}
      <Box
        sx={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          px: "40px",
          pt: "10px",
        }}
      >
        <Typography
          sx={{ color: t.ink, fontSize: "22px", fontWeight: 500, lineHeight: 1 }}
        >
          {TITLE}
        </Typography>
      </Box>

      {/* PMC chart */}
      <ChartsContainer
        skipAnimation
        width={W}
        height={H - TITLE_H - LEGEND_H}
        xAxis={[
          {
            id: "date",
            data: dates,
            scaleType: "time",
            height: 44,
            valueFormatter: (v: Date | number) => {
              const d = new Date(v);
              return d.toLocaleDateString("en-US", {
                month: "short",
                year: "numeric",
                timeZone: "UTC",
              });
            },
            tickNumber: 6,
            tickLabelStyle: { fill: t.inkSoft, fontSize: 14 },
          },
        ]}
        yAxis={[
          {
            id: "load",
            position: "left",
            width: 82,
            min: 0,
            max: loadAxisMax,
            label: LOAD_UNIT ? `Training load (${LOAD_UNIT})` : "Training load",
            tickLabelStyle: { fill: t.inkSoft, fontSize: 14 },
            labelStyle: { fill: t.inkSoft, fontSize: 15 },
          },
          {
            id: "tsb",
            position: "right",
            width: 82,
            min: -tsbBound,
            max: tsbBound,
            label: TSB,
            tickLabelStyle: { fill: t.inkSoft, fontSize: 14 },
            labelStyle: { fill: t.inkSoft, fontSize: 15 },
          },
        ]}
        series={[
          {
            id: "ctl",
            type: "line",
            data: ctlData,
            xAxisId: "date",
            yAxisId: "load",
            label: CTL_SERIES_LABEL,
            color: t.palette[0],
            showMark: false,
            curve: "monotoneX",
          },
          {
            id: "atl",
            type: "line",
            data: atlData,
            xAxisId: "date",
            yAxisId: "load",
            label: ATL_SERIES_LABEL,
            color: t.palette[1],
            showMark: false,
            curve: "monotoneX",
          },
          {
            id: "tss",
            type: "scatter",
            data: tssScatter,
            xAxisId: "date",
            yAxisId: "load",
            label: TSS,
            color: t.palette[3],
            markerSize: 3,
          },
        ]}
        margin={{ top: 20, bottom: 12, left: 16, right: 16 }}
        sx={{ "& .MuiScatterChart-marker": { fillOpacity: TSS_DOT_OPACITY } }}
      >
        <ChartsGrid horizontal />
        <TsbAreaLayer />
        <LinePlot skipAnimation />
        <ScatterPlot />
        <ChartsXAxis axisId="date" />
        <ChartsYAxis axisId="load" />
        <ChartsYAxis axisId="tsb" />
        {/* TSB = 0 horizontal reference — separates fresh from fatigued zones */}
        <ChartsReferenceLine
          y={0}
          axisId="tsb"
          lineStyle={{
            stroke: t.ink,
            strokeOpacity: 0.28,
            strokeDasharray: "6 3",
            strokeWidth: 1.5,
          }}
        />
        {/* Final phase start — marks the positive-form window before race day */}
        <ChartsReferenceLine
          x={finalPhaseStartDate}
          axisId="date"
          label={`↑ ${finalPhaseName}`}
          labelAlign="start"
          labelStyle={{ fill: t.inkSoft, fontSize: 14, fontStyle: "italic" }}
          lineStyle={{
            stroke: t.inkSoft,
            strokeOpacity: 0.4,
            strokeDasharray: "4 4",
            strokeWidth: 1,
          }}
        />
      </ChartsContainer>

      {/* Bottom Legend */}
      <Box
        sx={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "28px",
          pb: "8px",
        }}
      >
        {LEGEND_ITEMS.map((item) => (
          <Box
            key={item.label}
            sx={{ display: "flex", alignItems: "center", gap: "8px" }}
          >
            {item.kind === "line" ? (
              <Box
                sx={{
                  width: 20,
                  height: 3.5,
                  bgcolor: item.color,
                  borderRadius: "2px",
                }}
              />
            ) : item.kind === "area" ? (
              <Box
                sx={{
                  width: 18,
                  height: 12,
                  bgcolor: item.color,
                  opacity: 0.3,
                  borderRadius: "2px",
                }}
              />
            ) : (
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  bgcolor: item.color,
                  opacity: TSS_DOT_OPACITY,
                  borderRadius: "50%",
                }}
              />
            )}
            <Typography sx={{ color: t.inkSoft, fontSize: "14px", lineHeight: 1 }}>
              {item.label}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
