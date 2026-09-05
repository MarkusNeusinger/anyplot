// anyplot.ai
// line-markers: Line Plot with Markers
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Michaelis-Menten enzyme kinetics: v = Vmax * [S] / (Km + [S]), plus a small
// deterministic measurement jitter (fixed-seed LCG — no Math.random in browser).
let seed = 42;
function lcgNoise(scale) {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return (seed / 0x7fffffff - 0.5) * 2 * scale;
}

const substrate = [0.5, 1, 2, 3, 5, 8, 12, 18, 25, 35, 45];

function michaelisMenten(vmax, km) {
  return substrate.map((s) => {
    const rate = (vmax * s) / (km + s);
    return Math.round((rate + lcgNoise(2.2)) * 10) / 10;
  });
}

const wildType = michaelisMenten(98, 4.5);
const mutant = michaelisMenten(65, 14);

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "Enzyme Kinetics · line-markers · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Wild-type", "Mutant"],
    top: 76,
    textStyle: { color: t.inkSoft, fontSize: 16 },
    itemWidth: 24,
    itemHeight: 14,
  },
  grid: { left: 100, right: 70, top: 150, bottom: 100 },
  xAxis: {
    type: "value",
    name: "Substrate Concentration (mM)",
    nameLocation: "middle",
    nameGap: 46,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    min: 0,
    max: 46,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Reaction Rate (µM/min)",
    nameLocation: "middle",
    nameGap: 64,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    min: 0,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Wild-type",
      type: "line",
      data: substrate.map((s, i) => [s, wildType[i]]),
      symbol: "circle",
      symbolSize: 16,
      lineStyle: { width: 3.5, color: t.palette[0] },
      itemStyle: { color: t.palette[0], borderColor: t.pageBg, borderWidth: 2 },
    },
    {
      name: "Mutant",
      type: "line",
      data: substrate.map((s, i) => [s, mutant[i]]),
      symbol: "diamond",
      symbolSize: 18,
      lineStyle: { width: 3.5, color: t.palette[1] },
      itemStyle: { color: t.palette[1], borderColor: t.pageBg, borderWidth: 2 },
    },
  ],
});
