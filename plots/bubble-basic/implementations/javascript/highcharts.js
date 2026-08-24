// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-08-24

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
for (let i = 0; i < 55; i += 1) {
  const growthRate = -5 + rand() * 35;
  const revenue = 10 + rand() * 490;
  const marketShare = Z_MIN + rand() * (Z_MAX - Z_MIN);
  companies.push({ growthRate, revenue, marketShare });
}

const markerFill = hexToRgba(t.palette[0], 0.6);
const seriesData = companies.map((c) => ({
  x: c.growthRate,
  y: c.revenue,
  marker: { radius: radiusForShare(c.marketShare), fillColor: markerFill, lineColor: t.pageBg, lineWidth: 1.2 },
  custom: { marketShare: Math.round(c.marketShare) },
}));

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
      gridLineColor: t.grid,
      gridLineWidth: 1,
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
  },
);
