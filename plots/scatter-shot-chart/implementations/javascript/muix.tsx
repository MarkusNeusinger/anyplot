// anyplot.ai
// scatter-shot-chart: Basketball Shot Chart
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-21
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-shot-chart · javascript · muix · anyplot.ai";
const BASKET_Y = 5.25;
const THREE_PT_R = 23.75;
const CORNER_X = 22;
const CORNER_TOP_Y = BASKET_Y + Math.sqrt(THREE_PT_R ** 2 - CORNER_X ** 2);
const X_MIN = -25;
const X_MAX = 25;
const Y_MIN = 0;
const Y_MAX = 47;
const MADE_COLOR = "#009E73";
const MISSED_COLOR = "#AE3030";
const SHOT_RADIUS_MAP = {
  "free-throw": 4.5,
  "2-pointer": 5.5,
  "3-pointer": 6.5,
};

// Columns: set these to your data's column names
const X_POS = "Horizontal court position (ft)"; // role: x
const Y_POS = "Vertical court position (ft)"; // role: y
const MADE = "Shot made"; // role: made
const SHOT_TYPE = "Shot type"; // role: shot_type

// Data: replace this block with your own records
const N_SHOTS = 300;
let seed = 42;
const data = [];

for (let i = 0; i < N_SHOTS; i += 1) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const zone = seed / 4294967296;
  let x;
  let y;
  let shotType;

  if (zone < 0.2) {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    const angle = (seed / 4294967296) * Math.PI;
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    const dist = (seed / 4294967296) * 4 + 0.5;
    x = Math.cos(angle) * dist;
    y = BASKET_Y + Math.abs(Math.sin(angle)) * dist;
    shotType = "2-pointer";
  } else if (zone < 0.25) {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    x = -((seed / 4294967296) * 2.5 + 21.5);
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    y = (seed / 4294967296) * 10 + 0.5;
    shotType = "3-pointer";
  } else if (zone < 0.3) {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    x = (seed / 4294967296) * 2.5 + 21.5;
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    y = (seed / 4294967296) * 10 + 0.5;
    shotType = "3-pointer";
  } else if (zone < 0.58) {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    const angle = (seed / 4294967296) * Math.PI;
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    const dist = (seed / 4294967296) * 8 + 9;
    x = Math.cos(angle) * dist;
    y = BASKET_Y + Math.sin(angle) * dist;
    if (y < 0.5) {
      seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
      y = 0.5 + (seed / 4294967296) * 2;
    }
    const d = Math.sqrt(x ** 2 + (y - BASKET_Y) ** 2);
    if (d > 22) {
      x = (x / d) * 21.5;
      y = BASKET_Y + ((y - BASKET_Y) / d) * 21.5;
    }
    shotType = "2-pointer";
  } else if (zone < 0.85) {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    const angle = (seed / 4294967296) * Math.PI;
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    const dist = (seed / 4294967296) * 4.5 + THREE_PT_R;
    x = Math.cos(angle) * dist;
    y = BASKET_Y + Math.sin(angle) * dist;
    if (y < 0.5) {
      seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
      y = 0.5 + (seed / 4294967296) * 2;
    }
    if (y > 44) y = 44;
    x = Math.max(-24.5, Math.min(24.5, x));
    shotType = "3-pointer";
  } else {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    x = (seed / 4294967296) * 0.8 - 0.4;
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    y = 19 + (seed / 4294967296) * 0.6 - 0.3;
    shotType = "free-throw";
  }

  const d = Math.sqrt(x ** 2 + (y - BASKET_Y) ** 2);
  const makePct =
    shotType === "free-throw"
      ? 0.78
      : shotType === "3-pointer"
        ? 0.37
        : d < 7
          ? 0.6
          : 0.41;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const made = seed / 4294967296 < makePct;

  data.push({
    [X_POS]: parseFloat(x.toFixed(2)),
    [Y_POS]: parseFloat(y.toFixed(2)),
    [MADE]: made,
    [SHOT_TYPE]: shotType,
  });
}

// Plot: reads only data and the constants above
const allShots = data.map((row, id) => ({
  id,
  x: Number(row[X_POS]),
  y: Number(row[Y_POS]),
  made: Boolean(row[MADE]),
  shotType: String(row[SHOT_TYPE]),
}));

const missedShots = allShots.filter((s) => !s.made);
const madeShots = allShots.filter((s) => s.made);
const courtStroke =
  window.ANYPLOT_THEME === "light" ? "rgba(26,26,23,0.40)" : "rgba(240,239,232,0.50)";

