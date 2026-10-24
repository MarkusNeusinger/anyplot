// anyplot.ai
// scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-26
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-complex-plane · javascript · muix · anyplot.ai";
const DOMAIN = 2.7;
const TICKS = [-2, -1, 1, 2];

// Columns: set these to your data's column names
const LABEL = "Symbol"; // role: label
const REAL = "Real part (Re)"; // role: real
const IMAGINARY = "Imaginary part (Im)"; // role: imaginary
const CATEGORY = "Point group"; // role: group

// Data: replace this block with your own records
const data = [
  { [LABEL]: "z1", [REAL]: 1, [IMAGINARY]: 0, [CATEGORY]: "Cube roots of unity" },
  { [LABEL]: "z2", [REAL]: -0.5, [IMAGINARY]: Math.sqrt(3) / 2, [CATEGORY]: "Cube roots of unity" },
  { [LABEL]: "z3", [REAL]: -0.5, [IMAGINARY]: -Math.sqrt(3) / 2, [CATEGORY]: "Cube roots of unity" },
  { [LABEL]: "w1", [REAL]: 1.7, [IMAGINARY]: 1.0, [CATEGORY]: "Arbitrary points" },
  { [LABEL]: "w2", [REAL]: -1.4, [IMAGINARY]: 1.8, [CATEGORY]: "Arbitrary points" },
  { [LABEL]: "w3", [REAL]: 0.9, [IMAGINARY]: -1.9, [CATEGORY]: "Arbitrary points" },
];

// Plot: reads only data and the constants above
const categoryNames = Array.from(new Set(data.map((row) => String(row[CATEGORY]))));
const categories = categoryNames.map((catLabel, idx) => ({
  key: `cat-${idx}`,
  label: catLabel,
  color: t.palette[idx % t.palette.length],
  points: data
    .filter((row) => String(row[CATEGORY]) === catLabel)
    .map((row) => {
      const re = Number(row[REAL]);
      const im = Number(row[IMAGINARY]);
      const name = String(row[LABEL]);
      const sign = im < 0 ? "-" : "+";
      const rectStr = `${re.toFixed(2)}${sign}${Math.abs(im).toFixed(2)}i`;
      const r = Math.hypot(re, im);
      const theta = (Math.atan2(im, re) * 180) / Math.PI;
      const polarStr = `${r.toFixed(2)} ∠ ${theta.toFixed(0)}°`;
      const onRealAxis = Math.abs(im) < 0.08;
      const dx = onRealAxis ? 18 : re >= 0 ? 20 : -20;
      const dy = onRealAxis ? -40 : im >= 0 ? -18 : 32;
      const anchor = re >= 0 ? "start" : "end";
      return { name, re, im, rectStr, polarStr, dx, dy, anchor };
    }),
}));

