// anyplot.ai
// scatter-ashby-material: Ashby Material Selection Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-08-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-ashby-material · javascript · muix · anyplot.ai";
const SUBTITLE = "Density vs. Young's modulus · dashed lines mark constant specific stiffness E/ρ";
const HULL_MARGIN = 15;
const GUIDE_INDICES = [1, 100];
const MARGIN = { top: 130, right: 105, bottom: 32, left: 24 };

// Columns: set these to your data's column names
const MATERIAL = "Material"; // role: material
const FAMILY = "Material family"; // role: family
const PROPERTY_X = "Density (kg/m³)"; // role: property_x
const PROPERTY_Y = "Young's Modulus (GPa)"; // role: property_y

// Data: replace this block with your own records
const FAMILIES = [
  {
    name: "Metals",
    rho: [1800, 11400],
    e: [40, 410],
    materials: [
      "Mild Steel", "Stainless Steel", "Cast Iron", "Aluminum Alloys",
      "Titanium Alloys", "Copper Alloys", "Magnesium Alloys", "Nickel Superalloys",
      "Zinc Alloys", "Lead Alloys", "Tungsten", "Molybdenum",
      "Brass", "Bronze", "Chromium", "Tool Steel",
    ],
  },
  {
    name: "Polymers",
    rho: [900, 1500],
    e: [0.5, 4.5],
    materials: [
      "HDPE", "Polypropylene", "PVC", "Nylon 6,6",
      "Polycarbonate", "Acrylic (PMMA)", "ABS", "Polystyrene",
      "PTFE", "Epoxy Resin", "Polyester Resin", "Phenolic Resin",
      "Melamine", "Rigid Polyurethane", "PEEK",
    ],
  },
  {
    name: "Ceramics",
    rho: [2000, 4200],
    e: [10, 450],
    materials: [
      "Alumina", "Silicon Carbide", "Silicon Nitride", "Zirconia",
      "Boron Carbide", "Tungsten Carbide", "Magnesia", "Soda-Lime Glass",
      "Borosilicate Glass", "Concrete", "Fired Brick", "Natural Stone",
      "Fireclay", "Cement Paste",
    ],
  },
  {
    name: "Composites",
    rho: [500, 1900],
    e: [5, 200],
    materials: [
      "CFRP", "GFRP", "Kevlar Composite", "Boron Composite",
      "Carbon-Epoxy", "Glass-Epoxy", "Al-SiC MMC", "Cermet",
      "Plywood", "Wood (Along Grain)", "Wood (Across Grain)", "Bamboo",
      "Laminated Veneer",
    ],
  },
  {
    name: "Elastomers",
    rho: [900, 1300],
    e: [0.001, 0.1],
    materials: [
      "Natural Rubber", "Silicone Rubber", "Neoprene", "Butyl Rubber",
      "Nitrile Rubber", "EPDM", "Polyurethane Elastomer", "Latex Rubber",
      "Isoprene Rubber", "SBR", "Fluoroelastomer", "Polychloroprene",
    ],
  },
  {
    name: "Foams",
    rho: [20, 300],
    e: [0.001, 0.5],
    materials: [
      "Rigid Polyurethane Foam", "Polystyrene Foam", "Polyethylene Foam", "Cork",
      "Balsa Wood", "Aluminum Foam", "Flexible PU Foam", "Syntactic Foam",
      "Melamine Foam", "Foamed Glass", "Cellular Ceramic Foam", "Phenolic Foam",
    ],
  },
];

const MATERIAL_OVERRIDES = {
  Tungsten: { rho: [18900, 19600], e: [385, 411] },
  "Tungsten Carbide": { rho: [15400, 15800], e: [530, 650] },
  PTFE: { rho: [2150, 2200], e: [0.4, 0.75] },
};

