// anyplot.ai
// horizon-basic: Horizon Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-18

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: CPU load deviation from a 50% baseline, 10 fleet hosts over 24h --
// deterministic Park-Miller LCG — no seeded RNG in the browser
function makeLcg(seed) {
  let state = seed % 2147483647;
  if (state <= 0) state += 2147483646;
  return function next() {
    state = (state * 16807) % 2147483647;
    return (state - 1) / 2147483646;
  };
}

const HOSTS = ["api-1", "api-2", "api-3", "api-4", "worker-1", "worker-2",
               "cache-1", "cache-2", "db-primary", "db-replica"];
const POINTS = 144; // one reading every 10 minutes across 24h
const STEP_MS = 10 * 60 * 1000;
const START_MS = Date.UTC(2024, 5, 10, 0, 0, 0);
const BAND_HEIGHT = 15; // percentage points of CPU deviation folded per band
const BAND_COUNT = 3; // horizon bands per polarity (mirrored blue/red)

const hostSeries = HOSTS.map((name, hostIndex) => {
  const rng = makeLcg(1000 + hostIndex * 97);
  let level = (rng() - 0.5) * 20;
  const drift = (rng() - 0.5) * 0.4;
  const values = [];
  for (let p = 0; p < POINTS; p += 1) {
    level = (level + drift + (rng() - 0.5) * 8) * 0.96;
    values.push(level);
  }
  return { name, values };
});

// --- Horizon folding: clamp the excess above each band threshold into 0..H -
function foldBand(value, bandIndex, bandHeight) {
  return Math.min(Math.max(value - bandIndex * bandHeight, 0), bandHeight);
}

// --- Band colors: interpolate the Imprint diverging stops (imprint_div) ----
function lerpHex(hexA, hexB, fraction) {
  const a = [1, 3, 5].map((i) => parseInt(hexA.slice(i, i + 2), 16));
  const b = [1, 3, 5].map((i) => parseInt(hexB.slice(i, i + 2), 16));
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * fraction));
  return `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

const midColor = t.div[1];
const positiveColors = Array.from({ length: BAND_COUNT },
  (_, i) => lerpHex(midColor, t.div[2], (i + 1) / BAND_COUNT));
const negativeColors = Array.from({ length: BAND_COUNT },
  (_, i) => lerpHex(midColor, t.div[0], (i + 1) / BAND_COUNT));

// --- Series: 2 x BAND_COUNT opaque area layers per host, stacked on top ----
// so a deeper shade only shows through where the value actually reaches it.
const series = [];
hostSeries.forEach((host, hostIndex) => {
  for (let band = 0; band < BAND_COUNT; band += 1) {
    series.push({
      type: "area",
      yAxis: hostIndex,
      name: `${host.name} +band${band + 1}`,
      color: positiveColors[band],
      fillColor: positiveColors[band],
      fillOpacity: 1,
      lineWidth: 0,
      threshold: 0,
      marker: { enabled: false },
      enableMouseTracking: false,
      data: host.values.map((v, p) => [START_MS + p * STEP_MS, foldBand(v, band, BAND_HEIGHT)]),
    });
    series.push({
      type: "area",
      yAxis: hostIndex,
      name: `${host.name} -band${band + 1}`,
      color: negativeColors[band],
      fillColor: negativeColors[band],
      fillOpacity: 1,
      lineWidth: 0,
      threshold: 0,
      marker: { enabled: false },
      enableMouseTracking: false,
      data: host.values.map((v, p) => [START_MS + p * STEP_MS, foldBand(-v, band, BAND_HEIGHT)]),
    });
  }
});

// --- Panels: one compact yAxis strip per host, sharing the datetime xAxis --
const rowHeightPct = 100 / HOSTS.length;
const yAxis = HOSTS.map((name, hostIndex) => ({
  top: `${hostIndex * rowHeightPct}%`,
  height: `${rowHeightPct - 1.4}%`,
  min: 0,
  max: BAND_HEIGHT,
  gridLineWidth: 0,
  tickLength: 0,
  lineWidth: 0,
  labels: { enabled: false },
  title: {
    text: name,
    align: "middle",
    rotation: 0,
    x: -8,
    style: { color: t.inkSoft, fontSize: "13px", fontWeight: "500" },
  },
  plotLines: [{ value: 0, color: t.grid, width: 1, zIndex: 5 }],
}));

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: { backgroundColor: "transparent", animation: false,
           style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "horizon-basic · javascript · highcharts · anyplot.ai",
           style: { color: t.ink, fontSize: "22px", fontWeight: "600" } },
  subtitle: { text: "CPU deviation from a 50% baseline, folded into 3 bands per host — blue rises above baseline, red falls below, deeper shade means larger swing",
              style: { color: t.inkSoft, fontSize: "14px" } },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft, tickColor: t.inkSoft, gridLineWidth: 0,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Time (UTC)", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis,
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: { series: { animation: false } },
  series,
});