function ArgandDiagram() {
  const xScale = useXScale();
  const yScale = useYScale();
  const zeroX = xScale(0);
  const zeroY = yScale(0);
  const unitRadius = Math.abs(xScale(1) - xScale(0));
  const axisStart = xScale(-DOMAIN);
  const axisEnd = xScale(DOMAIN);
  const axisTop = yScale(DOMAIN);
  const axisBottom = yScale(-DOMAIN);

  return (
    <g>
      <defs>
        {categories.map((cat) => (
          <marker
            key={cat.key}
            id={`arrowhead-${cat.key}`}
            markerWidth={10}
            markerHeight={10}
            refX={8}
            refY={5}
            orient="auto"
          >
            <path d="M0,0 L10,5 L0,10 Z" fill={cat.color} />
          </marker>
        ))}
      </defs>

      {TICKS.map((v) => (
        <line key={`grid-v-${v}`} x1={xScale(v)} y1={axisTop} x2={xScale(v)} y2={axisBottom} stroke={t.grid} strokeWidth={1} />
      ))}
      {TICKS.map((v) => (
        <line key={`grid-h-${v}`} x1={axisStart} y1={yScale(v)} x2={axisEnd} y2={yScale(v)} stroke={t.grid} strokeWidth={1} />
      ))}

      <circle
        cx={zeroX}
        cy={zeroY}
        r={unitRadius}
        fill="none"
        stroke={t.inkSoft}
        strokeWidth={2}
        strokeDasharray="9 9"
        opacity={0.8}
      />

      <line x1={axisStart} y1={zeroY} x2={axisEnd} y2={zeroY} stroke={t.ink} strokeWidth={2.5} />
      <line x1={zeroX} y1={axisTop} x2={zeroX} y2={axisBottom} stroke={t.ink} strokeWidth={2.5} />
      <text x={axisEnd - 6} y={zeroY - 16} fontSize={20} fontWeight={600} fill={t.ink} textAnchor="end">
        Re
      </text>
      <text x={zeroX + 16} y={axisTop + 26} fontSize={20} fontWeight={600} fill={t.ink} textAnchor="start">
        Im
      </text>

      {TICKS.map((v) => (
        <g key={`tick-re-${v}`}>
          <line x1={xScale(v)} y1={zeroY - 9} x2={xScale(v)} y2={zeroY + 9} stroke={t.ink} strokeWidth={1.5} />
          <text x={xScale(v)} y={zeroY + 34} fontSize={17} fill={t.inkSoft} textAnchor="middle">
            {v}
          </text>
        </g>
      ))}
      {TICKS.map((v) => (
        <g key={`tick-im-${v}`}>
          <line x1={zeroX - 9} y1={yScale(v)} x2={zeroX + 9} y2={yScale(v)} stroke={t.ink} strokeWidth={1.5} />
          <text x={zeroX - 16} y={yScale(v) + 6} fontSize={17} fill={t.inkSoft} textAnchor="end">
            {`${v}i`}
          </text>
        </g>
      ))}
      <text x={zeroX - 14} y={zeroY + 30} fontSize={17} fill={t.inkSoft} textAnchor="end">
        0
      </text>

      {categories.map((cat) =>
        cat.points.map((p) => {
          const px = xScale(p.re);
          const py = yScale(p.im);
          return (
            <g key={p.name}>
              <line
                x1={zeroX}
                y1={zeroY}
                x2={px}
                y2={py}
                stroke={cat.color}
                strokeWidth={2.5}
                markerEnd={`url(#arrowhead-${cat.key})`}
              />
              <circle cx={px} cy={py} r={12} fill={cat.color} stroke={t.pageBg} strokeWidth={3} />
              <text x={px + p.dx} y={py + p.dy} fontSize={16} fontWeight={600} fill={t.ink} textAnchor={p.anchor}>
                {`${p.name} = ${p.rectStr}`}
              </text>
              <text x={px + p.dx} y={py + p.dy + 20} fontSize={15} fill={t.inkSoft} textAnchor={p.anchor}>
                {p.polarStr}
              </text>
            </g>
          );
        })
      )}

      {categories.map((cat, i) => {
        const legendX = axisStart + 24;
        const legendY = axisTop + 28 + i * 32;
        return (
          <g key={`legend-${cat.key}`}>
            <circle cx={legendX} cy={legendY} r={9} fill={cat.color} stroke={t.pageBg} strokeWidth={2} />
            <text x={legendX + 18} y={legendY + 5} fontSize={16} fill={t.ink} textAnchor="start">
              {cat.label}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const titleHeight = 70;
  const chartSize = Math.min(size.width, size.height - titleHeight);

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Box sx={{ height: titleHeight, display: "flex", alignItems: "center" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </Typography>
      </Box>
      <ChartsContainer
        width={chartSize}
        height={chartSize}
        series={[]}
        xAxis={[{ min: -DOMAIN, max: DOMAIN, scaleType: "linear", domainLimit: "strict", position: "none" }]}
        yAxis={[{ min: -DOMAIN, max: DOMAIN, scaleType: "linear", domainLimit: "strict", position: "none" }]}
        margin={{ top: 20, bottom: 20, left: 20, right: 20 }}
        skipAnimation
      >
        <ArgandDiagram />
      </ChartsContainer>
    </Box>
  );
}
