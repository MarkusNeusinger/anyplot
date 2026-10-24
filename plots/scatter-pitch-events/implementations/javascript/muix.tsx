// anyplot.ai
// scatter-pitch-events: Soccer Pitch Event Map
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-21

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-pitch-events · javascript · muix · anyplot.ai";
const PITCH_LENGTH = 105;
const PITCH_WIDTH = 68;
const PITCH_GREEN = "#2a6e1e";
const LINE_W = "rgba(255,255,255,0.88)";
const LW = 1.8;
const DEG = Math.PI / 180;
const CIRCLE_R = 9.15;
const PEN_DEPTH = 16.5;
const PEN_HW = 20.16;
const GOAL_DEPTH = 5.5;
const GOAL_HW = 9.16;
const GOAL_MOUTH_HW = 3.66;
const EVENT_ORDER = ["Pass", "Shot", "Tackle", "Interception"];

// Columns: set these to your data's column names
const X_POS = "Start X (m)"; // role: x
const Y_POS = "Start Y (m)"; // role: y
const END_X = "End X (m)"; // role: end_x
const END_Y = "End Y (m)"; // role: end_y
const EVENT_TYPE = "Event type"; // role: event_type
const OUTCOME = "Outcome"; // role: outcome

// Data: replace this block with your own records
let seed = 42;
const data = [];

for (let i = 0; i < 48; i += 1) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const x = (seed / 4294967296) * 100 + 2.5;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const y = (seed / 4294967296) * 63 + 2.5;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const dx = (seed / 4294967296 - 0.2) * 22;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const dy = (seed / 4294967296 - 0.5) * 16;
  const x2 = Math.max(2, Math.min(103, x + dx));
  const y2 = Math.max(2, Math.min(66, y + dy));
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const successful = seed / 4294967296 > 0.22;
  data.push({
    [X_POS]: x,
    [Y_POS]: y,
    [END_X]: x2,
    [END_Y]: y2,
    [EVENT_TYPE]: "Pass",
    [OUTCOME]: successful ? "Successful" : "Unsuccessful",
  });
}

for (let i = 0; i < 10; i += 1) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const x = 70 + (seed / 4294967296) * 30;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const y = 17 + (seed / 4294967296) * 34;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const x2 = 102 + (seed / 4294967296) * 3;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const y2 = 30.34 + (seed / 4294967296) * 7.32;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const successful = seed / 4294967296 > 0.75;
  data.push({
    [X_POS]: x,
    [Y_POS]: y,
    [END_X]: x2,
    [END_Y]: y2,
    [EVENT_TYPE]: "Shot",
    [OUTCOME]: successful ? "Successful" : "Unsuccessful",
  });
}

for (let i = 0; i < 22; i += 1) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const x = (seed / 4294967296) * 105;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const y = (seed / 4294967296) * 68;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const successful = seed / 4294967296 > 0.35;
  data.push({
    [X_POS]: x,
    [Y_POS]: y,
    [END_X]: null,
    [END_Y]: null,
    [EVENT_TYPE]: "Tackle",
    [OUTCOME]: successful ? "Successful" : "Unsuccessful",
  });
}

for (let i = 0; i < 18; i += 1) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const x = (seed / 4294967296) * 105;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const y = (seed / 4294967296) * 68;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const successful = seed / 4294967296 > 0.12;
  data.push({
    [X_POS]: x,
    [Y_POS]: y,
    [END_X]: null,
    [END_Y]: null,
    [EVENT_TYPE]: "Interception",
    [OUTCOME]: successful ? "Successful" : "Unsuccessful",
  });
}

// Plot: reads only data and the constants above
const events = data.map((row, idx) => ({
  id: `ev-${idx}`,
  x: Number(row[X_POS]),
  y: Number(row[Y_POS]),
  endX: row[END_X] !== null && row[END_X] !== undefined ? Number(row[END_X]) : null,
  endY: row[END_Y] !== null && row[END_Y] !== undefined ? Number(row[END_Y]) : null,
  type: String(row[EVENT_TYPE]),
  successful: String(row[OUTCOME]).toLowerCase() === "successful",
}));

