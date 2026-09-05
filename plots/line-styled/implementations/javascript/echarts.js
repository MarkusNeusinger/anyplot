// anyplot.ai
// line-styled: Styled Line Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 81/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily average temperature by city over one year (day-of-year 1-365, °C).
// Seasonal cycle (annual cosine) plus small monthly/weekly wobbles so the
// four line styles stay distinguishable across many segments, not just
// twelve monthly points.
const monthNames = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const monthStarts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335];

const days = Array.from({ length: 365 }, (_, i) => i + 1);

function seasonalTemp(mean, amplitude, peakDay, day) {
  const annual = amplitude * Math.cos((2 * Math.PI * (day - peakDay)) / 365);
  const wobble =
    1.2 * Math.cos((2 * Math.PI * day) / 9) +
    0.6 * Math.cos((2 * Math.PI * day) / 23);
  return Math.round((mean + annual + wobble) * 10) / 10;
}

const cities = [
  { name: "Berlin", mean: 10, amplitude: 10, peakDay: 208 },
  { name: "Madrid", mean: 17, amplitude: 10, peakDay: 208 },
  { name: "Oslo", mean: 7, amplitude: 11, peakDay: 208 },
  { name: "Cairo", mean: 21.5, amplitude: 7.5, peakDay: 208 },
];
const seriesData = cities.map((city) =>
  days.map((day) => seasonalTemp(city.mean, city.amplitude, city.peakDay, day)),
);

const dashPatterns = ["solid", "dashed", "dotted", [8, 4, 2, 4]];
const lineWidth = 3;

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "Daily Temperature by City · line-styled · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 18, fontWeight: 500 },
  },
  legend: {
    top: 68,
    textStyle: { color: t.inkSoft, fontSize: 15 },
    itemWidth: 28,
    itemHeight: 3,
  },
  grid: { left: 90, right: 60, top: 130, bottom: 70 },
  xAxis: {
    type: "category",
    data: days,
    boundaryGap: false,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      interval: (index, value) => monthStarts.includes(Number(value)),
      formatter: (value) => {
        const day = Number(value);
        let month = monthNames[0];
        for (let i = 0; i < monthStarts.length; i++) {
          if (day >= monthStarts[i]) month = monthNames[i];
        }
        return month;
      },
    },
    axisLine: { onZero: false, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Avg. Temperature (°C)",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.ink, fontSize: 15 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: cities.map((city, i) => ({
    name: city.name,
    type: "line",
    data: seriesData[i],
    lineStyle: { type: dashPatterns[i], width: lineWidth, color: t.palette[i] },
    itemStyle: { color: t.palette[i] },
    symbol: "none",
  })),
});
