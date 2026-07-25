// anyplot.ai
// stem-basic: Basic Stem Plot
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Impulse response of a damped second-order system: y[n] = exp(-decay*n) * cos(omega*n)
const N = 40;
const decay = 0.12;
const omega = 0.5;
const indices = [];
const values = [];
for (let n = 0; n < N; n++) {
  indices.push(String(n));
  values.push(Number((Math.exp(-decay * n) * Math.cos(omega * n)).toFixed(4)));
}
const peakIndex = values.indexOf(Math.max(...values));

// Peak marker keeps the same 16px size (spec requires consistent marker size)
// but gets a soft halo + glow so the eye lands on the dominant sample first.
const scatterData = values.map((v, i) =>
  i === peakIndex
    ? {
        value: v,
        itemStyle: {
          color: t.palette[0],
          borderColor: t.pageBg,
          borderWidth: 3,
          shadowBlur: 18,
          shadowColor: t.palette[0],
        },
      }
    : v,
);

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "stem-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 26 },
  },
  tooltip: {
    trigger: "axis",
    axisPointer: { type: "line" },
    formatter: (params) => {
      const p = params.find((d) => d.seriesType === "scatter") ?? params[0];
      return `Sample n = ${p.axisValueLabel}<br/>Amplitude = ${p.value.toFixed(4)}`;
    },
  },
  grid: { left: 100, right: 60, top: 100, bottom: 90 },
  xAxis: {
    type: "category",
    data: indices,
    name: "Sample Index (n)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 4 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Amplitude",
    nameLocation: "middle",
    nameGap: 65,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "stem",
      type: "bar",
      data: values,
      barWidth: 3,
      barGap: "-100%",
      itemStyle: { color: t.palette[0] },
      silent: true,
      markLine: {
        silent: true,
        symbol: "none",
        lineStyle: { color: t.inkSoft, width: 1.5, type: "solid" },
        label: { show: false },
        data: [{ yAxis: 0 }],
      },
      z: 2,
    },
    {
      name: "sample value",
      type: "scatter",
      data: scatterData,
      symbolSize: 16,
      itemStyle: { color: t.palette[0] },
      z: 3,
    },
  ],
});
