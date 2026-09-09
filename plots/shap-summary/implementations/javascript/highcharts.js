// anyplot.ai
// shap-summary: SHAP Summary Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
let seed = 42;
function rand() {
  seed = (1664525 * seed + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randNormal() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const N_SAMPLES = 180;

function zscore(values) {
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length;
  const std = Math.sqrt(variance);
  return values.map((v) => (v - mean) / std);
}

function minMaxNorm(values) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  return values.map((v) => (v - min) / (max - min));
}

// Raw feature values for a synthetic gradient-boosted house-price model
const rawFeatures = {
  "Living Area (sqft)": Array.from({ length: N_SAMPLES }, () => 1450 + randNormal() * 480),
  Bathrooms: Array.from({ length: N_SAMPLES }, () => 2 + randNormal() * 0.9),
  "House Age (years)": Array.from({ length: N_SAMPLES }, () => 28 + randNormal() * 16),
  "Garage Spaces": Array.from({ length: N_SAMPLES }, () => 1.6 + randNormal() * 0.8),
  "Lot Size (acres)": Array.from({ length: N_SAMPLES }, () => 0.35 + randNormal() * 0.18),
  "Distance to Downtown (km)": Array.from({ length: N_SAMPLES }, () => 12 + randNormal() * 7),
  "Walk Score": Array.from({ length: N_SAMPLES }, () => 55 + randNormal() * 22),
};
const featureNames = Object.keys(rawFeatures);

const zFeatures = {};
featureNames.forEach((name) => {
  zFeatures[name] = zscore(rawFeatures[name]);
});

// SHAP-like contribution per feature, in $1,000s of predicted price.
// "House Age" is modeled as non-linear: both historic and brand-new homes
// command a premium over mid-age housing stock.
const shapValues = {};
featureNames.forEach((name) => {
  shapValues[name] = zFeatures[name].map((zi) => {
    const noise = randNormal() * 4;
    switch (name) {
      case "Living Area (sqft)":
        return 26 * zi + noise;
      case "Bathrooms":
        return 14 * zi + noise;
      case "House Age (years)":
        return 9 * zi ** 2 - 6 + noise * 0.8;
      case "Garage Spaces":
        return 8 * zi + noise * 0.7;
      case "Lot Size (acres)":
        return 7 * zi + noise * 0.7;
      case "Distance to Downtown (km)":
        return -11 * zi + noise;
      case "Walk Score":
        return 6 * zi + noise * 0.8;
      default:
        return noise;
    }
  });
});

// Rank features by mean absolute SHAP value — most important at the top.
const meanAbsShap = {};
featureNames.forEach((name) => {
  const vals = shapValues[name];
  meanAbsShap[name] = vals.reduce((a, b) => a + Math.abs(b), 0) / vals.length;
});
const orderedFeatures = [...featureNames].sort((a, b) => meanAbsShap[b] - meanAbsShap[a]);
const categories = orderedFeatures;

const normFeatures = {};
featureNames.forEach((name) => {
  normFeatures[name] = minMaxNorm(rawFeatures[name]);
});

// --- Color mapping ------------------------------------------------------------
// The `coloraxis` module (colorAxis + automatic legend gradient) lives in
// modules/coloraxis.js, which isn't loaded — only the core bundle is. Interpolate
// each point's fill from the Imprint imprint_seq gradient by hand instead, and
// draw a matching colorbar with the core SVG renderer.
function hexToRgb(hex) {
  const v = parseInt(hex.slice(1), 16);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}
const seqLow = hexToRgb(t.seq[0]);
const seqHigh = hexToRgb(t.seq[1]);
function valueColor(ratio) {
  const [r, g, b] = seqLow.map((c, i) => Math.round(c + (seqHigh[i] - c) * ratio));
  return `rgb(${r}, ${g}, ${b})`;
}

// Beeswarm points: one dot per sample per feature, jittered around its row.
const points = [];
orderedFeatures.forEach((name, rowIndex) => {
  const shap = shapValues[name];
  const norm = normFeatures[name];
  shap.forEach((value, j) => {
    const jitter = (rand() - 0.5) * 0.62;
    points.push({
      x: value,
      y: rowIndex + jitter,
      color: valueColor(norm[j]),
      custom: { feature: name, featureValue: rawFeatures[name][j] },
    });
  });
});

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    marginRight: 170,
    style: { fontFamily: "inherit" },
    events: {
      load: function () {
        // Manual colorbar (see "Color mapping" note above) mirroring the
        // imprint_seq gradient used for the point fills.
        const chart = this;
        const barWidth = 26;
        const barX = chart.plotLeft + chart.plotWidth + 46;
        const barY = chart.plotTop;
        const barHeight = chart.plotHeight;

        // Fragment-url paint servers (linearGradient defs) don't resolve on the
        // harness's about:blank document, so the bar is built from many thin
        // interpolated bands instead of a single gradient fill.
        const bandCount = 60;
        const bandHeight = barHeight / bandCount;
        for (let i = 0; i < bandCount; i++) {
          const frac = (i + 0.5) / bandCount; // 0 = bottom (low), 1 = top (high)
          chart.renderer
            .rect(barX, barY + barHeight - (i + 1) * bandHeight, barWidth, bandHeight + 0.5)
            .attr({ fill: valueColor(frac) })
            .add();
        }
        chart.renderer
          .rect(barX, barY, barWidth, barHeight)
          .attr({ fill: "none", stroke: t.inkSoft, "stroke-width": 1 })
          .add();

        chart.renderer
          .text("High", barX + barWidth + 10, barY + 14)
          .css({ color: t.inkSoft, fontSize: "14px" })
          .add();
        chart.renderer
          .text("Low", barX + barWidth + 10, barY + barHeight)
          .css({ color: t.inkSoft, fontSize: "14px" })
          .add();
        chart.renderer
          .text("Feature value", barX + barWidth + 58, barY + barHeight / 2)
          .attr({ rotation: 90, align: "center" })
          .css({ color: t.inkSoft, fontSize: "16px" })
          .add();
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "shap-summary · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Gradient-boosted house-price model · 180 samples",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  legend: { enabled: false },
  tooltip: {
    headerFormat: "",
    pointFormat:
      "<b>{point.custom.feature}</b><br/>Feature value: {point.custom.featureValue:.2f}<br/>SHAP value: {point.x:.2f}",
  },
  xAxis: {
    title: {
      text: "SHAP value (impact on predicted price, $1,000s)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [{ value: 0, color: t.inkSoft, width: 1.5, dashStyle: "ShortDash", zIndex: 3 }],
  },
  yAxis: {
    categories,
    reversed: true,
    tickPositions: categories.map((_, i) => i),
    minPadding: 0.09,
    maxPadding: 0.09,
    startOnTick: false,
    endOnTick: false,
    title: { text: null },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    // Faint focal-point band on the most important feature (row 0) so the
    // ranking hierarchy reads at a glance, not just via row order.
    plotBands: [{ from: -0.5, to: 0.5, color: t.elevatedBg, zIndex: 0 }],
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: { radius: 5, lineWidth: 0.5, lineColor: t.pageBg, fillOpacity: 0.75 },
    },
  },
  series: [{ name: "SHAP values", showInLegend: false, data: points }],
});
