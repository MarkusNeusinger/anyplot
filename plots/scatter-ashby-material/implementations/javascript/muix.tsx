// anyplot.ai
// scatter-ashby-material: Ashby Material Selection Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LOG_PAD_SHARE = 0.08; // axis padding on each side as a share of the log span
const HULL_MARGIN = 15; // px the family envelopes reach beyond their outermost points
const GUIDE_STEP_DECADES = 2; // decades between neighbouring constant-ratio guide lines
const MARKER_RADIUS = 6; // px
const LABEL_CHAR_WIDTH = 9.2; // px per character of a 16 px family label
const LABEL_SWATCH_SPACE = 16; // px the colour swatch takes in front of the label text
const LABEL_HEIGHT = 22; // px
const LABEL_GAP = 12; // px between an envelope and its label
const LABEL_STEP = 16; // px each further try moves the label outward
const LABEL_STEPS = 8; // tries per side before a label falls back to its first spot
const GUIDE_LABEL_CHAR_WIDTH = 7.8; // px per character of a 14 px guide label
const GUIDE_LABEL_HEIGHT = 12; // px the guide label's glyphs rise above its baseline
const GUIDE_LABEL_OFFSET = 8; // px between a guide line and its label's baseline

// Columns: set these to your data's column names
const MATERIAL = "Material"; // role: material
const FAMILY = "Material family"; // role: family
const DENSITY = "Density (kg/m³)"; // role: property_x
const MODULUS = "Young's modulus (GPa)"; // role: property_y

// Data: replace this block with your own records, one object per row
// Classic density vs. Young's modulus chart: typical handbook values per material
// as [material, density in kg/m³, Young's modulus in GPa]
const data = Object.entries({
  Metals: [
    ["Mild Steel", 7850, 210], ["Stainless Steel", 7900, 193], ["Cast Iron", 7200, 110], ["Aluminum Alloys", 2700, 70],
    ["Titanium Alloys", 4430, 114], ["Copper Alloys", 8900, 120], ["Magnesium Alloys", 1740, 45], ["Nickel Superalloys", 8200, 210],
    ["Zinc Alloys", 7100, 100], ["Lead Alloys", 11340, 16], ["Tungsten", 19300, 411], ["Molybdenum", 10200, 329],
    ["Brass", 8500, 100], ["Bronze", 8800, 110], ["Chromium", 7190, 279], ["Tool Steel", 7800, 210],
  ],
  Polymers: [
    ["HDPE", 950, 0.9], ["Polypropylene", 905, 1.5], ["PVC", 1400, 3.0], ["Nylon 6,6", 1140, 2.8], ["Polycarbonate", 1200, 2.4],
    ["Acrylic (PMMA)", 1180, 3.0], ["ABS", 1050, 2.2], ["Polystyrene", 1050, 3.2], ["PTFE", 2170, 0.5], ["Epoxy Resin", 1200, 3.0],
    ["Polyester Resin", 1300, 3.5], ["Phenolic Resin", 1350, 4.5], ["Melamine", 1500, 7.0], ["Rigid Polyurethane", 1150, 2.0], ["PEEK", 1310, 3.6],
  ],
  Ceramics: [
    ["Alumina", 3950, 370], ["Silicon Carbide", 3200, 410], ["Silicon Nitride", 3200, 310], ["Zirconia", 6000, 200], ["Boron Carbide", 2520, 450],
    ["Tungsten Carbide", 15600, 600], ["Magnesia", 3580, 300], ["Soda-Lime Glass", 2500, 72], ["Borosilicate Glass", 2230, 63], ["Concrete", 2400, 30],
    ["Fired Brick", 1900, 15], ["Natural Stone", 2600, 50], ["Fireclay", 2100, 25], ["Cement Paste", 1900, 20],
  ],
  Composites: [
    ["CFRP", 1550, 110], ["GFRP", 1900, 25], ["Kevlar Composite", 1380, 76], ["Boron Composite", 2000, 200], ["Carbon-Epoxy", 1600, 140],
    ["Glass-Epoxy", 2000, 40], ["Al-SiC MMC", 2900, 120], ["Cermet", 6200, 380], ["Plywood", 600, 9], ["Wood (Along Grain)", 600, 12],
    ["Wood (Across Grain)", 600, 0.8], ["Bamboo", 700, 17], ["Laminated Veneer", 550, 13],
  ],
  Elastomers: [
    ["Natural Rubber", 920, 0.002], ["Silicone Rubber", 1200, 0.005], ["Neoprene", 1240, 0.01], ["Butyl Rubber", 920, 0.0015],
    ["Nitrile Rubber", 1000, 0.004], ["EPDM", 860, 0.005], ["Polyurethane Elastomer", 1200, 0.03], ["Latex Rubber", 940, 0.0015],
    ["Isoprene Rubber", 910, 0.002], ["SBR", 940, 0.004], ["Fluoroelastomer", 1850, 0.006], ["Polychloroprene", 1250, 0.008],
  ],
  Foams: [
    ["Rigid Polyurethane Foam", 50, 0.01], ["Polystyrene Foam", 25, 0.004], ["Polyethylene Foam", 35, 0.002], ["Cork", 160, 0.02],
    ["Balsa Wood", 150, 3.0], ["Aluminum Foam", 270, 0.8], ["Flexible PU Foam", 30, 0.0005], ["Syntactic Foam", 550, 2.5],
    ["Melamine Foam", 10, 0.0002], ["Foamed Glass", 130, 1.0], ["Cellular Ceramic Foam", 400, 1.5], ["Phenolic Foam", 60, 0.005],
  ],
} as Record<string, [string, number, number][]>).flatMap(([family, rows]) =>
  rows.map(([material, rho, e]) => ({ [MATERIAL]: material, [FAMILY]: family, [DENSITY]: rho, [MODULUS]: e })),
);

