// anyplot.ai
// timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG — no seeded RNG in the browser) ----
let seed = 42;
function nextRandom() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const HIST_MONTHS = 36; // 3 years of monthly history
const FORECAST_MONTHS = 12; // 1-year-ahead forecast
const FORECAST_START_INDEX = HIST_MONTHS - 1; // forecast overlaps the last actual point
const TOTAL_MONTHS = HIST_MONTHS + FORECAST_MONTHS;
const START_YEAR = 2023;
const START_MONTH = 8; // September, 0-indexed

const timestamps = [];
for (let i = 0; i < TOTAL_MONTHS; i++) {
  timestamps.push(Date.UTC(START_YEAR, START_MONTH + i, 1));
}

const BASELINE = 110; // thousand sessions
const GROWTH_PER_MONTH = 1.6;
const SEASONAL_AMPLITUDE = 18;

const actualSeries = [];
const forecastSeries = [];
const base80 = [];
const band80 = [];
const base95 = [];
const band95 = [];

for (let i = 0; i < TOTAL_MONTHS; i++) {
  const trend = BASELINE + GROWTH_PER_MONTH * i;
  const seasonal = SEASONAL_AMPLITUDE * Math.sin((2 * Math.PI * (i % 12)) / 12 - Math.PI / 2);
  const expected = trend + seasonal;
  const ts = timestamps[i];

  if (i <= FORECAST_START_INDEX) {
    const noise = (nextRandom() - 0.5) * 14;
    actualSeries.push([ts, Math.round((expected + noise) * 10) / 10]);
  } else {
    actualSeries.push([ts, null]);
  }

  if (i >= FORECAST_START_INDEX) {
    const horizon = i - FORECAST_START_INDEX;
    const point = Math.round(expected * 10) / 10;
    forecastSeries.push([ts, point]);

    const spread80 = 6 + 2.4 * Math.sqrt(horizon + 1);
    const spread95 = 10 + 4.1 * Math.sqrt(horizon + 1);
    base80.push([ts, Math.round((point - spread80) * 10) / 10]);
    band80.push([ts, Math.round(spread80 * 2 * 10) / 10]);
    base95.push([ts, Math.round((point - spread95) * 10) / 10]);
    band95.push([ts, Math.round(spread95 * 2 * 10) / 10]);
  } else {
    forecastSeries.push([ts, null]);
    base80.push([ts, null]);
    band80.push([ts, null]);
    base95.push([ts, null]);
    band95.push([ts, null]);
  }
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const actualColor = t.palette[0]; // brand green — always first series
const forecastColor = t.palette[1]; // canonical position 2
const band80Color = hexToRgba(forecastColor, 0.38); // 80% CI — darker, tighter band
const band95Color = hexToRgba(forecastColor, 0.2); // 95% CI — lighter, wider band

// --- Chart -------------------------------------------------------------------
const TITLE = "timeseries-forecast-uncertainty · javascript · highcharts · anyplot.ai";
const TITLE_FONTSIZE = Math.max(15, Math.round(22 * Math.min(1, 67 / TITLE.length)));

Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: TITLE,
    style: { color: t.ink, fontSize: `${TITLE_FONTSIZE}px`, fontWeight: "600" },
  },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      {
        value: timestamps[FORECAST_START_INDEX],
        color: t.inkSoft,
        width: 2,
        dashStyle: "Dash",
        zIndex: 5,
        label: {
          text: "Forecast start",
          rotation: 0,
          y: 20,
          style: { color: t.inkSoft, fontSize: "13px" },
        },
      },
    ],
  },
  yAxis: {
    reversedStacks: false, // keep the invisible base series at the bottom of the stack
    title: {
      text: "Website sessions (thousands)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  tooltip: {
    shared: true,
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    style: { color: t.ink, fontSize: "13px" },
    valueSuffix: "k",
    xDateFormat: "%b %Y",
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    line: { marker: { enabled: false } },
    area: { stacking: "normal", marker: { enabled: false }, animation: false },
  },
  series: [
    {
      name: "95% confidence",
      type: "area",
      data: base95,
      stack: "ci95",
      color: "transparent",
      lineWidth: 0,
      fillOpacity: 0,
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      name: "95% confidence",
      type: "area",
      data: band95,
      stack: "ci95",
      color: band95Color,
      lineWidth: 0,
      enableMouseTracking: false,
      legendIndex: 3,
    },
    {
      name: "80% confidence",
      type: "area",
      data: base80,
      stack: "ci80",
      color: "transparent",
      lineWidth: 0,
      fillOpacity: 0,
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      name: "80% confidence",
      type: "area",
      data: band80,
      stack: "ci80",
      color: band80Color,
      lineWidth: 0,
      enableMouseTracking: false,
      legendIndex: 2,
    },
    {
      name: "Historical",
      type: "line",
      data: actualSeries,
      color: actualColor,
      lineWidth: 3,
      legendIndex: 0,
    },
    {
      name: "Forecast",
      type: "line",
      data: forecastSeries,
      color: forecastColor,
      lineWidth: 2.5,
      dashStyle: "Dash",
      legendIndex: 1,
    },
  ],
});