const passes = events.filter((e) => e.type === "Pass");
const shots = events.filter((e) => e.type === "Shot");
const tackles = events.filter((e) => e.type === "Tackle");
const interceptions = events.filter((e) => e.type === "Interception");

const passHex = t.palette[0];
const shotHex = t.palette[1];
const tackleHex = t.palette[2];
const interceptHex = t.palette[3];

const passNum = parseInt(passHex.slice(1), 16);
const shotNum = parseInt(shotHex.slice(1), 16);
const tackleNum = parseInt(tackleHex.slice(1), 16);
const interceptNum = parseInt(interceptHex.slice(1), 16);

const passOk = `rgba(${(passNum >> 16) & 255},${(passNum >> 8) & 255},${passNum & 255},0.75)`;
const passFail = `rgba(${(passNum >> 16) & 255},${(passNum >> 8) & 255},${passNum & 255},0.3)`;
const passMarkerFail = `rgba(${(passNum >> 16) & 255},${(passNum >> 8) & 255},${passNum & 255},0.35)`;

const shotOk = `rgba(${(shotNum >> 16) & 255},${(shotNum >> 8) & 255},${shotNum & 255},0.85)`;
const shotFail = `rgba(${(shotNum >> 16) & 255},${(shotNum >> 8) & 255},${shotNum & 255},0.38)`;
const shotMarkerFail = `rgba(${(shotNum >> 16) & 255},${(shotNum >> 8) & 255},${shotNum & 255},0.4)`;

const tackleMarkerFail = `rgba(${(tackleNum >> 16) & 255},${(tackleNum >> 8) & 255},${tackleNum & 255},0.35)`;
const interceptMarkerFail = `rgba(${(interceptNum >> 16) & 255},${(interceptNum >> 8) & 255},${interceptNum & 255},0.35)`;