// Plot: reads only data and the constants above
const familyNames = [...new Set(data.map((d) => d[FAMILY]))];

// Convex hull per family (monotone chain) in log-log space, where the axes are linear
const families = familyNames.map((name, i) => {
  const rows = data.filter((d) => d[FAMILY] === name);
  const sorted = rows
    .map((d) => [Math.log10(d[DENSITY]), Math.log10(d[MODULUS])])
    .sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const hull: number[][] = [];
  [sorted, [...sorted].reverse()].forEach((pass) => {
    const chain: number[][] = [];
    pass.forEach((p) => {
      while (chain.length >= 2) {
        const o = chain[chain.length - 2];
        const a = chain[chain.length - 1];
        if ((a[0] - o[0]) * (p[1] - o[1]) - (a[1] - o[1]) * (p[0] - o[0]) > 0) break;
        chain.pop();
      }
      chain.push(p);
    });
    chain.pop();
    hull.push(...chain);
  });
  // Fewer than three distinct points have no area; their points stand in for the envelope
  return { name, color: t.palette[i], rows, outline: hull.length >= 3 ? hull : sorted };
});

// The envelopes in px, each hull pushed HULL_MARGIN beyond its points, as FamilyRegions draws them
function useEnvelopes() {
  const xScale = useXScale();
  const yScale = useYScale();
  return families.map((family) => {
    const px = family.outline.map(([lx, ly]) => [xScale(10 ** lx), yScale(10 ** ly)]);
    const cx = px.reduce((s, p) => s + p[0], 0) / px.length;
    const cy = px.reduce((s, p) => s + p[1], 0) / px.length;
    return px.map(([x, y]) => {
      const len = Math.hypot(x - cx, y - cy) || 1;
      return [x + ((x - cx) / len) * HULL_MARGIN, y + ((y - cy) / len) * HULL_MARGIN];
    });
  });
}

// Ray casting
const insidePolygon = (poly: number[][], x: number, y: number) =>
  poly.reduce((inside, [ax, ay], i) => {
    const [bx, by] = poly[(i + 1) % poly.length];
    return ay > y !== by > y && x < ((bx - ax) * (y - ay)) / (by - ay) + ax ? !inside : inside;
  }, false);

const distanceToPolygon = (poly: number[][], x: number, y: number) =>
  Math.min(
    ...poly.map(([ax, ay], i) => {
      const [bx, by] = poly[(i + 1) % poly.length];
      const len2 = (bx - ax) ** 2 + (by - ay) ** 2 || 1;
      const s = Math.max(0, Math.min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / len2));
      return Math.hypot(x - ax - s * (bx - ax), y - ay - s * (by - ay));
    }),
  );

const logX = data.map((d) => Math.log10(d[DENSITY]));
const logY = data.map((d) => Math.log10(d[MODULUS]));
const padX = (Math.max(...logX) - Math.min(...logX)) * LOG_PAD_SHARE;
const padY = (Math.max(...logY) - Math.min(...logY)) * LOG_PAD_SHARE;
const xMin = 10 ** (Math.min(...logX) - padX);
const xMax = 10 ** (Math.max(...logX) + padX);
const yMin = 10 ** (Math.min(...logY) - padY);
const yMax = 10 ** (Math.max(...logY) + padY);
const xDecades = Array.from(
  { length: Math.floor(Math.log10(xMax)) - Math.ceil(Math.log10(xMin)) + 1 },
  (_, i) => 10 ** (Math.ceil(Math.log10(xMin)) + i),
);
const yDecades = Array.from(
  { length: Math.floor(Math.log10(yMax)) - Math.ceil(Math.log10(yMin)) + 1 },
  (_, i) => 10 ** (Math.ceil(Math.log10(yMin)) + i),
);

