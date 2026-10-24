// anyplot.ai
// lightcurve-transit: Astronomical Light Curve
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-06-20

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TIME_COL = "Observation Time (BJD - 2457000)";
const PERIOD_COL = "Orbital Period (days)";
const PHASE_COL = "Orbital Phase";
const FLUX_COL = "Relative Flux";
const FLUX_ERR_COL = "Flux Uncertainty";
const MODEL_FLUX_COL = "Transit Model";

const N_PTS = 280;
const ORBITAL_PERIOD_DAYS = 3.5247;
const EPOCH_BJD = 1325.41;
const TRANSIT_CENTER = 0.5;
const TRANSIT_HALF_DUR = 0.05;
const TRANSIT_DEPTH = 0.01;
const BASELINE_FLUX = 1.0;
const NOISE_SIGMA = 0.0015;
const Y_PAD_SHARE = 0.14;

// Data: 280 simulated TESS-like photometric observations folded by orbital period
let lcgState = 42 >>> 0;
const rawRows: Array<{
  [TIME_COL]: number;
  [PERIOD_COL]: number;
  [PHASE_COL]: number;
  [FLUX_COL]: number;
  [FLUX_ERR_COL]: number;
  [MODEL_FLUX_COL]: number;
}> = [];

for (let i = 0; i < N_PTS; i += 1) {
  const ph = i / (N_PTS - 1);
  const orbitCycle = i % 4;
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

  rawRows.push({
    [TIME_COL]: Number(timeBjd.toFixed(4)),
    [PERIOD_COL]: ORBITAL_PERIOD_DAYS,
    [PHASE_COL]: Number(ph.toFixed(5)),
    [FLUX_COL]: Number(obsFlux.toFixed(6)),
    [FLUX_ERR_COL]: Number(fluxErr.toFixed(6)),
    [MODEL_FLUX_COL]: Number(modFlux.toFixed(6)),
  });
}

// Sort by orbital phase before drawing model curve
const DATA = [...rawRows].sort((a, b) => a[PHASE_COL] - b[PHASE_COL]);

const phases = DATA.map((d) => d[PHASE_COL]);
const observedFlux = DATA.map((d) => d[FLUX_COL]);
const fluxErrors = DATA.map((d) => d[FLUX_ERR_COL]);
const modelFlux = DATA.map((d) => d[MODEL_FLUX_COL]);
const times = DATA.map((d) => d[TIME_COL]);
const orbitalPeriod = DATA[0][PERIOD_COL];

const minPhase = Math.min(...phases);
const maxPhase = Math.max(...phases);
const lowerExtents = DATA.map((d) => d[FLUX_COL] - d[FLUX_ERR_COL]);
const upperExtents = DATA.map((d) => d[FLUX_COL] + d[FLUX_ERR_COL]);
const minDataFlux = Math.min(...lowerExtents, ...modelFlux);
const maxDataFlux = Math.max(...upperExtents, ...modelFlux);
const fluxSpan = maxDataFlux - minDataFlux;
const FLUX_MIN = Number((minDataFlux - fluxSpan * Y_PAD_SHARE).toFixed(4));
const FLUX_MAX = Number((maxDataFlux + fluxSpan * Y_PAD_SHARE).toFixed(4));

const minModelFlux = Math.min(...modelFlux);
const transitDepthPct = ((BASELINE_FLUX - minModelFlux) * 100).toFixed(2);
const transitDurationHours = (
  TRANSIT_HALF_DUR *
  2 *
  orbitalPeriod *
  24
).toFixed(2);
const bjdSpanDays = (Math.max(...times) - Math.min(...times)).toFixed(1);

const OBS_COLOR = t.palette[0];
const MODEL_COLOR = t.palette[1];

function TransitDataLayer() {
  const xScale = useXScale("phase") as (v: number) => number;
  const yScale = useYScale("flux") as (v: number) => number;
  if (!xScale || !yScale) return null;

  return (
    <g>
      {DATA.map((row, i) => {
        const x = xScale(row[PHASE_COL]);
        const yTop = yScale(row[FLUX_COL] + row[FLUX_ERR_COL]);
        const yBot = yScale(row[FLUX_COL] - row[FLUX_ERR_COL]);
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
      {DATA.map((row, i) => (
        <circle
          key={`pt-${i}`}
          cx={xScale(row[PHASE_COL])}
          cy={yScale(row[FLUX_COL])}
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
        fontFamily: t.sans,
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
            Exoplanet Transit · lightcurve-transit · javascript · muix ·
            anyplot.ai
          </div>
          <div
            style={{
              fontSize: 14,
              color: t.inkSoft,
              marginTop: 4,
              fontFamily: t.mono,
            }}
          >
            {DATA.length} phase-folded observations ({bjdSpanDays} d baseline, P
            = {orbitalPeriod.toFixed(4)} d) · transit depth {transitDepthPct}% (
            {transitDurationHours} h duration)
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
            <span>Observed {FLUX_COL} (±1σ)</span>
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
            <span>{MODEL_FLUX_COL}</span>
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
            label: MODEL_FLUX_COL,
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
            label: PHASE_COL,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink },
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: t.mono,
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
            label: FLUX_COL,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink },
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: t.mono,
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
