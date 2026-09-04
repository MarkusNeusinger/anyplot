// anyplot.ai
// circos-basic: Circos Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-04
//# anyplot-orientation: square
// anyplot.ai
// circos-basic: Circos Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-04
const t = window.ANYPLOT_TOKENS;

// --- Data: microservice call graph -----------------------------------------
// Segments = services (outer ring, arc length ∝ code size). Ribbons = call
// volume between services (width ∝ value). Inner track = test coverage.
const MODULES = [
  "Gateway",
  "Auth",
  "Catalog",
  "Orders",
  "Payments",
  "Inventory",
  "Notify",
  "Analytics",
];
const CODE_SIZE_KLOC = [22, 14, 35, 40, 18, 28, 9, 16]; // segment_size
const TEST_COVERAGE = [73, 88, 65, 79, 95, 58, 82, 69]; // track_data (%)

const CONNECTIONS = [
  { source: "Gateway", target: "Auth", value: 120 },
  { source: "Gateway", target: "Catalog", value: 95 },
  { source: "Gateway", target: "Orders", value: 80 },
  { source: "Gateway", target: "Payments", value: 60 },
  { source: "Gateway", target: "Inventory", value: 55 },
  { source: "Gateway", target: "Notify", value: 20 },
  { source: "Gateway", target: "Analytics", value: 8 },
  { source: "Orders", target: "Payments", value: 70 },
  { source: "Orders", target: "Inventory", value: 65 },
  { source: "Orders", target: "Notify", value: 30 },
  { source: "Orders", target: "Catalog", value: 25 },
  { source: "Orders", target: "Auth", value: 14 },
  { source: "Catalog", target: "Inventory", value: 40 },
  { source: "Catalog", target: "Notify", value: 10 },
  { source: "Payments", target: "Notify", value: 35 },
  { source: "Payments", target: "Auth", value: 18 },
  { source: "Inventory", target: "Notify", value: 12 },
  { source: "Analytics", target: "Orders", value: 45 },
  { source: "Analytics", target: "Catalog", value: 38 },
  { source: "Analytics", target: "Payments", value: 28 },
  { source: "Analytics", target: "Inventory", value: 22 },
  { source: "Auth", target: "Notify", value: 15 },
];

const GAP_DEG = 3;

// Segments arranged clockwise from 12 o'clock, span ∝ code size, fixed gaps
// between neighbors for visual separation.
const buildSegments = () => {
  const totalSize = CODE_SIZE_KLOC.reduce((a, b) => a + b, 0);
  const availableDeg = 360 - GAP_DEG * MODULES.length;
  let cursor = 0;
  return MODULES.map((name, i) => {
    const span = (CODE_SIZE_KLOC[i] / totalSize) * availableDeg;
    const startAngle = cursor;
    const endAngle = cursor + span;
    cursor = endAngle + GAP_DEG;
    return {
      name,
      startAngle,
      endAngle,
      color: t.palette[i % t.palette.length],
      codeSize: CODE_SIZE_KLOC[i],
      coverage: TEST_COVERAGE[i],
    };
  });
};

const SEGMENTS = buildSegments();
const SEGMENT_BY_NAME = Object.fromEntries(SEGMENTS.map((s) => [s.name, s]));

// Subdivide each segment's angular span among the connections that touch it
// (as source or target), proportional to connection value — the classic
// chord-diagram allocation. Ribbons are colored by their source segment.
const buildRibbons = () => {
  const touchTotal = {};
  SEGMENTS.forEach((s) => {
    touchTotal[s.name] = 0;
  });
  CONNECTIONS.forEach((c) => {
    touchTotal[c.source] += c.value;
    touchTotal[c.target] += c.value;
  });

  const cursor = {};
  SEGMENTS.forEach((s) => {
    cursor[s.name] = s.startAngle;
  });

  return CONNECTIONS.map((c) => {
    const segS = SEGMENT_BY_NAME[c.source];
    const segT = SEGMENT_BY_NAME[c.target];
    const spanS =
      (c.value / touchTotal[c.source]) * (segS.endAngle - segS.startAngle);
    const spanT =
      (c.value / touchTotal[c.target]) * (segT.endAngle - segT.startAngle);
    const sStart = cursor[c.source];
    const sEnd = sStart + spanS;
    cursor[c.source] = sEnd;
    const tStart = cursor[c.target];
    const tEnd = tStart + spanT;
    cursor[c.target] = tEnd;
    return { ...c, sStart, sEnd, tStart, tEnd, color: segS.color };
  });
};

const RIBBONS = buildRibbons();

// --- Geometry helpers (angle 0 = 12 o'clock, increasing = clockwise) -------
const toRad = (deg) => (deg * Math.PI) / 180;
const polarPoint = (cx, cy, angleDeg, radius) => ({
  x: cx + radius * Math.sin(toRad(angleDeg)),
  y: cy - radius * Math.cos(toRad(angleDeg)),
});

