// anyplot.ai
// scatter-color-mapped: Color-Mapped Scatter Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
let seed = 42;
function rand() {
  seed = (1664525 * seed + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const pointCount = 150;
const readings = [];
for (let i = 0; i < pointCount; i++) {
  const temperature = 150 + rand() * 100; // reaction temperature, deg C
  const duration = 10 + rand() * 80; // reaction duration, minutes
  const noise = (rand() - 0.5) * 15;
  let yieldPct =
    95 -
    0.012 * (temperature - 200) ** 2 -
    0.02 * (duration - 50) ** 2 +
    noise;
  yieldPct = Math.max(5, Math.min(98, yieldPct));
  readings.push({ x: temperature, y: duration, yieldPct });
}

const yieldValues = readings.map((r) => r.yieldPct);
const yieldMin = Math.min(...yieldValues);
const yieldMax = Math.max(...yieldValues);

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
function yieldColor(value) {
  const ratio = (value - yieldMin) / (yieldMax - yieldMin);
  const [r, g, b] = seqLow.map((c, i) => Math.round(c + (seqHigh[i] - c) * ratio));
  return `rgb(${r}, ${g}, ${b})`;
}

const points = readings.map((r) => ({
  x: r.x,
  y: r.y,
  color: yieldColor(r.yieldPct),
  custom: { yieldPct: r.yieldPct },
}));

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    marginRight: 190,
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
          const frac = (i + 0.5) / bandCount;
          const value = yieldMin + frac * (yieldMax - yieldMin);
          chart.renderer
            .rect(barX, barY + barHeight - (i + 1) * bandHeight, barWidth, bandHeight + 0.5)
            .attr({ fill: yieldColor(value) })
            .add();
        }
        chart.renderer
          .rect(barX, barY, barWidth, barHeight)
          .attr({ fill: "none", stroke: t.inkSoft, "stroke-width": 1 })
          .add();

        const tickCount = 5;
        for (let i = 0; i < tickCount; i++) {
          const frac = i / (tickCount - 1);
          const value = yieldMin + frac * (yieldMax - yieldMin);
          const tickY = barY + barHeight * (1 - frac);
          chart.renderer
            .path(["M", barX + barWidth, tickY, "L", barX + barWidth + 6, tickY])
            .attr({ stroke: t.inkSoft, "stroke-width": 1 })
            .add();
          chart.renderer
            .text(value.toFixed(0), barX + barWidth + 12, tickY + 5)
            .css({ color: t.inkSoft, fontSize: "14px" })
            .add();
        }

        chart.renderer
          .text("Reaction Yield (%)", barX + barWidth + 60, barY + barHeight / 2)
          .attr({ rotation: 90, align: "center" })
          .css({ color: t.inkSoft, fontSize: "16px" })
          .add();
      },
    },
  },
  credits: { enabled: false },
  accessibility: { enabled: false },
  title: {
    text: "scatter-color-mapped · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  legend: { enabled: false },
  tooltip: {
    pointFormat:
      "Temperature: {point.x:.0f}°C<br/>Duration: {point.y:.0f} min<br/>Yield: {point.custom.yieldPct:.1f}%",
  },
  xAxis: {
    title: {
      text: "Reaction Temperature (°C)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Reaction Duration (min)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: {
        radius: 7,
        lineWidth: 1,
        lineColor: t.pageBg,
      },
    },
  },
  series: [
    {
      name: "Yield",
      showInLegend: false,
      data: points,
    },
  ],
});
