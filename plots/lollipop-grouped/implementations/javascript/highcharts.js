// anyplot.ai
// lollipop-grouped: Grouped Lollipop Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly product-line revenue ($M) by region, sorted by total descending.
const categories = ["South", "North", "West", "East"];
const seriesNames = ["Solar", "Wind", "Storage"];
const revenueByProduct = {
  Solar: [58, 42, 61, 35],
  Wind: [33, 51, 29, 47],
  Storage: [24, 18, 15, 21],
};

// Side-by-side offset for lollipops within a group.
const offsetStep = 0.22;
const seriesOffsets = seriesNames.map((_, i) => (i - (seriesNames.length - 1) / 2) * offsetStep);

// Standout data point (single highest value) gets a subtle focal-point
// emphasis — a larger radius and a bolder ink ring — to give the chart a
// point of visual hierarchy beyond the raw category comparison.
const globalMax = Math.max(...seriesNames.flatMap((name) => revenueByProduct[name]));

// Each lollipop is a 2-point segment (baseline -> value) followed by a null
// gap, so a single "line" series draws every stem for that product line
// without connecting across categories.
const series = seriesNames.map((name, si) => {
  const x0 = seriesOffsets[si];
  const data = [];
  categories.forEach((_, ci) => {
    const x = ci + x0;
    const value = revenueByProduct[name][ci];
    const isFocal = value === globalMax;
    data.push({ x, y: 0, marker: { enabled: false } });
    data.push({
      x,
      y: value,
      marker: isFocal ? { enabled: true, radius: 10, lineWidth: 3, lineColor: t.ink } : { enabled: true },
    });
    data.push({ x, y: null });
  });
  return {
    name,
    type: "line",
    data,
    color: t.palette[si],
    lineWidth: 2.5,
    marker: { enabled: true, radius: 7, symbol: "circle", lineColor: t.pageBg, lineWidth: 1.5 },
  };
});

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: { backgroundColor: "transparent", animation: false, style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "lollipop-grouped · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "26px", fontWeight: "700" },
  },
  xAxis: {
    categories,
    min: -0.5,
    max: categories.length - 0.5,
    startOnTick: false,
    endOnTick: false,
    tickPositions: categories.map((_, ci) => ci),
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Region", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: {
    min: 0,
    title: { text: "Revenue ($M)", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    formatter: function () {
      if (this.y === 0 || this.y === null) return false;
      const category = categories[Math.round(this.x)];
      return `<b>${this.series.name}</b><br/>${category}: $${this.y}M`;
    },
  },
  plotOptions: {
    series: { animation: false, enableMouseTracking: true },
  },
  series,
});