let seed = 42;
const data = [];
for (const family of FAMILIES) {
  for (const material of family.materials) {
    const range = MATERIAL_OVERRIDES[material] ?? { rho: family.rho, e: family.e };
    seed = (1664525 * seed + 1013904223) >>> 0;
    const uRho = seed / 4294967296;
    seed = (1664525 * seed + 1013904223) >>> 0;
    const uE = seed / 4294967296;
    const logRho = Math.log10(range.rho[0]) + uRho * (Math.log10(range.rho[1]) - Math.log10(range.rho[0]));
    const logE = Math.log10(range.e[0]) + uE * (Math.log10(range.e[1]) - Math.log10(range.e[0]));
    data.push({
      [MATERIAL]: material,
      [FAMILY]: family.name,
      [PROPERTY_X]: 10 ** logRho,
      [PROPERTY_Y]: 10 ** logE,
    });
  }
}

// Plot: reads only data and the constants above
const familyNames = Array.from(new Set(data.map((row) => String(row[FAMILY]))));
const familyPoints = familyNames.map((name) => ({
  name,
  points: data
    .filter((row) => String(row[FAMILY]) === name)
    .map((row) => ({
      material: String(row[MATERIAL]),
      rho: Number(row[PROPERTY_X]),
      e: Number(row[PROPERTY_Y]),
    })),
}));

const allRho = familyPoints.flatMap((f) => f.points.map((p) => p.rho));
const allE = familyPoints.flatMap((f) => f.points.map((p) => p.e));
const xMin = Math.min(...allRho) / 1.7;
const xMax = Math.max(...allRho) * 1.7;
const yMin = Math.min(...allE) / 2.4;
const yMax = Math.max(...allE) * 3.2;

const xTickStart = Math.floor(Math.log10(xMin));
const xTickEnd = Math.ceil(Math.log10(xMax));
const xDecadeTicks = Array.from({ length: xTickEnd - xTickStart + 1 }, (_, i) => 10 ** (xTickStart + i));

const yTickStart = Math.floor(Math.log10(yMin));
const yTickEnd = Math.ceil(Math.log10(yMax));
const yDecadeTicks = Array.from({ length: yTickEnd - yTickStart + 1 }, (_, i) => 10 ** (yTickStart + i));

function AshbyOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();
  const xDomain = xScale.domain();
  const yDomain = yScale.domain();

  return (
    <g>
      {familyPoints.map((family, i) => {
        const pixels = family.points.map((p) => [xScale(p.rho), yScale(p.e)]);
        const sorted = [...pixels].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
        const lower = [];
        for (const p of sorted) {
          while (
            lower.length >= 2 &&
            (lower[lower.length - 1][0] - lower[lower.length - 2][0]) * (p[1] - lower[lower.length - 2][1]) -
              (lower[lower.length - 1][1] - lower[lower.length - 2][1]) * (p[0] - lower[lower.length - 2][0]) <=
              0
          ) {
            lower.pop();
          }
          lower.push(p);
        }
        const upper = [];
        for (let k = sorted.length - 1; k >= 0; k -= 1) {
          const p = sorted[k];
          while (
            upper.length >= 2 &&
            (upper[upper.length - 1][0] - upper[upper.length - 2][0]) * (p[1] - upper[upper.length - 2][1]) -
              (upper[upper.length - 1][1] - upper[upper.length - 2][1]) * (p[0] - upper[upper.length - 2][0]) <=
              0
          ) {
            upper.pop();
          }
          upper.push(p);
        }
        upper.pop();
        lower.pop();
        const hull = lower.concat(upper);
        const cx = hull.reduce((s, p) => s + p[0], 0) / hull.length;
        const cy = hull.reduce((s, p) => s + p[1], 0) / hull.length;
        const inflated = hull.map(([x, y]) => {
          const dx = x - cx;
          const dy = y - cy;
          const len = Math.hypot(dx, dy);
          return [x + (dx / len) * HULL_MARGIN, y + (dy / len) * HULL_MARGIN];
        });
        const d = `M ${inflated.map((p) => p.join(",")).join(" L ")} Z`;
        const labelY = Math.min(...inflated.map((p) => p[1])) - 8;
        const color = t.palette[i % t.palette.length];
        return (
          <g key={family.name}>
            <path
              d={d}
              fill={color}
              fillOpacity={0.07}
              stroke={color}
              strokeOpacity={0.6}
              strokeWidth={1.5}
              strokeLinejoin="round"
            />
            <text
              x={cx}
              y={labelY}
              textAnchor="middle"
              fontSize={15}
              fontWeight={600}
              fill={color}
              stroke={t.pageBg}
              strokeWidth={4}
              paintOrder="stroke"
            >
              {family.name}
            </text>
          </g>
        );
      })}

      {GUIDE_INDICES.map((index) => {
        const k = index / 1000;
        let x0 = xDomain[0];
        let x1 = xDomain[1];
        let y0 = k * x0;
        let y1 = k * x1;
        if (y0 < yDomain[0]) {
          x0 = yDomain[0] / k;
          y0 = yDomain[0];
        }
        if (y0 > yDomain[1]) {
          x0 = yDomain[1] / k;
          y0 = yDomain[1];
        }
        if (y1 < yDomain[0]) {
          x1 = yDomain[0] / k;
          y1 = yDomain[0];
        }
        if (y1 > yDomain[1]) {
          x1 = yDomain[1] / k;
          y1 = yDomain[1];
        }
        if (x0 >= x1) return null;
        const px0 = xScale(x0);
        const py0 = yScale(y0);
        const px1 = xScale(x1);
        const py1 = yScale(y1);
        const angle = (Math.atan2(py1 - py0, px1 - px0) * 180) / Math.PI;
        const midX = (px0 + px1) / 2;
        const midY = (py0 + py1) / 2;
        return (
          <g key={index}>
            <line
              x1={px0}
              y1={py0}
              x2={px1}
              y2={py1}
              stroke={t.inkSoft}
              strokeWidth={1.5}
              strokeDasharray="7 6"
              opacity={0.55}
            />
            <text
              x={midX}
              y={midY - 8}
              textAnchor="middle"
              transform={`rotate(${angle}, ${midX}, ${midY - 8})`}
              fontSize={12}
              fill={t.inkSoft}
              stroke={t.pageBg}
              strokeWidth={4}
              paintOrder="stroke"
            >
              {`E/ρ = ${index}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <ChartsContainer
      width={width}
      height={height}
      margin={MARGIN}
      skipAnimation
      sx={{ "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 } }}
      series={familyPoints.map((family, i) => ({
        type: "scatter",
        id: family.name,
        label: family.name,
        color: t.palette[i % t.palette.length],
        markerSize: 6,
        data: family.points.map((p, j) => ({ x: p.rho, y: p.e, id: `${family.name}-${j}` })),
      }))}
      xAxis={[
        {
          id: "density",
          scaleType: "log",
          min: xMin,
          max: xMax,
          height: 64,
          disableTicks: true,
          tickInterval: xDecadeTicks,
          label: PROPERTY_X,
          labelStyle: { fontSize: 16, fill: t.ink },
          tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
          valueFormatter: (v) =>
            v >= 100
              ? Math.round(v).toLocaleString()
              : v >= 1
                ? Number(v.toPrecision(2)).toString()
                : Number(v.toPrecision(1)).toString(),
        },
      ]}
      yAxis={[
        {
          id: "modulus",
          scaleType: "log",
          min: yMin,
          max: yMax,
          width: 96,
          disableTicks: true,
          tickInterval: yDecadeTicks,
          label: PROPERTY_Y,
          labelStyle: { fontSize: 16, fill: t.ink },
          tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
          valueFormatter: (v) =>
            v >= 100
              ? Math.round(v).toLocaleString()
              : v >= 1
                ? Number(v.toPrecision(2)).toString()
                : Number(v.toPrecision(1)).toString(),
        },
      ]}
    >
      <ChartsGrid vertical horizontal />
      <AshbyOverlay />
      <ScatterPlot />
      <ChartsXAxis axisId="density" />
      <ChartsYAxis axisId="modulus" />
      <ChartsTooltip trigger="item" />
      <text x={width / 2} y={46} textAnchor="middle" fontSize={26} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
      <text x={width / 2} y={78} textAnchor="middle" fontSize={15} fill={t.inkSoft}>
        {SUBTITLE}
      </text>
    </ChartsContainer>
  );
}
