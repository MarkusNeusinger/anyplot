// anyplot.ai
// column-stratigraphic: Stratigraphic Column with Lithology Patterns
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 95/100 | Created: 2026-06-17

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// Constants
const TITLE = "column-stratigraphic · javascript · muix · anyplot.ai";
const FONT =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
const PATTERN_TYPES = ["stipple", "dash", "brick", "rhomb", "silt", "clasts"] as const;
const LITHOLOGY_PATTERN_MAP: Record<string, (typeof PATTERN_TYPES)[number]> = {
  Sandstone: "stipple",
  Shale: "dash",
  Limestone: "brick",
  Dolomite: "rhomb",
  Siltstone: "silt",
  Conglomerate: "clasts",
};

const COL_LEFT = 4.25;
const COL_RIGHT = 7.7;
const COL_TOP_Y = 7.7;
const COL_BOT_Y = 0.6;
const AXIS_X = 4.05;
const BRACKET_X = 2.95;
const FORM_X = 7.95;
const LEGEND_X = 11.3;
const LEGEND_STEP = 0.72;
const TICK_COUNT = 7;
const WAVY_SAMPLES = 48;

// Columns: set these to your data's column names
const TOP = "Top depth (m)"; // role: top
const BOTTOM = "Bottom depth (m)"; // role: bottom
const LITHOLOGY = "Lithology"; // role: lithology
const FORMATION = "Formation"; // role: formation
const STAGE_AGE = "Stage age"; // role: age
const PERIOD = "Geological period"; // role: extra
const PERIOD_SPAN = "Period span"; // role: extra
const UNCONFORMITY = "Unconformity"; // role: extra

// Data: replace this block with your own records
const data = [
  {
    [TOP]: 0,
    [BOTTOM]: 28,
    [LITHOLOGY]: "Sandstone",
    [FORMATION]: "Horseshoe Canyon Fm",
    [STAGE_AGE]: "Maastrichtian",
    [PERIOD]: "Cretaceous",
    [PERIOD_SPAN]: "145–66 Ma",
    [UNCONFORMITY]: false,
  },
  {
    [TOP]: 28,
    [BOTTOM]: 62,
    [LITHOLOGY]: "Shale",
    [FORMATION]: "Bearpaw Shale",
    [STAGE_AGE]: "Campanian",
    [PERIOD]: "Cretaceous",
    [PERIOD_SPAN]: "145–66 Ma",
    [UNCONFORMITY]: false,
  },
  {
    [TOP]: 62,
    [BOTTOM]: 88,
    [LITHOLOGY]: "Sandstone",
    [FORMATION]: "Belly River Fm",
    [STAGE_AGE]: "Campanian",
    [PERIOD]: "Cretaceous",
    [PERIOD_SPAN]: "145–66 Ma",
    [UNCONFORMITY]: false,
  },
  {
    [TOP]: 88,
    [BOTTOM]: 120,
    [LITHOLOGY]: "Limestone",
    [FORMATION]: "Rundle Group",
    [STAGE_AGE]: "Mississippian",
    [PERIOD]: "Carboniferous",
    [PERIOD_SPAN]: "359–299 Ma",
    [UNCONFORMITY]: true,
  },
  {
    [TOP]: 120,
    [BOTTOM]: 150,
    [LITHOLOGY]: "Dolomite",
    [FORMATION]: "Palliser Fm",
    [STAGE_AGE]: "Famennian",
    [PERIOD]: "Devonian",
    [PERIOD_SPAN]: "419–359 Ma",
    [UNCONFORMITY]: false,
  },
  {
    [TOP]: 150,
    [BOTTOM]: 178,
    [LITHOLOGY]: "Shale",
    [FORMATION]: "Ireton Fm",
    [STAGE_AGE]: "Frasnian",
    [PERIOD]: "Devonian",
    [PERIOD_SPAN]: "419–359 Ma",
    [UNCONFORMITY]: false,
  },
  {
    [TOP]: 178,
    [BOTTOM]: 214,
    [LITHOLOGY]: "Limestone",
    [FORMATION]: "Leduc Reef",
    [STAGE_AGE]: "Frasnian",
    [PERIOD]: "Devonian",
    [PERIOD_SPAN]: "419–359 Ma",
    [UNCONFORMITY]: false,
  },
  {
    [TOP]: 214,
    [BOTTOM]: 246,
    [LITHOLOGY]: "Siltstone",
    [FORMATION]: "Beaverhill Lake Gp",
    [STAGE_AGE]: "Givetian",
    [PERIOD]: "Devonian",
    [PERIOD_SPAN]: "419–359 Ma",
    [UNCONFORMITY]: false,
  },
  {
    [TOP]: 246,
    [BOTTOM]: 280,
    [LITHOLOGY]: "Conglomerate",
    [FORMATION]: "Basal Clastics",
    [STAGE_AGE]: "Cambrian",
    [PERIOD]: "Cambrian",
    [PERIOD_SPAN]: "539–485 Ma",
    [UNCONFORMITY]: true,
  },
];