function PitchEventLayer() {
  const { left, top, width: drawW, height: drawH } = useDrawingArea();
  const xScale = useXScale();
  const yScale = useYScale();
  const { width, height } = window.ANYPLOT_SIZE;

  const goalDepthPx = xScale(2) - xScale(0);

  const centerCirclePts = Array.from({ length: 361 }, (_, a) => {
    const rad = a * DEG;
    return `${xScale(52.5 + CIRCLE_R * Math.cos(rad))},${yScale(34 + CIRCLE_R * Math.sin(rad))}`;
  }).join(" ");

  const leftPenArcPts = [];
  for (let a = -60; a <= 60; a += 1) {
    const px = 11 + CIRCLE_R * Math.cos(a * DEG);
    const py = 34 + CIRCLE_R * Math.sin(a * DEG);
    if (px > PEN_DEPTH) leftPenArcPts.push(`${xScale(px)},${yScale(py)}`);
  }

  const rightPenArcPts = [];
  for (let a = 120; a <= 240; a += 1) {
    const px = 94 + CIRCLE_R * Math.cos(a * DEG);
    const py = 34 + CIRCLE_R * Math.sin(a * DEG);
    if (px < PITCH_LENGTH - PEN_DEPTH) rightPenArcPts.push(`${xScale(px)},${yScale(py)}`);
  }

  const cornerSpecs = [
    { cx: 0, cy: 0, a0: 0, a1: 90 },
    { cx: PITCH_LENGTH, cy: 0, a0: 90, a1: 180 },
    { cx: 0, cy: PITCH_WIDTH, a0: -90, a1: 0 },
    { cx: PITCH_LENGTH, cy: PITCH_WIDTH, a0: 180, a1: 270 },
  ];

  const lp = { fill: "none", stroke: LINE_W, strokeWidth: LW };
  const legendY = height - 42;
  const legendSpacing = 170;
  const legendStartX = width / 2 - ((EVENT_ORDER.length - 1) * legendSpacing) / 2;

  return (
    <g>
      <rect x={left} y={top} width={drawW} height={drawH} fill={PITCH_GREEN} />

      <rect
        {...lp}
        x={xScale(0)}
        y={yScale(PITCH_WIDTH)}
        width={Math.abs(xScale(PITCH_LENGTH) - xScale(0))}
        height={Math.abs(yScale(0) - yScale(PITCH_WIDTH))}
      />

      <line {...lp} x1={xScale(52.5)} y1={yScale(0)} x2={xScale(52.5)} y2={yScale(PITCH_WIDTH)} />
      <polyline {...lp} points={centerCirclePts} />
      <circle cx={xScale(52.5)} cy={yScale(34)} r={4} fill={LINE_W} />

      <rect
        {...lp}
        x={xScale(0)}
        y={yScale(34 + PEN_HW)}
        width={Math.abs(xScale(PEN_DEPTH) - xScale(0))}
        height={Math.abs(yScale(34 - PEN_HW) - yScale(34 + PEN_HW))}
      />
      <rect
        {...lp}
        x={xScale(PITCH_LENGTH - PEN_DEPTH)}
        y={yScale(34 + PEN_HW)}
        width={Math.abs(xScale(PITCH_LENGTH) - xScale(PITCH_LENGTH - PEN_DEPTH))}
        height={Math.abs(yScale(34 - PEN_HW) - yScale(34 + PEN_HW))}
      />

      <rect
        {...lp}
        x={xScale(0)}
        y={yScale(34 + GOAL_HW)}
        width={Math.abs(xScale(GOAL_DEPTH) - xScale(0))}
        height={Math.abs(yScale(34 - GOAL_HW) - yScale(34 + GOAL_HW))}
      />
      <rect
        {...lp}
        x={xScale(PITCH_LENGTH - GOAL_DEPTH)}
        y={yScale(34 + GOAL_HW)}
        width={Math.abs(xScale(PITCH_LENGTH) - xScale(PITCH_LENGTH - GOAL_DEPTH))}
        height={Math.abs(yScale(34 - GOAL_HW) - yScale(34 + GOAL_HW))}
      />

      <rect
        x={xScale(0) - goalDepthPx}
        y={yScale(34 + GOAL_MOUTH_HW)}
        width={goalDepthPx}
        height={Math.abs(yScale(34 - GOAL_MOUTH_HW) - yScale(34 + GOAL_MOUTH_HW))}
        fill="none"
        stroke={LINE_W}
        strokeWidth={LW}
      />
      <rect
        x={xScale(PITCH_LENGTH)}
        y={yScale(34 + GOAL_MOUTH_HW)}
        width={goalDepthPx}
        height={Math.abs(yScale(34 - GOAL_MOUTH_HW) - yScale(34 + GOAL_MOUTH_HW))}
        fill="none"
        stroke={LINE_W}
        strokeWidth={LW}
      />

      <circle cx={xScale(11)} cy={yScale(34)} r={3} fill={LINE_W} />
      <circle cx={xScale(94)} cy={yScale(34)} r={3} fill={LINE_W} />

      <polyline {...lp} points={leftPenArcPts.join(" ")} />
      <polyline {...lp} points={rightPenArcPts.join(" ")} />

      {cornerSpecs.map((c, idx) => {
        const steps = Math.abs(c.a1 - c.a0);
        const pts = Array.from({ length: steps + 1 }, (_, k) => {
          const a = (c.a0 + ((c.a1 - c.a0) * k) / steps) * DEG;
          return `${xScale(c.cx + Math.cos(a))},${yScale(c.cy + Math.sin(a))}`;
        }).join(" ");
        return <polyline key={idx} {...lp} points={pts} />;
      })}

      <defs>
        <marker id="arr-pass-ok" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="3" markerHeight="3" orient="auto">
          <path d="M 0 0 L 8 4 L 0 8 z" fill={passOk} />
        </marker>
        <marker id="arr-pass-fail" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="3" markerHeight="3" orient="auto">
          <path d="M 0 0 L 8 4 L 0 8 z" fill={passFail} />
        </marker>
        <marker id="arr-shot-ok" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="3.5" markerHeight="3.5" orient="auto">
          <path d="M 0 0 L 8 4 L 0 8 z" fill={shotOk} />
        </marker>
        <marker id="arr-shot-fail" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="3.5" markerHeight="3.5" orient="auto">
          <path d="M 0 0 L 8 4 L 0 8 z" fill={shotFail} />
        </marker>
      </defs>

      {passes.map((p) => (
        <line
          key={p.id}
          x1={xScale(p.x)}
          y1={yScale(p.y)}
          x2={xScale(Number(p.endX))}
          y2={yScale(Number(p.endY))}
          stroke={p.successful ? passOk : passFail}
          strokeWidth={p.successful ? 1.6 : 1.1}
          strokeDasharray={p.successful ? undefined : "4,3"}
          markerEnd={p.successful ? "url(#arr-pass-ok)" : "url(#arr-pass-fail)"}
        />
      ))}

      {shots.map((s) => (
        <line
          key={s.id}
          x1={xScale(s.x)}
          y1={yScale(s.y)}
          x2={xScale(Number(s.endX))}
          y2={yScale(Number(s.endY))}
          stroke={s.successful ? shotOk : shotFail}
          strokeWidth={s.successful ? 2.2 : 1.6}
          strokeDasharray={s.successful ? undefined : "5,3"}
          markerEnd={s.successful ? "url(#arr-shot-ok)" : "url(#arr-shot-fail)"}
        />
      ))}

      {passes.map((p) => (
        <circle
          key={`m-${p.id}`}
          cx={xScale(p.x)}
          cy={yScale(p.y)}
          r={p.successful ? 7 : 5}
          fill={p.successful ? passHex : passMarkerFail}
        />
      ))}

      {shots.map((s) => {
        const cx = xScale(s.x);
        const cy = yScale(s.y);
        const r = s.successful ? 10 : 7;
        const inner = r * 0.4;
        const starPts = Array.from({ length: 10 }, (_, k) => {
          const angle = (k * Math.PI) / 5 - Math.PI / 2;
          const rad = k % 2 === 0 ? r : inner;
          return `${cx + rad * Math.cos(angle)},${cy + rad * Math.sin(angle)}`;
        }).join(" ");
        return <polygon key={`m-${s.id}`} points={starPts} fill={s.successful ? shotHex : shotMarkerFail} />;
      })}

      {tackles.map((tk) => {
        const cx = xScale(tk.x);
        const cy = yScale(tk.y);
        const r = tk.successful ? 8 : 6;
        const triPts = `${cx},${cy - r} ${cx - r * 0.866},${cy + r * 0.5} ${cx + r * 0.866},${cy + r * 0.5}`;
        return <polygon key={`m-${tk.id}`} points={triPts} fill={tk.successful ? tackleHex : tackleMarkerFail} />;
      })}

      {interceptions.map((ic) => {
        const cx = xScale(ic.x);
        const cy = yScale(ic.y);
        const r = ic.successful ? 8 : 6;
        const diaPts = `${cx},${cy - r} ${cx + r * 0.7},${cy} ${cx},${cy + r} ${cx - r * 0.7},${cy}`;
        return <polygon key={`m-${ic.id}`} points={diaPts} fill={ic.successful ? interceptHex : interceptMarkerFail} />;
      })}

      {EVENT_ORDER.map((label, i) => {
        const lx = legendStartX + i * legendSpacing;
        const color = t.palette[i];
        return (
          <g key={`leg-${label}`}>
            <rect x={lx - 42} y={legendY - 6} width={18} height={12} rx={2} fill={color} />
            <text x={lx - 16} y={legendY} fontSize={14} fill={t.ink} dominantBaseline="middle">
              {label}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  const topM = 68;
  const botM = 92;
  const pitchH = height - topM - botM;
  const pitchW = Math.round(pitchH * (PITCH_LENGTH / PITCH_WIDTH));
  const hM = Math.round((width - pitchW) / 2);
  const margin = { top: topM, bottom: botM, left: hM, right: hM };
  const titleSize = Math.round(22 * Math.min(1, 67 / TITLE.length));

  return (
    <ChartsContainer
      width={width}
      height={height}
      margin={margin}
      xAxis={[{ id: "x", min: 0, max: PITCH_LENGTH, scaleType: "linear", position: "none" }]}
      yAxis={[{ id: "y", min: 0, max: PITCH_WIDTH, scaleType: "linear", position: "none" }]}
      series={[]}
      skipAnimation
    >
      <PitchEventLayer />
      <text
        x={width / 2}
        y={topM / 2}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={titleSize}
        fontWeight="600"
        fill={t.ink}
      >
        {TITLE}
      </text>
    </ChartsContainer>
  );
}
