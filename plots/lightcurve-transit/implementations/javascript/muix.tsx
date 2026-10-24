// anyplot.ai
// lightcurve-transit: Astronomical Light Curve
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 87/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = '"Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, sans-serif';
const MONO = '"JetBrains Mono", "SFMono-Regular", Menlo, monospace';
const PHASE_AXIS_LABEL = "Orbital phase";
const BASELINE_FLUX = 1.0;
const Y_PAD_SHARE = 0.14;

// Columns: set these to your data's column names
const TIME = "Observation time (BJD - 2457000)"; // role: time
const PERIOD = "Orbital period (days)"; // role: period
const FLUX = "Relative flux"; // role: flux
const FLUX_ERR = "Flux uncertainty"; // role: flux_err
const MODEL_FLUX = "Transit model"; // role: model_flux

// Data: replace this block with your own records
const N_PTS = 280;
const ORBITAL_PERIOD_DAYS = 3.5247;
const EPOCH_BJD = 1325.41;
const TRANSIT_CENTER = 0.5;
const TRANSIT_HALF_DUR = 0.018;
const TRANSIT_DEPTH = 0.01;
const NOISE_SIGMA = 0.0015;

let lcgState = 42 >>> 0;
const data: Array<{
  [TIME]: number;
  [PERIOD]: number;
  [FLUX]: number;
  [FLUX_ERR]: number;
  [MODEL_FLUX]: number;
}> = [];

for (let i = 0; i < N_PTS; i += 1) {
  const ph = i / N_PTS;
  const orbitCycle = i === 0 ? 0 : i % 4;
  const timeBjd = EPOCH_BJD + (orbitCycle + ph) * ORBITAL_PERIOD_DAYS;

  const dt = Math.abs(ph - TRANSIT_CENTER);
  let modFlux = BASELINE_FLUX;
  if (dt < TRANSIT_HALF_DUR) {
    const u = 1 - dt / TRANSIT_HALF_DUR;
    const smooth = u * u * (3 - 2 * u);
    modFlux = BASELINE_FLUX - TRANSIT_DEPTH * smooth;
  }

  lcgState = (Math.imul(1664525, lcgState) + 1013904223) >>> 0;
  const r1 = lcgState / 0x100000000;
  const obsFlux = modFlux + (r1 * 2 - 1) * NOISE_SIGMA * 2.5;

  lcgState = (Math.imul(1664525, lcgState) + 1013904223) >>> 0;
  const r2 = lcgState / 0x100000000;
  const fluxErr = NOISE_SIGMA * (1 + r2 * 0.35);

  data.push({
    [TIME]: Number(timeBjd.toFixed(6)),
    [PERIOD]: ORBITAL_PERIOD_DAYS,
    [FLUX]: Number(obsFlux.toFixed(6)),
    [FLUX_ERR]: Number(fluxErr.toFixed(6)),
    [MODEL_FLUX]: Number(modFlux.toFixed(6)),
  });
}

// Plot: reads only data and the constants above
const rawTimes = data.map((d) => d[TIME]);
const minTime = Math.min(...rawTimes);
const maxTime = Math.max(...rawTimes);
const isAlreadyPhase = minTime >= 0 && maxTime <= 1;

const foldedRows = data
  .map((row) => {
    const p = row[PERIOD];
    const phase = isAlreadyPhase
      ? row[TIME]
      : (((row[TIME] - minTime) / p) % 1 + 1) % 1;
    return {
      ...row,
      phase,
    };
  })
  .sort((a, b) => a.phase - b.phase);

const phases = foldedRows.map((d) => d.phase);
const modelFlux = foldedRows.map((d) => d[MODEL_FLUX]);
const orbitalPeriod = foldedRows[0][PERIOD];

const minPhase = Math.min(...phases);
const maxPhase = Math.max(...phases);
const lowerExtents = foldedRows.map((d) => d[FLUX] - d[FLUX_ERR]);
const upperExtents = foldedRows.map((d) => d[FLUX] + d[FLUX_ERR]);
const minDataFlux = Math.min(...lowerExtents, ...modelFlux);
const maxDataFlux = Math.max(...upperExtents, ...modelFlux);
const fluxSpan = maxDataFlux - minDataFlux;
const FLUX_MIN = minDataFlux - fluxSpan * Y_PAD_SHARE;
const FLUX_MAX = maxDataFlux + fluxSpan * Y_PAD_SHARE;