function CourtAndShotsLayer() {
  const { left, top, width, height } = useDrawingArea();
  const canvasH = window.ANYPLOT_SIZE.height;
  const xSpan = X_MAX - X_MIN;
  const ySpan = Y_MAX - Y_MIN;

  const threeRx = (THREE_PT_R / xSpan) * width;
  const threeRy = (THREE_PT_R / ySpan) * height;
  const ftCircRx = (6 / xSpan) * width;
  const ftCircRy = (6 / ySpan) * height;
  const raRx = (4 / xSpan) * width;
  const raRy = (4 / ySpan) * height;
  const basketRx = (0.75 / xSpan) * width;
  const basketRy = (0.75 / ySpan) * height;

  const xAtm25 = left;
  const xAt25 = left + width;
  const xAtm8 = left + ((-8 - X_MIN) / xSpan) * width;
  const xAt8 = left + ((8 - X_MIN) / xSpan) * width;
  const xAtm4 = left + ((-4 - X_MIN) / xSpan) * width;
  const xAt4 = left + ((4 - X_MIN) / xSpan) * width;
  const xAtm3 = left + ((-3 - X_MIN) / xSpan) * width;
  const xAt3 = left + ((3 - X_MIN) / xSpan) * width;
  const xAtmCorner = left + ((-CORNER_X - X_MIN) / xSpan) * width;
  const xAtCorner = left + ((CORNER_X - X_MIN) / xSpan) * width;
  const xAt0 = left + ((0 - X_MIN) / xSpan) * width;

  const yAt0 = top + height;
  const yAt47 = top;
  const yAt19 = top + ((Y_MAX - 19) / ySpan) * height;
  const yAt4 = top + ((Y_MAX - 4) / ySpan) * height;
  const yAtBasket = top + ((Y_MAX - BASKET_Y) / ySpan) * height;
  const yAtCornerTop = top + ((Y_MAX - CORNER_TOP_Y) / ySpan) * height;

  const ls = {
    fill: "none",
    stroke: courtStroke,
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  const legendY = canvasH - 36;
  const centerX = left + width / 2;

  return (
    <g>
      <text
        x={centerX}
        y={top - 24}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        {TITLE}
      </text>

      <rect
        x={xAtm25}
        y={yAt47}
        width={xAt25 - xAtm25}
        height={yAt0 - yAt47}
        style={{ ...ls, strokeWidth: 2.5 }}
      />
      <rect
        x={xAtm8}
        y={yAt19}
        width={xAt8 - xAtm8}
        height={yAt0 - yAt19}
        style={ls}
      />
      <ellipse cx={xAt0} cy={yAt19} rx={ftCircRx} ry={ftCircRy} style={ls} />
      <path
        d={`M ${xAtm4} ${yAtBasket} A ${raRx} ${raRy} 0 0 1 ${xAt4} ${yAtBasket}`}
        style={ls}
      />
      <line x1={xAtmCorner} y1={yAt0} x2={xAtmCorner} y2={yAtCornerTop} style={ls} />
      <line x1={xAtCorner} y1={yAt0} x2={xAtCorner} y2={yAtCornerTop} style={ls} />
      <path
        d={`M ${xAtmCorner} ${yAtCornerTop} A ${threeRx} ${threeRy} 0 0 1 ${xAtCorner} ${yAtCornerTop}`}
        style={ls}
      />
      <line x1={xAtm3} y1={yAt4} x2={xAt3} y2={yAt4} style={{ ...ls, strokeWidth: 4 }} />
      <ellipse
        cx={xAt0}
        cy={yAtBasket}
        rx={basketRx}
        ry={basketRy}
        style={{ ...ls, strokeWidth: 2.5 }}
      />

      {missedShots.map((shot) => {
        const sx = left + ((shot.x - X_MIN) / xSpan) * width;
        const sy = top + ((Y_MAX - shot.y) / ySpan) * height;
        const r = SHOT_RADIUS_MAP[shot.shotType];
        return (
          <path
            key={shot.id}
            d={`M ${sx - r} ${sy - r} L ${sx + r} ${sy + r} M ${sx + r} ${sy - r} L ${sx - r} ${sy + r}`}
            stroke={MISSED_COLOR}
            strokeWidth={r * 0.55}
            strokeOpacity={0.7}
            strokeLinecap="round"
          />
        );
      })}

      {madeShots.map((shot) => {
        const sx = left + ((shot.x - X_MIN) / xSpan) * width;
        const sy = top + ((Y_MAX - shot.y) / ySpan) * height;
        const r = SHOT_RADIUS_MAP[shot.shotType];
        return (
          <circle
            key={shot.id}
            cx={sx}
            cy={sy}
            r={r}
            fill={MADE_COLOR}
            fillOpacity={0.7}
          />
        );
      })}

      <g transform={`translate(${centerX - 110}, ${legendY})`}>
        <path
          d="M -6 -6 L 6 6 M 6 -6 L -6 6"
          stroke={MISSED_COLOR}
          strokeWidth={3.2}
          strokeLinecap="round"
        />
        <text x={16} y={0} fontSize={18} fill={t.ink} dominantBaseline="central">
          Missed
        </text>
      </g>
      <g transform={`translate(${centerX + 40}, ${legendY})`}>
        <circle cx={0} cy={0} r={7} fill={MADE_COLOR} />
        <text x={16} y={0} fontSize={18} fill={t.ink} dominantBaseline="central">
          Made
        </text>
      </g>
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  return (
    <ChartsContainer
      width={W}
      height={H}
      skipAnimation
      series={[]}
      xAxis={[{ min: X_MIN, max: X_MAX, scaleType: "linear", position: "none" }]}
      yAxis={[{ min: Y_MIN, max: Y_MAX, scaleType: "linear", position: "none" }]}
      margin={{ top: 76, bottom: 108, left: 60, right: 60 }}
    >
      <CourtAndShotsLayer />
    </ChartsContainer>
  );
}
