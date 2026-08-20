// anyplot.ai
// feynman-basic: Feynman Diagram for Particle Interactions
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-20

const t = window.ANYPLOT_TOKENS;

// --- Data: e- + e+ -> gamma -> mu- + mu+ (QED annihilation / pair production) ---
// Vertices are interaction points; propagators connect them (or connect a
// vertex to an external incoming/outgoing leg). Coordinates are a plain
// data-space grid — time runs left to right, as is conventional.
const V1 = { x: 2, y: 0 };
const V2 = { x: 4, y: 0 };

const legs = [
  { from: { x: 0, y: 2.6 }, to: V1, style: "straight", color: t.palette[0],
    label: "e⁻", align: "left", labelPos: { x: 0.4, y: 2.85 }, arrow: "forward" },
  { from: { x: 0, y: -2.6 }, to: V1, style: "straight", color: t.palette[0],
    label: "e⁺", align: "left", labelPos: { x: 0.4, y: -2.95 }, arrow: "backward" },
  { from: V1, to: V2, style: "wavy", color: t.palette[1],
    label: "γ", align: "center", labelPos: { x: 3, y: 0.7 }, arrow: null },
  { from: V2, to: { x: 6, y: 2.6 }, style: "straight", color: t.palette[2],
    label: "μ⁻", align: "right", labelPos: { x: 5.6, y: 2.85 }, arrow: "forward" },
  { from: V2, to: { x: 6, y: -2.6 }, style: "straight", color: t.palette[2],
    label: "μ⁺", align: "right", labelPos: { x: 5.6, y: -2.95 }, arrow: "backward" },
];

// --- Helpers -----------------------------------------------------------------

function toPx(chart, point) {
  return {
    x: chart.xAxis[0].toPixels(point.x, false),
    y: chart.yAxis[0].toPixels(point.y, false),
  };
}

function straightPath(p1, p2) {
  return ["M", p1.x, p1.y, "L", p2.x, p2.y];
}

function wavyPath(p1, p2, amplitude, wavelengths) {
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const len = Math.sqrt(dx * dx + dy * dy);
  const ux = dx / len;
  const uy = dy / len;
  const nx = -uy;
  const ny = ux;
  const steps = 120;
  const path = ["M", p1.x, p1.y];
  for (let i = 1; i <= steps; i++) {
    const s = i / steps;
    const offset = amplitude * Math.sin(2 * Math.PI * wavelengths * s);
    path.push("L", p1.x + ux * len * s + nx * offset, p1.y + uy * len * s + ny * offset);
  }
  return path;
}

// Arrowhead centred on (cx, cy), pointing along `angle` (radians).
function arrowPath(cx, cy, angle, size) {
  const half = size * 0.55;
  const tipX = cx + size * 0.6 * Math.cos(angle);
  const tipY = cy + size * 0.6 * Math.sin(angle);
  const baseX = cx - size * 0.4 * Math.cos(angle);
  const baseY = cy - size * 0.4 * Math.sin(angle);
  const perp = angle + Math.PI / 2;
  const leftX = baseX + half * Math.cos(perp);
  const leftY = baseY + half * Math.sin(perp);
  const rightX = baseX - half * Math.cos(perp);
  const rightY = baseY - half * Math.sin(perp);
  return ["M", tipX, tipY, "L", leftX, leftY, "L", rightX, rightY, "Z"];
}

function drawDiagram(chart) {
  const renderer = chart.renderer;
  const group = renderer.g("feynman-diagram").add();

  legs.forEach((leg) => {
    const p1 = toPx(chart, leg.from);
    const p2 = toPx(chart, leg.to);

    const path = leg.style === "wavy" ? wavyPath(p1, p2, 14, 5) : straightPath(p1, p2);
    renderer.path(path)
      .attr({ stroke: leg.color, "stroke-width": 3, fill: "none", "stroke-linejoin": "round" })
      .add(group);

    if (leg.arrow) {
      const mid = { x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2 };
      let angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);
      if (leg.arrow === "backward") angle += Math.PI;
      renderer.path(arrowPath(mid.x, mid.y, angle, 20))
        .attr({ fill: leg.color, stroke: "none" })
        .add(group);
    }

    const labelPx = toPx(chart, leg.labelPos);
    renderer.text(leg.label, labelPx.x, labelPx.y)
      .attr({ align: leg.align })
      .css({ color: leg.color, fontSize: "20px", fontWeight: "600" })
      .add(group);
  });

  [V1, V2].forEach((vertex) => {
    const p = toPx(chart, vertex);
    renderer.circle(p.x, p.y, 8).attr({ fill: t.ink, stroke: "none" }).add(group);
  });
}

// --- Chart ---------------------------------------------------------------
// Axes are used purely as the data-to-pixel coordinate system (hidden line,
// ticks, gridlines) — the diagram itself is drawn with the SVG renderer in
// the `load` event so lines/arrows can follow arbitrary particle-line
// geometry (straight with arrowheads, sine-wave photon) that no built-in
// series type expresses.
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    events: {
      load: function () {
        drawDiagram(this);
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "feynman-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    min: -0.5,
    max: 6.5,
    startOnTick: false,
    endOnTick: false,
    lineWidth: 0,
    tickLength: 0,
    gridLineWidth: 0,
    labels: { enabled: false },
    title: { text: "time →", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: {
    min: -3.6,
    max: 3.6,
    startOnTick: false,
    endOnTick: false,
    lineWidth: 0,
    tickLength: 0,
    gridLineWidth: 0,
    labels: { enabled: false },
    title: { text: null },
  },
  legend: {
    align: "right",
    verticalAlign: "middle",
    layout: "vertical",
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: { series: { animation: false, enableMouseTracking: false, marker: { enabled: false } } },
  series: [
    { name: "Electron / positron (fermion)", color: t.palette[0], lineWidth: 3, data: [], showInLegend: true },
    { name: "Photon (γ, wavy)", color: t.palette[1], lineWidth: 3, data: [], showInLegend: true },
    { name: "Muon / antimuon (fermion)", color: t.palette[2], lineWidth: 3, data: [], showInLegend: true },
  ],
});
