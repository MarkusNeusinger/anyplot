// anyplot.ai
// sparkline-basic: Basic Sparkline
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG — daily active users, thousands) --
function lcg(seed) {
  let state = seed % 2147483647;
  if (state <= 0) state += 2147483646;
  return function () {
    state = (state * 48271) % 2147483647;
    return (state - 1) / 2147483646;
  };
}
const rand = lcg(42);
const days = 60;
const values = [];
let level = 58;
for (let i = 0; i < days; i++) {
  level = Math.max(30, level + 0.35 + (rand() - 0.5) * 4.5);
  values.push(Math.round(level * 10) / 10);
}

const minIndex = values.indexOf(Math.min(...values));
const maxIndex = values.indexOf(Math.max(...values));
const lastIndex = values.length - 1;

const referenceMarker = {
  enabled: true,
  radius: 5,
  fillColor: t.ink,
  lineColor: t.pageBg,
  lineWidth: 1.5,
};

const seriesData = values.map((value, index) => {
  if (index === lastIndex) {
    return {
      y: value,
      marker: { enabled: true, radius: 7, fillColor: t.palette[0], lineColor: t.pageBg, lineWidth: 2 },
      dataLabels: {
        enabled: true,
        format: `${value}K`,
        align: "left",
        verticalAlign: "middle",
        x: 16,
        crop: false,
        overflow: "allow",
        style: { color: t.ink, fontSize: "18px", fontWeight: "600", textOutline: "none" },
      },
    };
  }
  if (index === minIndex || index === maxIndex) {
    return { y: value, marker: referenceMarker };
  }
  return value;
});

const title = "Daily Active Users · sparkline-basic · javascript · highcharts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / title.length));

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "areaspline",
    backgroundColor: "transparent",
    animation: false,
    margin: [90, 90, 30, 30],
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: title,
    align: "left",
    style: { color: t.ink, fontSize: `${titleFontSize}px`, fontWeight: "600" },
  },
  xAxis: { visible: false },
  yAxis: {
    visible: false,
    startOnTick: false,
    endOnTick: false,
    min: Math.floor(Math.min(...values) - 3),
    max: Math.ceil(Math.max(...values) + 3),
  },
  legend: { enabled: false },
  tooltip: {
    backgroundColor: t.elevatedBg,
    borderWidth: 0,
    style: { color: t.ink, fontSize: "14px" },
    valueSuffix: "K DAU",
  },
  plotOptions: {
    series: { animation: false },
    areaspline: {
      lineWidth: 2.5,
      color: t.palette[0],
      fillColor: {
        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
        stops: [
          [0, Highcharts.color(t.palette[0]).setOpacity(0.28).get()],
          [1, Highcharts.color(t.palette[0]).setOpacity(0.02).get()],
        ],
      },
      marker: { enabled: false },
    },
  },
  series: [{ name: "Daily active users", data: seriesData }],
});
