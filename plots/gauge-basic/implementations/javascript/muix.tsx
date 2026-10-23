//# anyplot-orientation: square
// anyplot.ai
// gauge-basic: Basic Gauge Chart
// Library: muix 7.29.1 | JavaScript 22.23.0
// Quality: 90/100 | Created: 2026-06-30

import {
  GaugeContainer,
  useGaugeState,
} from "@mui/x-charts/Gauge";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const VALUE = "value"; // role: value
const MIN_VALUE = "min_value"; // role: min_value
const MAX_VALUE = "max_value"; // role: max_value
const LOW_THRESHOLD = "Low threshold"; // role: thresholds
const HIGH_THRESHOLD = "High threshold"; // role: thresholds

// Data: replace this block with your own records, one object per row
// Customer satisfaction score on a 0–100 scale with zone thresholds at 30 and 70.
const data = [
  { [VALUE]: 72, [MIN_VALUE]: 0, [MAX_VALUE]: 100, [LOW_THRESHOLD]: 30, [HIGH_THRESHOLD]: 70 },
];

// Plot: reads only data and the constants above
const record = data[0];
const score = record[VALUE];
const VALUE_MIN = record[MIN_VALUE];
const VALUE_MAX = record[MAX_VALUE];
const lowThreshold = record[LOW_THRESHOLD];
const highThreshold = record[HIGH_THRESHOLD];

// Imprint semantic colors: red=poor, amber=fair, green=good
const COLOR_POOR = t.palette[4];
const COLOR_FAIR = t.amber;
const COLOR_GOOD = t.palette[0];

const scoreColor =
  score < lowThreshold
    ? COLOR_POOR
    : score < highThreshold
    ? COLOR_FAIR
    : COLOR_GOOD;

// Gauge arc geometry (degrees — MUI X convention)
const START_DEG = -120;
const END_DEG = 120;
const START_RAD = (START_DEG * Math.PI) / 180;
const TOTAL_RAD = ((END_DEG - START_DEG) * Math.PI) / 180;

// SVG annular sector path (angles in radians, MUI X convention: 0=top, CW)
function sectorPath(
  cx: number,
  cy: number,
  innerR: number,
  outerR: number,
  s: number,
  e: number,
) {
  const la = e - s > Math.PI ? 1 : 0;
  const x1 = cx + outerR * Math.sin(s);
  const y1 = cy - outerR * Math.cos(s);
  const x2 = cx + outerR * Math.sin(e);
  const y2 = cy - outerR * Math.cos(e);
  const x3 = cx + innerR * Math.sin(e);
  const y3 = cy - innerR * Math.cos(e);
  const x4 = cx + innerR * Math.sin(s);
  const y4 = cy - innerR * Math.cos(s);
  return `M${x1},${y1} A${outerR},${outerR} 0 ${la},1 ${x2},${y2} L${x3},${y3} A${innerR},${innerR} 0 ${la},0 ${x4},${y4} Z`;
}

// Zone arcs and scale labels drawn inside GaugeContainer
function ZoneArcs() {
  const { cx, cy, outerRadius, innerRadius } = useGaugeState();
  const range = VALUE_MAX - VALUE_MIN || 1;
  const lowFrac = (lowThreshold - VALUE_MIN) / range;
  const highFrac = (highThreshold - VALUE_MIN) / range;
  const gapRad = TOTAL_RAD * 0.007;

  const z1S = START_RAD;
  const z1E = START_RAD + TOTAL_RAD * lowFrac - gapRad;
  const z2S = START_RAD + TOTAL_RAD * lowFrac + gapRad;
  const z2E = START_RAD + TOTAL_RAD * highFrac - gapRad;
  const z3S = START_RAD + TOTAL_RAD * highFrac + gapRad;
  const z3E = START_RAD + TOTAL_RAD;

  const ticks = [VALUE_MIN, lowThreshold, highThreshold, VALUE_MAX];
  const labelR = outerRadius + 24;

  return (
    <g>
      <path d={sectorPath(cx, cy, innerRadius, outerRadius, z1S, z1E)} fill={COLOR_POOR} />
      <path d={sectorPath(cx, cy, innerRadius, outerRadius, z2S, z2E)} fill={COLOR_FAIR} />
      <path d={sectorPath(cx, cy, innerRadius, outerRadius, z3S, z3E)} fill={COLOR_GOOD} />
      {ticks.map((tickVal) => {
        const frac = (tickVal - VALUE_MIN) / range;
        const angle = START_RAD + TOTAL_RAD * frac;
        const lx = cx + labelR * Math.sin(angle);
        const ly = cy - labelR * Math.cos(angle);
        return (
          <text
            key={tickVal}
            x={lx}
            y={ly}
            textAnchor="middle"
            dominantBaseline="central"
            style={{
              fontSize: 16,
              fontWeight: 500,
              fill: t.inkSoft,
              fontFamily: "Roboto, sans-serif",
            }}
          >
            {tickVal}
          </text>
        );
      })}
    </g>
  );
}

