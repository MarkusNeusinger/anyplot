// anyplot.ai
// quiver-basic: Basic Quiver Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 83/100 | Created: 2026-07-24
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data: spiral flow field u = -y + 0.2x, v = x + 0.2y, on a 12x12 grid --
const GRID = 12;
const EXTENT = 6;
const STEP = (2 * EXTENT) / (GRID - 1);

const vectors = [];
let maxMagnitude = 0;
for (let i = 0; i < GRID; i++) {
  for (let j = 0; j < GRID; j++) {
    const x = -EXTENT + i * STEP;
    const y = -EXTENT + j * STEP;
    const u = -y + 0.2 * x;
    const v = x + 0.2 * y;
    const magnitude = Math.hypot(u, v);
    maxMagnitude = Math.max(maxMagnitude, magnitude);
    vectors.push({ x, y, u, v, magnitude });
  }
}

// Scale every vector so the longest arrow spans ~90% of the grid spacing —
// keeps arrows from overlapping their neighbors regardless of field strength.
const ARROW_SCALE = (STEP * 0.9) / maxMagnitude;

// --- Color: imprint_seq (brand green -> blue), driven by vector magnitude -
const hexToRgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const [r0, g0, b0] = hexToRgb(t.seq[0]);
const [r1, g1, b1] = hexToRgb(t.seq[1]);
const colorForMagnitude = (magnitude) => {
  const f = magnitude / maxMagnitude;
  const r = Math.round(r0 + (r1 - r0) * f);
  const g = Math.round(g0 + (g1 - g0) * f);
  const b = Math.round(b0 + (b1 - b0) * f);
  return `rgb(${r}, ${g}, ${b})`;
};

// --- Chart ------------------------------------------------------------------
// The core bundle has no vector-field series type, so the axes below only fix
// the coordinate system; every arrow is drawn as a native SVG path through
// chart.renderer (toPixels() converts data coords to screen space) on each
// render pass — no add-on module, no other library involved.
Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    events: {
      render() {
        if (this.arrowGroup) this.arrowGroup.destroy();
        this.arrowGroup = this.renderer.g("arrows").add();

        vectors.forEach(({ x, y, u, v, magnitude }) => {
          const dx = (u * ARROW_SCALE) / 2;
          const dy = (v * ARROW_SCALE) / 2;
          const x0 = this.xAxis[0].toPixels(x - dx);
          const y0 = this.yAxis[0].toPixels(y - dy);
          const x1 = this.xAxis[0].toPixels(x + dx);
          const y1 = this.yAxis[0].toPixels(y + dy);
          const color = colorForMagnitude(magnitude);

          this.renderer
            .path(["M", x0, y0, "L", x1, y1])
            .attr({ stroke: color, "stroke-width": 2.2, opacity: 0.9 })
            .add(this.arrowGroup);

          const angle = Math.atan2(y1 - y0, x1 - x0);
          const shaftLength = Math.hypot(x1 - x0, y1 - y0);
          const headLength = Math.min(10, shaftLength * 0.45);
          const headAngle = Math.PI / 7;
          const hx1 = x1 - headLength * Math.cos(angle - headAngle);
          const hy1 = y1 - headLength * Math.sin(angle - headAngle);
          const hx2 = x1 - headLength * Math.cos(angle + headAngle);
          const hy2 = y1 - headLength * Math.sin(angle + headAngle);

          this.renderer
            .path(["M", x1, y1, "L", hx1, hy1, "L", hx2, hy2, "Z"])
            .attr({ fill: color, opacity: 0.9 })
            .add(this.arrowGroup);
        });
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "quiver-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Spiral flow field · arrow color encodes vector magnitude",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: -EXTENT - STEP,
    max: EXTENT + STEP,
    title: { text: "x", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    min: -EXTENT - STEP,
    max: EXTENT + STEP,
    title: { text: "y", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: { series: { animation: false, enableMouseTracking: false } },
  series: [
    {
      type: "scatter",
      name: "Grid",
      data: vectors.map((p) => [p.x, p.y]),
      marker: { enabled: false },
      showInLegend: false,
    },
  ],
});