// Plot: reads only data and the constants above
const DEPTH_UNIT = TOP.match(/\(([^)]+)\)/)?.[1] ?? "";
const depthUnitSuffix = DEPTH_UNIT ? ` ${DEPTH_UNIT}` : "";
const DEPTH_AXIS_TITLE = TOP.replace(/^Top\s+/i, "").replace(/^d/, "D");

const minDepth = Math.min(...data.map((d) => Number(d[TOP])));
const maxDepth = Math.max(...data.map((d) => Number(d[BOTTOM])));
const depthSpan = maxDepth - minDepth;
const worldSpan = COL_TOP_Y - COL_BOT_Y;

const LITHO_NAMES = Array.from(new Set(data.map((d) => String(d[LITHOLOGY]))));
const LITHO_COLORS = Object.fromEntries(
  LITHO_NAMES.map((name, idx) => [name, t.palette[idx]]),
);
const LITHO_IDS = Object.fromEntries(
  LITHO_NAMES.map((name, idx) => [name, `lith-${idx}`]),
);

const usedPatterns = new Set<string>(
  LITHO_NAMES.map((name) => LITHOLOGY_PATTERN_MAP[name]).filter(Boolean),
);
const unusedPatterns = PATTERN_TYPES.filter((p) => !usedPatterns.has(p));
let unusedIdx = 0;
const LITHO_PATTERNS: Record<string, (typeof PATTERN_TYPES)[number]> = {};
for (const name of LITHO_NAMES) {
  const mapped = LITHOLOGY_PATTERN_MAP[name];
  if (mapped) {
    LITHO_PATTERNS[name] = mapped;
  } else {
    if (unusedIdx >= unusedPatterns.length) {
      throw new Error(`Exceeded available lithology patterns (${PATTERN_TYPES.length})`);
    }
    LITHO_PATTERNS[name] = unusedPatterns[unusedIdx++];
  }
}

const LAYERS = data.map((d) => {
  const top = Number(d[TOP]);
  const bottom = Number(d[BOTTOM]);
  const litho = String(d[LITHOLOGY]);
  const yTopW = COL_TOP_Y - ((top - minDepth) / depthSpan) * worldSpan;
  const yBotW = COL_TOP_Y - ((bottom - minDepth) / depthSpan) * worldSpan;
  return {
    top,
    bottom,
    thickness: bottom - top,
    litho,
    patternId: LITHO_IDS[litho],
    formation: String(d[FORMATION]),
    age: String(d[STAGE_AGE]),
    period: String(d[PERIOD]),
    periodSpan: String(d[PERIOD_SPAN]),
    unconf: Boolean(d[UNCONFORMITY]),
    yTopW,
    yBotW,
    yMidW: (yTopW + yBotW) / 2,
  };
});

const PERIODS: {
  name: string;
  age: string;
  top: number;
  bottom: number;
  yTopW: number;
  yBotW: number;
}[] = [];
for (const layer of LAYERS) {
  const prev = PERIODS[PERIODS.length - 1];
  if (prev && prev.name === layer.period) {
    prev.bottom = layer.bottom;
    prev.yBotW = layer.yBotW;
  } else {
    PERIODS.push({
      name: layer.period,
      age: layer.periodSpan,
      top: layer.top,
      bottom: layer.bottom,
      yTopW: layer.yTopW,
      yBotW: layer.yBotW,
    });
  }
}

