// anyplot.ai
// area-basic: Basic Area Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-20

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Web server CPU utilization sampled every 30 minutes over a 24-hour window —
// low overnight, ramping up through the workday, peaking mid-afternoon.
function lcg(seed) {
  let state = seed;
  return function next() {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
}
const random = lcg(42);

const cpuUtilization = [];
for (let step = 0; step < 48; step += 1) {
  const hour = step * 0.5;
  const dailyCurve = 20 + 58 * Math.exp(-((hour - 14.5) ** 2) / (2 * 4.2 ** 2));
  const noise = (random() - 0.5) * 7;
  const timestamp = Date.UTC(2026, 0, 12, Math.floor(hour), (hour % 1) * 60);
  const percent = Math.max(3, Math.min(97, dailyCurve + noise));
  cpuUtilization.push([timestamp, Math.round(percent * 10) / 10]);
}

// Call out the daily peak with a highlighted marker + data label.
let peakIndex = 0;
for (let i = 1; i < cpuUtilization.length; i += 1) {
  if (cpuUtilization[i][1] > cpuUtilization[peakIndex][1]) peakIndex = i;
}
const [peakX, peakY] = cpuUtilization[peakIndex];
cpuUtilization[peakIndex] = {
  x: peakX,
  y: peakY,
  marker: {
    enabled: true,
    radius: 6,
    fillColor: t.palette[0],
    lineColor: t.pageBg,
    lineWidth: 2,
  },
  dataLabels: {
    enabled: true,
    format: "Peak {y}%",
    y: -16,
    style: { color: t.ink, fontSize: "13px", fontWeight: "600", textOutline: "none" },
  },
};

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "area",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "area-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Web server CPU utilization, 24-hour sample",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    type: "datetime",
    tickInterval: 4 * 3600 * 1000,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      format: "{value:%H:%M}",
    },
    title: {
      text: "Time of Day (UTC)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
  },
  yAxis: {
    min: 0,
    max: 100,
    tickInterval: 20,
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      format: "{value}%",
    },
    title: {
      text: "CPU Utilization (%)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    plotBands: [
      {
        from: 70,
        to: 100,
        color: Highcharts.color(t.amber).setOpacity(0.12).get("rgba"),
        label: {
          text: "Elevated load",
          align: "right",
          x: -8,
          y: 14,
          style: { color: t.inkSoft, fontSize: "12px" },
        },
      },
    ],
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    area: {
      lineWidth: 3,
      lineColor: t.palette[0],
      fillColor: {
        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
        stops: [
          [0, Highcharts.color(t.palette[0]).setOpacity(0.45).get("rgba")],
          [1, Highcharts.color(t.palette[0]).setOpacity(0.02).get("rgba")],
        ],
      },
      marker: { enabled: false, states: { hover: { enabled: true, radius: 5 } } },
      states: { hover: { lineWidthPlus: 0 } },
    },
  },
  series: [{ name: "CPU Utilization", data: cpuUtilization }],
});
