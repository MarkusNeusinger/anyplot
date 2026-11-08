// anyplot.ai
// rug-basic: Basic Rug Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 85/100 | Updated: 2026-11-08

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.04; // x padding on each side as a share of the value span
const TICK_SHARE = 0.18; // tick length as a share of the plot height
const TICK_ALPHA = 0.5; // overlapping ticks add up to darker clusters

// Columns: set these to your data's column names
const REACTION_TIME = "Reaction time (ms)"; // role: values

// Data: replace this block with your own records, one object per row
// Reaction times in a visual cognitive task: morning and evening trials plus a few
// slow "attention lapse" trials in the right tail.
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (Math.imul(1664525, seed) + 1013904223) | 0;
    return (seed >>> 0) / 4294967296;
  };
  const randn = () => Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-10))) * Math.cos(2 * Math.PI * rand());
  const morning = Array.from({ length: 140 }, () => 420 + 55 * randn());
  const evening = Array.from({ length: 140 }, () => 458 + 70 * randn());
  const lapses = [636, 688, 706, 727];
  return [...morning, ...evening, ...lapses].map((v) => ({ [REACTION_TIME]: Math.round(v * 10) / 10 }));
})();

// Plot: reads only data and the constants above
const values = data.map((d) => d[REACTION_TIME]);
const valueMin = Math.min(...values);
const valueMax = Math.max(...values);
const pad = (valueMax - valueMin) * PAD_SHARE;

const TITLE = "rug-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `n = ${values.length} · range ${Math.round(valueMin)} to ${Math.round(valueMax)} · one tick per observation`;
const HEADER_HEIGHT = 84;

function RugTicks() {
  const xScale = useXScale();
  const area = useDrawingArea();
  const baseline = area.top + area.height;
  const tickTop = baseline - area.height * TICK_SHARE;
  return (
    <g>
      {values.map((v, i) => (
        <line
          key={`tick-${i}`}
          x1={xScale(v)}
          x2={xScale(v)}
          y1={baseline}
          y2={tickTop}
          stroke={t.palette[0]}
          strokeWidth={2.5}
          strokeOpacity={TICK_ALPHA}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - HEADER_HEIGHT}
        series={[]}
        skipAnimation
        margin={{ top: 24, right: 64, bottom: 24, left: 64 }}
        xAxis={[
          {
            scaleType: "linear",
            min: valueMin - pad,
            max: valueMax + pad,
            label: REACTION_TIME,
            height: 72,
            tickNumber: 12,
            valueFormatter: (v: number) => `${Math.round(v)}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[{ position: "none", min: 0, max: 1 }]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <RugTicks />
        <ChartsXAxis />
      </ChartsContainer>
    </div>
  );
}