// Custom needle + score label rendered inside the gauge SVG
function NeedleAndLabel() {
  const { cx, cy, outerRadius, innerRadius, value } = useGaugeState();
  const currentVal = value ?? score;
  const frac = (currentVal - VALUE_MIN) / (VALUE_MAX - VALUE_MIN || 1);
  const angleRad = START_RAD + TOTAL_RAD * frac;
  const needleLen = outerRadius * 0.82;
  const tipX = cx + needleLen * Math.sin(angleRad);
  const tipY = cy - needleLen * Math.cos(angleRad);
  const perp = angleRad + Math.PI / 2;
  const baseW = Math.max(4, outerRadius * 0.025);
  const baseR = innerRadius * 0.35;
  const b1x = cx + baseR * Math.sin(angleRad) + baseW * Math.sin(perp);
  const b1y = cy - baseR * Math.cos(angleRad) - baseW * Math.cos(perp);
  const b2x = cx + baseR * Math.sin(angleRad) - baseW * Math.sin(perp);
  const b2y = cy - baseR * Math.cos(angleRad) + baseW * Math.cos(perp);

  return (
    <g>
      <polygon
        points={`${tipX},${tipY} ${b1x},${b1y} ${b2x},${b2y}`}
        fill={t.ink}
        opacity={0.88}
      />
      <circle cx={cx} cy={cy} r={outerRadius * 0.055} fill={t.ink} opacity={0.88} />
      <text
        x={cx}
        y={cy + outerRadius * 0.24}
        textAnchor="middle"
        dominantBaseline="middle"
        style={{
          fontSize: outerRadius * 0.38,
          fontWeight: 700,
          fill: scoreColor,
          fontFamily: "Roboto, sans-serif",
        }}
      >
        {currentVal}
      </text>
      <text
        x={cx}
        y={cy + outerRadius * 0.50}
        textAnchor="middle"
        dominantBaseline="middle"
        style={{
          fontSize: outerRadius * 0.13,
          fill: t.inkSoft,
          fontFamily: "Roboto, sans-serif",
        }}
      >
        out of {VALUE_MAX}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const gaugeW = width * 0.8;
  const gaugeH = height * 0.62;

  const titleFontSize = Math.round(22 * (67 / 80));

  const zones = [
    { label: "Needs Work", range: `${VALUE_MIN}–${lowThreshold}`, color: COLOR_POOR },
    { label: "Developing", range: `${lowThreshold}–${highThreshold}`, color: COLOR_FAIR },
    { label: "Excellent", range: `${highThreshold}–${VALUE_MAX}`, color: COLOR_GOOD },
  ];

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Typography
        sx={{
          color: t.ink,
          fontSize: titleFontSize,
          fontWeight: 600,
          letterSpacing: "0.01em",
          mb: 1,
          textAlign: "center",
          px: 2,
        }}
      >
        Customer Satisfaction Score · gauge-basic · javascript · muix · anyplot.ai
      </Typography>

      <GaugeContainer
        width={gaugeW}
        height={gaugeH}
        value={score}
        valueMin={VALUE_MIN}
        valueMax={VALUE_MAX}
        startAngle={START_DEG}
        endAngle={END_DEG}
        innerRadius="58%"
        outerRadius="86%"
        skipAnimation
      >
        <ZoneArcs />
        <NeedleAndLabel />
      </GaugeContainer>

      <Box sx={{ display: "flex", gap: 4, mt: 1 }}>
        {zones.map(({ label, range, color }) => (
          <Box key={label} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box
              sx={{
                width: 14,
                height: 14,
                borderRadius: "3px",
                bgcolor: color,
                flexShrink: 0,
              }}
            />
            <Typography sx={{ color: t.inkSoft, fontSize: 15 }}>
              {label} ({range})
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
