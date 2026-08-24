// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
// Market analysis: growth rate vs. revenue, bubble size = market share.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const Z_MIN = 10;
const Z_MAX = 100;
const R_MIN = 6;
const R_MAX = 32;

// Scale by area, not radius, so bubble size reads proportionally.
function radiusForShare(share) {
  const frac = Math.max(0, Math.min(1, (share - Z_MIN) / (Z_MAX - Z_MIN)));
  return R_MIN + (R_MAX - R_MIN) * Math.sqrt(frac);
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const companies = [];
for (let i = 0; i < 90; i += 1) {
  const growthRate = -5 + rand() * 35;
  const revenue = 10 + rand() * 490;
  const marketShare = Z_MIN + rand() * (Z_MAX - Z_MIN);
  companies.push({ growthRate, revenue, marketShare });
}

// Focal point: the standout company that ranks highest on BOTH growth and
// share (normalized 0-1 and summed) — gives the viewer a guided insight
// instead of a bare position+size encoding.
let focalIndex = 0;
let focalScore = -Infinity;
companies.forEach((c, i) => {
  const growthNorm = (c.growthRate + 5) / 35;
  const shareNorm = (c.marketShare - Z_MIN) / (Z_MAX - Z_MIN);
  const score = growthNorm + shareNorm;
  if (score > focalScore) {
    focalScore = score;
    focalIndex = i;
  }
});

const markerFill = hexToRgba(t.palette[0], 0.6);
const seriesData = companies.map((c, i) => {
  const isFocal = i === focalIndex;
  return {
    x: c.growthRate,
    y: c.revenue,
    marker: {
      radius: radiusForShare(c.marketShare),
      fillColor: markerFill,
      lineColor: isFocal ? t.amber : t.pageBg,
      lineWidth: isFocal ? 3 : 1.6,
    },
    custom: { marketShare: Math.round(c.marketShare) },
  };
});

// --- Chart post-render helpers ------------------------------------------------
function drawSizeLegend(chart) {
  // Highcharts core has no bubbleLegend (that lives in highcharts-more), so
  // the size key is drawn manually in the reserved right margin.
  const legendX = chart.plotLeft + chart.plotWidth + 40;
  let cursorY = chart.plotTop + 30;

  chart.renderer
    .text("Market Share (%)", legendX, cursorY)
    .css({ color: t.ink, fontSize: "14px", fontWeight: "600" })
    .add();
  cursorY += 30;

  [Z_MIN, (Z_MIN + Z_MAX) / 2, Z_MAX].forEach((share) => {
    const r = radiusForShare(share);
    const cy = cursorY + R_MAX;
    chart.renderer
      .circle(legendX + R_MAX, cy, r)
      .attr({ fill: markerFill, stroke: t.palette[0], "stroke-width": 1.2 })
      .add();
    chart.renderer
      .text(`${Math.round(share)}%`, legendX + 2 * R_MAX + 16, cy + 5)
      .css({ color: t.inkSoft, fontSize: "13px" })
      .add();
    cursorY += 2 * R_MAX + 16;
  });
}

function highlightFocalPoint(chart) {
  // Guide the viewer to one standout company (top-ranked on both growth and
  // share) with an amber-ringed marker and a native Highcharts SVGRenderer
  // "callout" label pointing at it — a focal point beyond the bare
  // position+size encoding.
  const focal = companies[focalIndex];
  const point = chart.series[0].points[focalIndex];
  const anchorX = chart.plotLeft + point.plotX;
  const anchorY = chart.plotTop + point.plotY;
  const labelX = Math.min(anchorX + 60, chart.plotLeft + chart.plotWidth - 160);
  const labelY = Math.max(anchorY - 70, chart.plotTop + 10);

  chart.renderer
    .label(
      `Standout: ${focal.growthRate.toFixed(0)}% growth, ${Math.round(focal.marketShare)}% share`,
      labelX,
      labelY,
      "callout",
      anchorX,
      anchorY,
    )
    .css({ color: t.ink, fontSize: "13px", fontWeight: "600" })
    .attr({ fill: t.elevatedBg, stroke: t.amber, "stroke-width": 1.5, padding: 8, r: 5, zIndex: 6 })
    .add();
}

// --- Chart -------------------------------------------------------------------
// Core bundle has no highcharts-more, so bubbles are core "scatter" points
// with a per-point marker.radius (area-scaled) instead of the "bubble" series
// type — same visual result using only the loaded core module.
Highcharts.chart(
  "container",
  {
    chart: {
      type: "scatter",
      backgroundColor: "transparent",
      animation: false,
      marginRight: 210,
      style: { fontFamily: "inherit" },
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
      text: "bubble-basic · javascript · highcharts · anyplot.ai",
      style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
    },
    xAxis: {
      title: { text: "Year-over-Year Growth Rate (%)", style: { color: t.inkSoft, fontSize: "16px" } },
      lineColor: t.inkSoft,
      tickColor: t.inkSoft,
      gridLineWidth: 0,
      labels: { style: { color: t.inkSoft, fontSize: "14px" }, format: "{value}%" },
    },
    yAxis: {
      title: { text: "Annual Revenue ($M)", style: { color: t.inkSoft, fontSize: "16px" } },
      lineColor: t.inkSoft,
      tickColor: t.inkSoft,
      gridLineColor: t.grid,
      gridLineWidth: 1,
      labels: { style: { color: t.inkSoft, fontSize: "14px" }, format: "${value}" },
    },
    legend: { enabled: false },
    tooltip: {
      backgroundColor: t.elevatedBg,
      borderColor: t.grid,
      style: { color: t.ink, fontSize: "13px" },
      pointFormatter: function pointFormatter() {
        return (
          `Growth: <b>${this.x.toFixed(1)}%</b><br/>` +
          `Revenue: <b>$${this.y.toFixed(0)}M</b><br/>` +
          `Market share: <b>${this.custom.marketShare}%</b>`
        );
      },
    },
    plotOptions: {
      series: { animation: false },
      scatter: { marker: { symbol: "circle", states: { hover: { lineWidthPlus: 1 } } } },
    },
    series: [{ name: "Companies", data: seriesData, showInLegend: false }],
  },
  function drawExtras(chart) {
    drawSizeLegend(chart);
    highlightFocalPoint(chart);
  },
);