const minModelFlux = Math.min(...modelFlux);
const transitDepthPct = ((BASELINE_FLUX - minModelFlux) * 100).toFixed(2);
const inTransitPhases = foldedRows
  .filter((r) => r[MODEL_FLUX] < BASELINE_FLUX - 1e-5)
  .map((r) => r.phase);
const transitPhaseSpan =
  inTransitPhases.length > 1
    ? Math.max(...inTransitPhases) - Math.min(...inTransitPhases)
    : 0;
const transitDurationHours = (
  transitPhaseSpan *
  orbitalPeriod *
  24
).toFixed(2);
const timeSpanDays = (maxTime - minTime).toFixed(1);

const OBS_COLOR = t.palette[0];
const MODEL_COLOR = t.palette[1];

function TransitDataLayer() {
  const xScale = useXScale("phase") as (v: number) => number;
  const yScale = useYScale("flux") as (v: number) => number;

  return (
    <g>
      {foldedRows.map((row, i) => {
        const x = xScale(row.phase);
        const yTop = yScale(row[FLUX] + row[FLUX_ERR]);
        const yBot = yScale(row[FLUX] - row[FLUX_ERR]);
        return (
          <line
            key={`err-${i}`}
            x1={x}
            y1={yTop}
            x2={x}
            y2={yBot}
            stroke={OBS_COLOR}
            strokeWidth={1.25}
            opacity={0.5}
          />
        );
      })}
      {foldedRows.map((row, i) => (
        <circle
          key={`pt-${i}`}
          cx={xScale(row.phase)}
          cy={yScale(row[FLUX])}
          r={3.5}
          fill={OBS_COLOR}
          opacity={0.84}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const headerHeight = 84;
  const chartHeight = height - headerHeight;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        color: t.ink,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          height: headerHeight,
          padding: "14px 44px 4px 116px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxSizing: "border-box",
        }}
      >
        <div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: t.ink,
              lineHeight: 1.2,
            }}
          >
            lightcurve-transit · javascript · muix · anyplot.ai
          </div>
          <div
            style={{
              fontSize: 14,
              color: t.inkSoft,
              marginTop: 4,
              fontFamily: MONO,
            }}
          >
            {foldedRows.length} phase-folded observations ({timeSpanDays} d
            span, P = {orbitalPeriod.toFixed(4)} d) · transit depth{" "}
            {transitDepthPct}% ({transitDurationHours} h duration)
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 24,
            fontSize: 15,
            color: t.ink,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 11,
                height: 11,
                borderRadius: "50%",
                background: OBS_COLOR,
                display: "inline-block",
              }}
            />
            <span>Observed {FLUX} (±1σ)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 24,
                height: 3,
                borderRadius: 2,
                background: MODEL_COLOR,
                display: "inline-block",
              }}
            />
            <span>{MODEL_FLUX}</span>
          </div>
        </div>
      </div>

      <ChartsContainer
        width={width}
        height={chartHeight}
        margin={{ left: 20, right: 40, top: 20, bottom: 20 }}
        skipAnimation
        series={[
          {
            type: "line",
            id: "model",
            xAxisId: "phase",
            yAxisId: "flux",
            data: modelFlux,
            label: MODEL_FLUX,
            color: MODEL_COLOR,
            showMark: false,
            curve: "natural",
          },
        ]}
        xAxis={[
          {
            id: "phase",
            data: phases,
            scaleType: "linear",
            min: minPhase,
            max: maxPhase,
            height: 60,
            label: PHASE_AXIS_LABEL,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink },
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: MONO,
            },
            valueFormatter: (v: number) => v.toFixed(2),
          },
        ]}
        yAxis={[
          {
            id: "flux",
            min: FLUX_MIN,
            max: FLUX_MAX,
            width: 96,
            label: FLUX,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink },
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: MONO,
            },
            valueFormatter: (v: number) => v.toFixed(3),
          },
        ]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <ChartsReferenceLine
          y={BASELINE_FLUX}
          axisId="flux"
          lineStyle={{
            stroke: t.inkSoft,
            strokeDasharray: "5 4",
            strokeWidth: 1.4,
          }}
        />
        <TransitDataLayer />
        <LinePlot skipAnimation />
        <ChartsXAxis axisId="phase" />
        <ChartsYAxis axisId="flux" />
      </ChartsContainer>
    </div>
  );
}