const rawStep = depthSpan / TICK_COUNT;
const stepMag = Math.pow(10, Math.floor(Math.log10(rawStep)));
const stepNorm = rawStep / stepMag;
const tickStep = (stepNorm <= 1.5 ? 1 : stepNorm <= 3.5 ? 2 : 5) * stepMag;
const DEPTH_TICKS = [];
for (let d = Math.ceil(minDepth / tickStep) * tickStep; d <= maxDepth + 1e-9; d += tickStep) {
  DEPTH_TICKS.push({
    depth: Number(d.toFixed(4)),
    yW: COL_TOP_Y - ((d - minDepth) / depthSpan) * worldSpan,
  });
}

const SUBTITLE = `${LAYERS.length} stratigraphic units (${minDepth}–${maxDepth}${depthUnitSuffix}) · ${LITHO_NAMES.length} ${LITHOLOGY} types across ${PERIODS.length} periods`;
const WAVY_STEPS = Array.from({ length: WAVY_SAMPLES + 1 }, (_, i) => i / WAVY_SAMPLES);

function StratigraphicLayer() {
  const xs = useXScale() as any;
  const ys = useYScale() as any;

  const xL = xs(COL_LEFT);
  const xR = xs(COL_RIGHT);
  const colW = xR - xL;
  const axisX = xs(AXIS_X);
  const bx = xs(BRACKET_X);
  const xLead = xs(FORM_X) - 8;
  const xText = xs(FORM_X);
  const legX = xs(LEGEND_X);
  const swW = xs(LEGEND_X + 0.85) - legX;
  const swH = Math.abs(ys(0) - ys(0.42));

  return (
    <g fontFamily={FONT}>
      <defs>
        {LITHO_NAMES.map((name) => {
          const color = LITHO_COLORS[name];
          const pid = LITHO_IDS[name];
          const patType = LITHO_PATTERNS[name];
          if (patType === "stipple") {
            return (
              <pattern key={pid} id={pid} patternUnits="userSpaceOnUse" width={24} height={24}>
                <rect width={24} height={24} fill={color} fillOpacity={0.26} />
                {[
                  [5, 5],
                  [17, 9],
                  [9, 17],
                  [20, 20],
                  [13, 13],
                ].map(([x, y], i) => (
                  <circle key={i} cx={x} cy={y} r={2.1} fill={color} />
                ))}
              </pattern>
            );
          }
          if (patType === "dash") {
            return (
              <pattern key={pid} id={pid} patternUnits="userSpaceOnUse" width={24} height={16}>
                <rect width={24} height={16} fill={color} fillOpacity={0.26} />
                {[4, 9, 14].map((y, i) => (
                  <line key={i} x1={0} y1={y} x2={24} y2={y} stroke={color} strokeWidth={1.7} />
                ))}
              </pattern>
            );
          }
          if (patType === "brick") {
            return (
              <pattern key={pid} id={pid} patternUnits="userSpaceOnUse" width={28} height={18}>
                <rect width={28} height={18} fill={color} fillOpacity={0.26} />
                <g stroke={color} strokeWidth={1.7}>
                  <line x1={0} y1={0} x2={28} y2={0} />
                  <line x1={0} y1={9} x2={28} y2={9} />
                  <line x1={0} y1={18} x2={28} y2={18} />
                  <line x1={14} y1={0} x2={14} y2={9} />
                  <line x1={0} y1={9} x2={0} y2={18} />
                  <line x1={28} y1={9} x2={28} y2={18} />
                </g>
              </pattern>
            );
          }
          if (patType === "rhomb") {
            return (
              <pattern key={pid} id={pid} patternUnits="userSpaceOnUse" width={20} height={20}>
                <rect width={20} height={20} fill={color} fillOpacity={0.26} />
                <g stroke={color} strokeWidth={1.6}>
                  <line x1={0} y1={0} x2={20} y2={20} />
                  <line x1={0} y1={20} x2={20} y2={0} />
                  <line x1={-10} y1={10} x2={10} y2={-10} />
                  <line x1={10} y1={30} x2={30} y2={10} />
                </g>
              </pattern>
            );
          }
          if (patType === "silt") {
            return (
              <pattern key={pid} id={pid} patternUnits="userSpaceOnUse" width={26} height={26}>
                <rect width={26} height={26} fill={color} fillOpacity={0.26} />
                <g stroke={color} strokeWidth={1.8} strokeLinecap="round">
                  <line x1={3} y1={6} x2={10} y2={6} />
                  <line x1={15} y1={12} x2={22} y2={12} />
                  <line x1={6} y1={19} x2={13} y2={19} />
                  <line x1={18} y1={23} x2={25} y2={23} />
                </g>
              </pattern>
            );
          }
          return (
            <pattern key={pid} id={pid} patternUnits="userSpaceOnUse" width={32} height={32}>
              <rect width={32} height={32} fill={color} fillOpacity={0.26} />
              <g fill="none" stroke={color} strokeWidth={1.8}>
                <circle cx={9} cy={9} r={5.5} />
                <circle cx={24} cy={13} r={6.5} />
                <circle cx={15} cy={25} r={5} />
                <circle cx={30} cy={29} r={4} />
              </g>
            </pattern>
          );
        })}
      </defs>

      {/* Column blocks */}
      {LAYERS.map((L, i) => {
        const yTop = ys(L.yTopW);
        const yBot = ys(L.yBotW);
        return (
          <rect
            key={`blk-${i}`}
            x={xL}
            y={yTop}
            width={colW}
            height={yBot - yTop}
            fill={`url(#${L.patternId})`}
            stroke={t.ink}
            strokeWidth={1.4}
          />
        );
      })}

      {/* Contacts */}
      {LAYERS.map((L, i) => {
        if (L.top === minDepth) return null;
        const y = ys(L.yTopW);
        if (!L.unconf) {
          return (
            <line
              key={`c-${i}`}
              x1={xL}
              y1={y}
              x2={xR}
              y2={y}
              stroke={t.ink}
              strokeWidth={1.6}
            />
          );
        }
        const dPath = WAVY_STEPS.map((frac, k) => {
          const px = xL + colW * frac;
          const py = y + 4.5 * Math.sin(frac * 5 * 2 * Math.PI);
          return `${k === 0 ? "M" : "L"}${px.toFixed(1)} ${py.toFixed(1)}`;
        }).join(" ");
        return (
          <path
            key={`c-${i}`}
            d={dPath}
            fill="none"
            stroke={t.ink}
            strokeWidth={3}
            strokeLinecap="round"
          />
        );
      })}

      {/* Depth axis */}
      <line
        x1={axisX}
        y1={ys(COL_TOP_Y)}
        x2={axisX}
        y2={ys(COL_BOT_Y)}
        stroke={t.inkSoft}
        strokeWidth={1.6}
      />
      {DEPTH_TICKS.map((tk) => {
        const y = ys(tk.yW);
        return (
          <g key={`tk-${tk.depth}`}>
            <line x1={axisX - 8} y1={y} x2={axisX} y2={y} stroke={t.inkSoft} strokeWidth={1.6} />
            <text
              x={axisX - 13}
              y={y}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize={14}
              fill={t.inkSoft}
            >
              {tk.depth}
            </text>
          </g>
        );
      })}
      <text
        x={axisX - 13}
        y={ys(COL_TOP_Y) - 22}
        textAnchor="end"
        dominantBaseline="middle"
        fontSize={15}
        fontWeight={600}
        fill={t.ink}
      >
        {DEPTH_AXIS_TITLE}
      </text>

      {/* Geological periods */}
      {PERIODS.map((p, i) => {
        const yTop = ys(p.yTopW);
        const yBot = ys(p.yBotW);
        const yMid = (yTop + yBot) / 2;
        return (
          <g key={`p-${i}`}>
            <line x1={bx} y1={yTop + 1} x2={bx} y2={yBot - 1} stroke={t.inkSoft} strokeWidth={1.8} />
            <line x1={bx} y1={yTop + 1} x2={bx - 10} y2={yTop + 1} stroke={t.inkSoft} strokeWidth={1.8} />
            <line x1={bx} y1={yBot - 1} x2={bx - 10} y2={yBot - 1} stroke={t.inkSoft} strokeWidth={1.8} />
            <text
              x={bx - 16}
              y={yMid - 10}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize={16}
              fontWeight={600}
              fill={t.ink}
            >
              {p.name}
            </text>
            <text
              x={bx - 16}
              y={yMid + 11}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize={14}
              fill={t.inkSoft}
            >
              {p.age}
            </text>
          </g>
        );
      })}

      {/* Formation labels */}
      {LAYERS.map((L, i) => {
        const yMid = ys(L.yMidW);
        return (
          <g key={`fm-${i}`}>
            <line x1={xR} y1={yMid} x2={xLead} y2={yMid} stroke={t.grid} strokeWidth={1.2} />
            <text
              x={xText}
              y={yMid - 10}
              dominantBaseline="middle"
              fontSize={16}
              fontWeight={600}
              fill={t.ink}
            >
              {L.formation}
            </text>
            <text
              x={xText}
              y={yMid + 11}
              dominantBaseline="middle"
              fontSize={14}
              fill={t.inkSoft}
            >
              {`${L.age} · ${L.thickness}${depthUnitSuffix}`}
            </text>
          </g>
        );
      })}

      {/* Legend */}
      <text x={legX} y={ys(COL_TOP_Y + 0.55)} fontSize={18} fontWeight={700} fill={t.ink}>
        {LITHOLOGY}
      </text>
      {LITHO_NAMES.map((name, i) => {
        const y = ys(COL_TOP_Y - i * LEGEND_STEP);
        return (
          <g key={`leg-${name}`}>
            <rect
              x={legX}
              y={y - swH / 2}
              width={swW}
              height={swH}
              fill={`url(#${LITHO_IDS[name]})`}
              stroke={t.ink}
              strokeWidth={1.2}
            />
            <text x={legX + swW + 14} y={y} dominantBaseline="middle" fontSize={15} fill={t.inkSoft}>
              {name}
            </text>
          </g>
        );
      })}

      <text
        x={legX}
        y={ys(COL_TOP_Y - LITHO_NAMES.length * LEGEND_STEP - 0.15)}
        fontSize={16}
        fontWeight={700}
        fill={t.ink}
      >
        Contacts
      </text>
      <g>
        <line
          x1={legX}
          y1={ys(COL_TOP_Y - (LITHO_NAMES.length + 0.6) * LEGEND_STEP)}
          x2={legX + swW}
          y2={ys(COL_TOP_Y - (LITHO_NAMES.length + 0.6) * LEGEND_STEP)}
          stroke={t.ink}
          strokeWidth={2}
        />
        <text
          x={legX + swW + 14}
          y={ys(COL_TOP_Y - (LITHO_NAMES.length + 0.6) * LEGEND_STEP)}
          dominantBaseline="middle"
          fontSize={15}
          fill={t.inkSoft}
        >
          Conformable
        </text>
      </g>
      <g>
        <path
          d={WAVY_STEPS.map((frac, k) => {
            const px = legX + swW * frac;
            const py =
              ys(COL_TOP_Y - (LITHO_NAMES.length + 1.4) * LEGEND_STEP) +
              3.5 * Math.sin(frac * 2.5 * 2 * Math.PI);
            return `${k === 0 ? "M" : "L"}${px.toFixed(1)} ${py.toFixed(1)}`;
          }).join(" ")}
          fill="none"
          stroke={t.ink}
          strokeWidth={2.4}
        />
        <text
          x={legX + swW + 14}
          y={ys(COL_TOP_Y - (LITHO_NAMES.length + 1.4) * LEGEND_STEP)}
          dominantBaseline="middle"
          fontSize={15}
          fill={t.inkSoft}
        >
          Unconformity (hiatus)
        </text>
      </g>

      {/* Title block */}
      <text x={xs(0.55)} y={ys(8.62)} fontSize={22} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
      <text x={xs(0.55)} y={ys(8.2)} fontSize={15} fill={t.inkSoft}>
        {SUBTITLE}
      </text>
    </g>
  );
}

export default function Chart() {
  return (
    <ChartsContainer
      width={SIZE.width}
      height={SIZE.height}
      margin={{ top: 12, right: 12, bottom: 12, left: 12 }}
      series={[]}
      xAxis={[{ scaleType: "linear", min: 0, max: 16, position: "none" }]}
      yAxis={[{ scaleType: "linear", min: 0, max: 9, position: "none" }]}
      skipAnimation
    >
      <StratigraphicLayer />
    </ChartsContainer>
  );
}
