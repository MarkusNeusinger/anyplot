// anyplot.ai
// scatter-ashby-material: Ashby Material Selection Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-24

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

// Columns: set these to your data's column names
const MATERIAL = "Material"; // role: material
const FAMILY = "Material family"; // role: family
const DENSITY = "Density (kg/m³)"; // role: property_x
const MODULUS = "Young's modulus (GPa)"; // role: property_y

// Data: replace this block with your own records, one object per row
// Classic density vs. Young's modulus chart: each family's materials are sampled
// log-uniformly inside the family's archetypal property box; a few well-known
// outliers get a tight box around their published values.
const data = (() => {
  let seed = 42;
  const rng = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const families = [
    { name: "Metals", rho: [1800, 11400], e: [40, 410], materials: ["Mild Steel", "Stainless Steel", "Cast Iron", "Aluminum Alloys", "Titanium Alloys", "Copper Alloys", "Magnesium Alloys", "Nickel Superalloys", "Zinc Alloys", "Lead Alloys", "Tungsten", "Molybdenum", "Brass", "Bronze", "Chromium", "Tool Steel"] },
    { name: "Polymers", rho: [900, 1500], e: [0.5, 4.5], materials: ["HDPE", "Polypropylene", "PVC", "Nylon 6,6", "Polycarbonate", "Acrylic (PMMA)", "ABS", "Polystyrene", "PTFE", "Epoxy Resin", "Polyester Resin", "Phenolic Resin", "Melamine", "Rigid Polyurethane", "PEEK"] },
    { name: "Ceramics", rho: [2000, 4200], e: [10, 450], materials: ["Alumina", "Silicon Carbide", "Silicon Nitride", "Zirconia", "Boron Carbide", "Tungsten Carbide", "Magnesia", "Soda-Lime Glass", "Borosilicate Glass", "Concrete", "Fired Brick", "Natural Stone", "Fireclay", "Cement Paste"] },
    { name: "Composites", rho: [500, 1900], e: [5, 200], materials: ["CFRP", "GFRP", "Kevlar Composite", "Boron Composite", "Carbon-Epoxy", "Glass-Epoxy", "Al-SiC MMC", "Cermet", "Plywood", "Wood (Along Grain)", "Wood (Across Grain)", "Bamboo", "Laminated Veneer"] },
    { name: "Elastomers", rho: [900, 1300], e: [0.001, 0.1], materials: ["Natural Rubber", "Silicone Rubber", "Neoprene", "Butyl Rubber", "Nitrile Rubber", "EPDM", "Polyurethane Elastomer", "Latex Rubber", "Isoprene Rubber", "SBR", "Fluoroelastomer", "Polychloroprene"] },
    { name: "Foams", rho: [20, 300], e: [0.001, 0.5], materials: ["Rigid Polyurethane Foam", "Polystyrene Foam", "Polyethylene Foam", "Cork", "Balsa Wood", "Aluminum Foam", "Flexible PU Foam", "Syntactic Foam", "Melamine Foam", "Foamed Glass", "Cellular Ceramic Foam", "Phenolic Foam"] },
  ];
  const overrides = {
    Tungsten: { rho: [18900, 19600], e: [385, 411] },
    "Tungsten Carbide": { rho: [15400, 15800], e: [530, 650] },
    PTFE: { rho: [2150, 2200], e: [0.4, 0.75] },
  };
  return families.flatMap((family) =>
    family.materials.map((material) => {
      const box = overrides[material] ?? family;
      const logRho = Math.log10(box.rho[0]) + rng() * Math.log10(box.rho[1] / box.rho[0]);
      const logE = Math.log10(box.e[0]) + rng() * Math.log10(box.e[1] / box.e[0]);
      return {
        [MATERIAL]: material,
        [FAMILY]: family.name,
        [DENSITY]: Math.round(10 ** logRho),
        [MODULUS]: Number((10 ** logE).toPrecision(3)),
      };
    }),
  );
})();

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
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {families.map((family) => {
        const px = family.outline.map(([lx, ly]) => [xScale(10 ** lx), yScale(10 ** ly)]);
        const cx = px.reduce((s, p) => s + p[0], 0) / px.length;
        const cy = px.reduce((s, p) => s + p[1], 0) / px.length;
        const inflated = px.map(([x, y]) => {
          const len = Math.hypot(x - cx, y - cy) || 1;
          return [x + ((x - cx) / len) * HULL_MARGIN, y + ((y - cy) / len) * HULL_MARGIN];
        });
        return (
          <path
            key={`region-${family.name}`}
            d={`M ${inflated.map((p) => p.join(",")).join(" L ")} Z`}
            fill={family.color}
            fillOpacity={0.1}
            stroke={family.color}
            strokeOpacity={0.75}
            strokeWidth={1.5}
            strokeLinejoin="round"
          />
        );
      })}
    </g>
  );
}

function GuideLines() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {guides.map((g) => {
        const ax = xScale(g.x0);
        const ay = yScale(g.y0);
        const bx = xScale(g.x1);
        const by = yScale(g.y1);
        const mx = xScale(Math.sqrt(g.x0 * g.x1));
        const my = yScale(Math.sqrt(g.y0 * g.y1));
        const angle = (Math.atan2(by - ay, bx - ax) * 180) / Math.PI;
        return (
          <g key={`guide-${g.k}`}>
            <line x1={ax} y1={ay} x2={bx} y2={by} stroke={t.inkSoft} strokeWidth={1.25} strokeDasharray="7 6" strokeOpacity={0.6} />
            <text
              transform={`translate(${mx}, ${my - 9}) rotate(${angle})`}
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
  // The envelopes in px, inflated as FamilyRegions draws them
  const hulls = families.map((family) => {
    const px = family.outline.map(([lx, ly]) => [xScale(10 ** lx), yScale(10 ** ly)]);
    const cx = px.reduce((s, p) => s + p[0], 0) / px.length;
    const cy = px.reduce((s, p) => s + p[1], 0) / px.length;
    return px.map(([x, y]) => {
      const len = Math.hypot(x - cx, y - cy) || 1;
      return [x + ((x - cx) / len) * HULL_MARGIN, y + ((y - cy) / len) * HULL_MARGIN];
    });
  });
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
      // Ray casting: a sample inside another family's envelope rules the spot out
      const inOther = hulls.some(
        (hull, g) =>
          g !== f &&
          samples.some(([sx, sy]) =>
            hull.reduce((inside, [ax, ay], i) => {
              const [bx, by] = hull[(i + 1) % hull.length];
              return ay > sy !== by > sy && sx < ((bx - ax) * (sy - ay)) / (by - ay) + ax ? !inside : inside;
            }, false),
          ),
      );
      if (inOther) return false;
      const distances = hulls.map((hull) =>
        Math.min(
          ...hull.map(([ax, ay], i) => {
            const [bx, by] = hull[(i + 1) % hull.length];
            const len2 = (bx - ax) ** 2 + (by - ay) ** 2 || 1;
            const s = Math.max(0, Math.min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / len2));
            return Math.hypot(x - ax - s * (bx - ax), y - ay - s * (by - ay));
          }),
        ),
      );
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