// Constant-ratio guides (y / x = 10^k) every few decades across the data's ratio range,
// clipped to the axis box; straight and parallel on log-log axes
const ratios = data.map((d) => d[MODULUS] / d[DENSITY]);
const kLow = Math.ceil(Math.log10(Math.min(...ratios)));
const kHigh = Math.floor(Math.log10(Math.max(...ratios)));
const guides = Array.from({ length: Math.floor((kHigh - kLow) / GUIDE_STEP_DECADES) + 1 }, (_, i) => {
  const k = kLow + i * GUIDE_STEP_DECADES;
  const x0 = Math.max(xMin, yMin / 10 ** k);
  const x1 = Math.min(xMax, yMax / 10 ** k);
  return { k, x0, x1, y0: 10 ** k * x0, y1: 10 ** k * x1 };
}).filter((g) => g.x0 < g.x1);
const unitX = DENSITY.match(/\(([^)]+)\)/)?.[1] ?? "";
const unitY = MODULUS.match(/\(([^)]+)\)/)?.[1] ?? "";

const TITLE = "scatter-ashby-material · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} materials in ${familyNames.length} families · dashed lines hold the ratio ${MODULUS} / ${DENSITY} constant`;
const HEADER_HEIGHT = 84;

function FamilyRegions() {
  const envelopes = useEnvelopes();
  return (
    <g>
      {families.map((family, f) => (
        <path
          key={`region-${family.name}`}
          d={`M ${envelopes[f].map((p) => p.join(",")).join(" L ")} Z`}
          fill={family.color}
          fillOpacity={0.1}
          stroke={family.color}
          strokeOpacity={0.75}
          strokeWidth={1.5}
          strokeLinejoin="round"
        />
      ))}
    </g>
  );
}

function GuideLines() {
  const xScale = useXScale();
  const yScale = useYScale();
  const area = useDrawingArea();
  const envelopes = useEnvelopes();
  return (
    <g>
      {guides.map((g) => {
        const ax = xScale(g.x0);
        const ay = yScale(g.y0);
        const bx = xScale(g.x1);
        const by = yScale(g.y1);
        const rad = Math.atan2(by - ay, bx - ax);
        const [ux, uy] = [Math.cos(rad), Math.sin(rad)];
        const [nx, ny] = [uy, -ux]; // normal pointing above the line
        const w = (`10${g.k} ${unitY}/(${unitX})`.length * GUIDE_LABEL_CHAR_WIDTH) / 2;
        // The label slides along its line to the spot that keeps it furthest from every envelope
        // (negative inside one) and inside the plot
        const spots = Array.from({ length: 33 }, (_, i) => 0.1 + i * 0.025).map((share) => {
          const cx = ax + (bx - ax) * share + nx * GUIDE_LABEL_OFFSET;
          const cy = ay + (by - ay) * share + ny * GUIDE_LABEL_OFFSET;
          const samples = [-1, -0.5, 0, 0.5, 1].flatMap((s) =>
            [0, GUIDE_LABEL_HEIGHT].map((h) => [cx + ux * s * w + nx * h, cy + uy * s * w + ny * h]),
          );
          const clearance = Math.min(
            ...samples.map(([sx, sy]) => {
              if (sx < area.left || sx > area.left + area.width || sy < area.top || sy > area.top + area.height) return -Infinity;
              return Math.min(...envelopes.map((poly) => (insidePolygon(poly, sx, sy) ? -1 : 1) * distanceToPolygon(poly, sx, sy)));
            }),
          );
          return { cx, cy, clearance };
        });
        const spot = spots.reduce((best, s) => (s.clearance > best.clearance ? s : best));
        return (
          <g key={`guide-${g.k}`}>
            <line x1={ax} y1={ay} x2={bx} y2={by} stroke={t.inkSoft} strokeWidth={1.25} strokeDasharray="7 6" strokeOpacity={0.6} />
            <text
              transform={`translate(${spot.cx}, ${spot.cy}) rotate(${(rad * 180) / Math.PI})`}
              textAnchor="middle"
              fontSize={14}
              fill={t.inkSoft}
              stroke={t.pageBg}
              strokeWidth={4}
              paintOrder="stroke"
            >
              10<tspan dy={-6}>{g.k}</tspan>
              <tspan dy={6}>{` ${unitY}/(${unitX})`}</tspan>
            </text>
          </g>
        );
      })}
    </g>
  );
}

function FamilyLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  const area = useDrawingArea();
  const hulls = useEnvelopes();
  const markers = data.map((d) => [xScale(d[DENSITY]), yScale(d[MODULUS])]);
  // Each label tries above, below, right of and left of its envelope, stepping further out, and takes
  // the first spot inside the plot that touches no marker, no other label and no other envelope, and
  // that lies nearer its own envelope than any other
  const placed: { x: number; y: number; w: number }[] = [];
  families.forEach((family, f) => {
    const w = family.name.length * LABEL_CHAR_WIDTH + LABEL_SWATCH_SPACE;
    const xs = hulls[f].map((p) => p[0]);
    const ys = hulls[f].map((p) => p[1]);
    const midX = (Math.min(...xs) + Math.max(...xs)) / 2;
    const midY = (Math.min(...ys) + Math.max(...ys)) / 2;
    const candidates = Array.from({ length: LABEL_STEPS }, (_, s) => LABEL_GAP + s * LABEL_STEP).flatMap((gap) => [
      { x: midX, y: Math.min(...ys) - gap - LABEL_HEIGHT / 2 },
      { x: midX, y: Math.max(...ys) + gap + LABEL_HEIGHT / 2 },
      { x: Math.max(...xs) + gap + w / 2, y: midY },
      { x: Math.min(...xs) - gap - w / 2, y: midY },
    ]);
    const free = candidates.find(({ x, y }) => {
      const x0 = x - w / 2;
      const x1 = x + w / 2;
      const y0 = y - LABEL_HEIGHT / 2;
      const y1 = y + LABEL_HEIGHT / 2;
      if (x0 < area.left || x1 > area.left + area.width || y0 < area.top || y1 > area.top + area.height) return false;
      if (markers.some(([mx, my]) => mx > x0 - MARKER_RADIUS && mx < x1 + MARKER_RADIUS && my > y0 - MARKER_RADIUS && my < y1 + MARKER_RADIUS)) return false;
      if (placed.some((p) => x0 < p.x + p.w / 2 && p.x - p.w / 2 < x1 && Math.abs(p.y - y) < LABEL_HEIGHT)) return false;
      const samples = [x0, x, x1].flatMap((sx) => [y0, y, y1].map((sy) => [sx, sy]));
      // A sample inside another family's envelope rules the spot out
      if (hulls.some((hull, g) => g !== f && samples.some(([sx, sy]) => insidePolygon(hull, sx, sy)))) return false;
      const distances = hulls.map((hull) => distanceToPolygon(hull, x, y));
      return distances.every((d, g) => g === f || d > distances[f]);
    });
    placed.push({ ...(free ?? candidates[0]), w });
  });
  return (
    <g>
      {families.map((family, f) => {
        const { x, y, w } = placed[f];
        // A swatch in the region's colour ties the label to its envelope; the text stays in ink
        const left = x - w / 2;
        return (
          <g key={`label-${family.name}`}>
            <circle cx={left + 5} cy={y} r={6} fill={family.color} stroke={t.pageBg} strokeWidth={2} />
            <text
              x={left + LABEL_SWATCH_SPACE}
              y={y}
              dominantBaseline="central"
              fontSize={16}
              fontWeight={600}
              fill={t.ink}
              stroke={t.pageBg}
              strokeWidth={4}
              paintOrder="stroke"
            >
              {family.name}
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
      <ChartsDataProvider
        width={width}
        height={height - HEADER_HEIGHT}
        margin={{ top: 12, right: 48, bottom: 16, left: 24 }}
        skipAnimation
        series={families.map((family) => ({
          type: "scatter" as const,
          id: family.name,
          label: family.name,
          color: family.color,
          markerSize: MARKER_RADIUS,
          data: family.rows.map((d, j) => ({ id: `${family.name}-${j}`, x: d[DENSITY], y: d[MODULUS], material: d[MATERIAL] })),
          valueFormatter: (p: any) => `${p.material}: ${p.x} ${unitX}, ${p.y} ${unitY}`,
        }))}
        xAxis={[
          {
            id: "density",
            scaleType: "log",
            min: xMin,
            max: xMax,
            tickInterval: xDecades,
            label: DENSITY,
            height: 72,
            valueFormatter: (v: number) => (v >= 1 ? v.toLocaleString("en-US") : `${Number(v.toPrecision(1))}`),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "modulus",
            scaleType: "log",
            min: yMin,
            max: yMax,
            tickInterval: yDecades,
            label: MODULUS,
            width: 84,
            valueFormatter: (v: number) => (v >= 1 ? v.toLocaleString("en-US") : `${Number(v.toPrecision(1))}`),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsSurface
          sx={{
            "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
            "& .MuiChartsAxis-line": { stroke: t.inkSoft },
            "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          }}
        >
          <ChartsGrid vertical horizontal />
          <FamilyRegions />
          <GuideLines />
          <ScatterPlot />
          <FamilyLabels />
          <ChartsXAxis axisId="density" />
          <ChartsYAxis axisId="modulus" />
        </ChartsSurface>
        <ChartsTooltip trigger="item" />
      </ChartsDataProvider>
    </div>
  );
}