const ringArcPath = (cx, cy, startAngle, endAngle, rInner, rOuter) => {
  const large = endAngle - startAngle > 180 ? 1 : 0;
  const outerStart = polarPoint(cx, cy, startAngle, rOuter);
  const outerEnd = polarPoint(cx, cy, endAngle, rOuter);
  const innerEnd = polarPoint(cx, cy, endAngle, rInner);
  const innerStart = polarPoint(cx, cy, startAngle, rInner);
  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${rOuter} ${rOuter} 0 ${large} 1 ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerEnd.x} ${innerEnd.y}`,
    `A ${rInner} ${rInner} 0 ${large} 0 ${innerStart.x} ${innerStart.y}`,
    "Z",
  ].join(" ");
};

const ribbonPath = (cx, cy, sStart, sEnd, tStart, tEnd, radius) => {
  const largeS = sEnd - sStart > 180 ? 1 : 0;
  const largeT = tEnd - tStart > 180 ? 1 : 0;
  const p1 = polarPoint(cx, cy, sStart, radius);
  const p2 = polarPoint(cx, cy, sEnd, radius);
  const p3 = polarPoint(cx, cy, tStart, radius);
  const p4 = polarPoint(cx, cy, tEnd, radius);
  return [
    `M ${p1.x} ${p1.y}`,
    `A ${radius} ${radius} 0 ${largeS} 1 ${p2.x} ${p2.y}`,
    `Q ${cx} ${cy} ${p3.x} ${p3.y}`,
    `A ${radius} ${radius} 0 ${largeT} 1 ${p4.x} ${p4.y}`,
    `Q ${cx} ${cy} ${p1.x} ${p1.y}`,
    "Z",
  ].join(" ");
};

const hexToRgb = (hex) => {
  const clean = hex.replace("#", "");
  const value = parseInt(clean, 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
};

const lerpColor = (hexA, hexB, ratio) => {
  const a = hexToRgb(hexA);
  const b = hexToRgb(hexB);
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * ratio));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
};

const COVERAGE_MIN = Math.min(...TEST_COVERAGE);
const COVERAGE_MAX = Math.max(...TEST_COVERAGE);

// --- Chrome ------------------------------------------------------------------
const TITLE = "circos-basic · javascript · muix · anyplot.ai";
const TITLE_FONT_DEFAULT = 30;
const titleFontSize =
  TITLE.length > 67
    ? Math.round(TITLE_FONT_DEFAULT * (67 / TITLE.length))
    : TITLE_FONT_DEFAULT;
const SUBTITLE =
  "Ribbon width ∝ API call volume · outer ring ∝ code size · inner track ∝ test coverage (light→dark = low→high)";
const TITLE_H = 58;
const SUBTITLE_H = 32;

function CircosDiagram({ size }) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2;
  const rSegOuter = r * 0.85;
  const segThickness = r * 0.07;
  const rSegInner = rSegOuter - segThickness;
  const trackGap = r * 0.02;
  const rTrackOuter = rSegInner - trackGap;
  const trackThickness = r * 0.12;
  const rTrackBase = rTrackOuter - trackThickness;
  const rRibbon = rTrackBase - r * 0.015;
  const rLabel = rSegOuter + r * 0.05;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      style={{ overflow: "visible" }}
    >
      <g>
        {RIBBONS.map((rb, i) => (
          <path
            key={`ribbon-${i}`}
            d={ribbonPath(cx, cy, rb.sStart, rb.sEnd, rb.tStart, rb.tEnd, rRibbon)}
            fill={rb.color}
            fillOpacity={0.45}
            stroke={rb.color}
            strokeOpacity={0.55}
            strokeWidth={1}
          />
        ))}
      </g>
      <g>
        {SEGMENTS.map((s) => {
          const ratio = (s.coverage - COVERAGE_MIN) / (COVERAGE_MAX - COVERAGE_MIN || 1);
          const barHeight = trackThickness * (0.2 + 0.8 * ratio);
          return (
            <path
              key={`track-${s.name}`}
              d={ringArcPath(
                cx,
                cy,
                s.startAngle + 0.6,
                s.endAngle - 0.6,
                rTrackBase,
                rTrackBase + barHeight,
              )}
              fill={lerpColor(t.seq[0], t.seq[1], ratio)}
            />
          );
        })}
      </g>
      <g>
        {SEGMENTS.map((s) => (
          <path
            key={`seg-${s.name}`}
            d={ringArcPath(cx, cy, s.startAngle, s.endAngle, rSegInner, rSegOuter)}
            fill={s.color}
            stroke={t.pageBg}
            strokeWidth={1.5}
          />
        ))}
      </g>
      <g>
        {SEGMENTS.map((s) => {
          const mid = (s.startAngle + s.endAngle) / 2;
          const p = polarPoint(cx, cy, mid, rLabel);
          const rotate = mid < 180 ? mid - 90 : mid + 90;
          const anchor = mid < 180 ? "start" : "end";
          return (
            <text
              key={`label-${s.name}`}
              x={p.x}
              y={p.y}
              textAnchor={anchor}
              dominantBaseline="middle"
              fontSize={15}
              fill={t.ink}
              transform={`rotate(${rotate}, ${p.x}, ${p.y})`}
            >
              {s.name}
            </text>
          );
        })}
      </g>
    </svg>
  );
}

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chromeH = TITLE_H + SUBTITLE_H;
  // Margin so rotated segment labels never reach the viewport edge (the
  // harness clips at the exact ANYPLOT_SIZE bounds; the <svg> itself uses
  // overflow: visible since its own viewBox would otherwise clip labels
  // that extend past the ring radius).
  const svgSize = Math.min(width, height - chromeH) * 0.78;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ paddingLeft: "20px" }}>
        <div
          style={{
            height: `${TITLE_H}px`,
            lineHeight: `${TITLE_H}px`,
            fontSize: `${titleFontSize}px`,
            fontWeight: 500,
            color: t.ink,
          }}
        >
          {TITLE}
        </div>
        <div
          style={{
            height: `${SUBTITLE_H}px`,
            lineHeight: `${SUBTITLE_H}px`,
            fontSize: "14px",
            fontStyle: "italic",
            color: t.inkSoft,
          }}
        >
          {SUBTITLE}
        </div>
      </div>
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircosDiagram size={svgSize} />
      </div>
    </div>
  );
}
