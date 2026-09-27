// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 90/100 | Updated: 2026-09-27

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
// Market analysis: growth rate vs. revenue, bubble size = revenue share of segment.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const Z_MIN = 10;
const Z_MAX = 100;
const R_MIN = 9;
const R_MAX = 32;

// Scale by area, not radius, so bubble size reads proportionally.
function radiusForShare(share) {
  const frac = Math.max(0, Math.min(1, (share - Z_MIN) / (Z_MAX - Z_MIN)));
  return R_MIN + (R_MAX - R_MIN) * Math.sqrt(frac);
}

// Small bubbles have the least area to carry color, so nudge their opacity up
// a bit to keep them from washing out against the plot background.
function alphaForShare(share) {
  const frac = Math.max(0, Math.min(1, (share - Z_MIN) / (Z_MAX - Z_MIN)));
  return 0.6 + 0.15 * (1 - frac);
}

const companies = [];
for (let i = 0; i < 90; i += 1) {
  const growthRate = -5 + rand() * 35;
  const revenue = 10 + rand() * 490;
  // Each company's share is relative to its own market segment, not a
  // shared market — so these values do NOT sum to 100 across companies,
  // unlike a conventional "market share" metric. Labelled as such below.
  const segmentShare = Z_MIN + rand() * (Z_MAX - Z_MIN);
  companies.push({ growthRate, revenue, segmentShare });
}

const X_RANGE = 35;
const Y_RANGE = 490;
const X_MIN = -5;
const Y_MIN = 10;

// Declutter pass: the densest region (~19-24% growth, $300-450M revenue)
// otherwise lands several similarly sized bubbles almost exactly on top of
// each other, which reads as one merged blob even with a page-bg stroke.
// Nudge any pair closer than MIN_SEP (in axis-normalized space, so growth%
// and revenue$ contribute comparably) apart along their connecting vector.
const MIN_SEP = 0.035;
for (let i = 1; i < companies.length; i += 1) {
  for (let j = 0; j < i; j += 1) {
    const dx = (companies[i].growthRate - companies[j].growthRate) / X_RANGE;
    const dy = (companies[i].revenue - companies[j].revenue) / Y_RANGE;
    const dist = Math.hypot(dx, dy);
    if (dist > 0 && dist < MIN_SEP) {
      const push = ((MIN_SEP - dist) / dist) * 0.5;
      companies[i].growthRate = Math.min(X_MIN + X_RANGE, Math.max(X_MIN, companies[i].growthRate + dx * push * X_RANGE));
      companies[i].revenue = Math.min(Y_MIN + Y_RANGE, Math.max(Y_MIN, companies[i].revenue + dy * push * Y_RANGE));
    }
  }
}

// Focal point: the standout company that ranks highest on BOTH growth and
// share (normalized 0-1 and summed) — gives the viewer a guided insight
// instead of a bare position+size encoding.
const scored = companies.map((c) => {
  const growthNorm = (c.growthRate - X_MIN) / X_RANGE;
  const shareNorm = (c.segmentShare - Z_MIN) / (Z_MAX - Z_MIN);
  return growthNorm + shareNorm;
});
let focalIndex = 0;
scored.forEach((score, i) => {
  if (score > scored[focalIndex]) focalIndex = i;
});

// Secondary cue: a high-scoring point that also has few neighbors nearby, so
// its label lands in genuinely open space instead of overlapping the dense
// cluster around it — a second, lighter-weight highlight so the chart isn't
// a single point of interest floating over an undifferentiated scatter.
function neighborCount(i) {
  let count = 0;
  companies.forEach((c, j) => {
    if (j === i) return;
    const dx = (c.growthRate - companies[i].growthRate) / X_RANGE;
    const dy = (c.revenue - companies[i].revenue) / Y_RANGE;
    if (Math.hypot(dx, dy) < 0.1) count += 1;
  });
  return count;
}

const secondaryCandidates = companies
  .map((c, i) => {
    const dx = (c.growthRate - companies[focalIndex].growthRate) / X_RANGE;
    const dy = (c.revenue - companies[focalIndex].revenue) / Y_RANGE;
    return { i, distFromFocal: Math.hypot(dx, dy), neighbors: neighborCount(i) };
  })
  .filter((cand) => cand.i !== focalIndex && cand.distFromFocal >= 0.25)
  .sort((a, b) => a.neighbors - b.neighbors || scored[b.i] - scored[a.i]);

const secondaryIndex = secondaryCandidates.length > 0 ? secondaryCandidates[0].i : -1;

const [fr, fg, fb] = [1, 3, 5].map((i) => parseInt(t.palette[0].slice(i, i + 2), 16));
const fillForShare = (share) => `rgba(${fr}, ${fg}, ${fb}, ${alphaForShare(share)})`;
const seriesData = companies.map((c, i) => {
  const isFocal = i === focalIndex;
  return {
    x: c.growthRate,
    y: c.revenue,
    marker: {
      radius: radiusForShare(c.segmentShare),
      fillColor: fillForShare(c.segmentShare),
      // Page-bg stroke carves a visible edge between overlapping same-color
      // bubbles in the densest cluster. The focal point reuses the brand
      // green at full opacity (not amber, which is reserved for warning/
      // caution) so the highlight reads as "notable", not "alert".
      lineColor: isFocal ? t.palette[0] : t.pageBg,
      lineWidth: isFocal ? 3.5 : 3,
    },
    custom: { segmentShare: Math.round(c.segmentShare) },
  };
});

// --- Chart post-render helpers ------------------------------------------------
function drawSizeLegend(chart) {
  // Highcharts core has no bubbleLegend (that lives in highcharts-more), so
  // the size key is drawn manually in the reserved right margin.
  const legendX = chart.plotLeft + chart.plotWidth + 40;
  let cursorY = chart.plotTop + 30;

  chart.renderer
    .text("Share of Own<br/>Market Segment (%)", legendX, cursorY, true)
    .css({ color: t.ink, fontSize: "15px", fontWeight: "600" })
    .add();
  cursorY += 54;

  [Z_MIN, (Z_MIN + Z_MAX) / 2, Z_MAX].forEach((share) => {
    const r = radiusForShare(share);
    const cy = cursorY + R_MAX;
    chart.renderer
      .circle(legendX + R_MAX, cy, r)
      .attr({ fill: fillForShare(share), stroke: t.palette[0], "stroke-width": 1.2 })
      .add();
    chart.renderer
      .text(`${Math.round(share)}%`, legendX + 2 * R_MAX + 16, cy + 5)
      .css({ color: t.inkSoft, fontSize: "14px" })
      .add();
    cursorY += 2 * R_MAX + 16;
  });
}

function highlightFocalPoint(chart) {
  // Guide the viewer to one standout company (top-ranked on both growth and
  // share) with a brand-green-ringed marker and a native Highcharts
  // SVGRenderer "callout" label pointing at it — a focal point beyond the
  // bare position+size encoding. Brand green (not amber, reserved for
  // warning/caution) keeps the highlight read as "notable" rather than "alert".
  const focal = companies[focalIndex];
  const point = chart.series[0].points[focalIndex];
  const anchorX = chart.plotLeft + point.plotX;
  const anchorY = chart.plotTop + point.plotY;
  const labelX = Math.min(anchorX + 60, chart.plotLeft + chart.plotWidth - 160);
  const labelY = Math.max(anchorY - 70, chart.plotTop + 10);

  chart.renderer
    .label(
      `Standout: ${focal.growthRate.toFixed(0)}% growth, ${Math.round(focal.segmentShare)}% segment share`,
      labelX,
      labelY,
      "callout",
      anchorX,
      anchorY,
    )
    .css({ color: t.ink, fontSize: "13px", fontWeight: "600" })
    .attr({ fill: t.elevatedBg, stroke: t.palette[0], "stroke-width": 1.5, padding: 8, r: 5, zIndex: 6 })
    .add();
}

function highlightSecondaryPoint(chart) {
  // A second, deliberately lighter-weight cue: a plain italic note on a thin
  // dotted leader, no fill box or border. This gives the chart a secondary
  // point of interest — beyond the single bordered focal callout — without
  // competing with it for visual weight.
  if (secondaryIndex < 0) return;
  const secondary = companies[secondaryIndex];
  const point = chart.series[0].points[secondaryIndex];
  const anchorX = chart.plotLeft + point.plotX;
  const anchorY = chart.plotTop + point.plotY;
  const labelX = Math.min(Math.max(anchorX + 90, chart.plotLeft + 10), chart.plotLeft + chart.plotWidth - 195);
  const labelY = Math.min(Math.max(anchorY - 60, chart.plotTop + 10), chart.plotTop + chart.plotHeight - 16);

  chart.renderer
    .path(["M", anchorX, anchorY, "L", labelX - 6, labelY + 6])
    .attr({ stroke: t.inkSoft, "stroke-width": 1, dashstyle: "Dot", zIndex: 5 })
    .add();
  chart.renderer
    .text(
      `Also notable: ${secondary.growthRate.toFixed(0)}% growth, ${Math.round(secondary.segmentShare)}% share`,
      labelX,
      labelY,
    )
    .css({ color: t.inkSoft, fontSize: "12px", fontStyle: "italic" })
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
      style: { color: t.ink, fontSize: "23px", fontWeight: "700" },
      margin: 26,
    },
    xAxis: {
      title: {
        text: "Year-over-Year Growth Rate (%)",
        style: { color: t.inkSoft, fontSize: "16px", fontWeight: "500" },
      },
      lineColor: t.inkSoft,
      tickColor: t.inkSoft,
      tickWidth: 0,
      tickLength: 0,
      gridLineColor: t.grid,
      gridLineWidth: 1,
      labels: { style: { color: t.inkSoft, fontSize: "14px" }, format: "{value}%" },
    },
    yAxis: {
      title: {
        text: "Annual Revenue ($M)",
        style: { color: t.inkSoft, fontSize: "16px", fontWeight: "500" },
      },
      lineColor: t.inkSoft,
      tickColor: t.inkSoft,
      tickWidth: 0,
      tickLength: 0,
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
          `Share of own segment: <b>${this.custom.segmentShare}%</b>`
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
    highlightSecondaryPoint(chart);
  },
);
