// anyplot.ai
// bland-altman-basic: Bland-Altman Agreement Plot
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 88/100 | Created: 2026-08-11

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
// mulberry32 PRNG — the browser has no seeded Math.random()
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(42);
function gaussian() {
  const u1 = rand() || 1e-9;
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Systolic blood pressure (mmHg): reference mercury sphygmomanometer vs a new
// automated device, paired readings from the same subjects.
const n = 100;
const referenceBp = [];
const deviceBp = [];
for (let i = 0; i < n; i++) {
  const reference = 90 + rand() * 90;
  const device = reference - 2.5 + gaussian() * 3.5;
  referenceBp.push(reference);
  deviceBp.push(device);
}

const points = referenceBp.map((reference, i) => {
  const device = deviceBp[i];
  const mean = (device + reference) / 2;
  const diff = device - reference;
  return [mean, diff];
});

const diffs = points.map((p) => p[1]);
const bias = diffs.reduce((a, b) => a + b, 0) / diffs.length;
const variance =
  diffs.reduce((a, b) => a + (b - bias) ** 2, 0) / (diffs.length - 1);
const sd = Math.sqrt(variance);
const upperLoA = bias + 1.96 * sd;
const lowerLoA = bias - 1.96 * sd;

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "bland-altman-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 110, right: 150, top: 100, bottom: 90 },
  tooltip: {
    trigger: "item",
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink },
    formatter: (params) =>
      Array.isArray(params.value)
        ? `Mean: ${params.value[0].toFixed(1)} mmHg<br/>Difference: ${params.value[1].toFixed(1)} mmHg`
        : params.name,
  },
  xAxis: {
    type: "value",
    scale: true,
    name: "Mean of Two Methods (mmHg)",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    scale: true,
    name: "Difference: Device − Reference (mmHg)",
    nameLocation: "middle",
    nameGap: 70,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "scatter",
      data: points,
      symbolSize: 14,
      itemStyle: { color: t.palette[0], opacity: 0.6 },
      markLine: {
        symbol: "none",
        silent: true,
        animation: false,
        lineStyle: { width: 2 },
        label: { fontSize: 14, position: "end" },
        data: [
          {
            yAxis: bias,
            lineStyle: { color: t.ink, type: "solid" },
            label: { color: t.ink, formatter: `Bias ${bias.toFixed(1)}` },
          },
          {
            yAxis: upperLoA,
            lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
            label: {
              color: t.inkSoft,
              fontSize: 13,
              formatter: `+1.96 SD  ${upperLoA.toFixed(1)}`,
            },
          },
          {
            yAxis: lowerLoA,
            lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
            label: {
              color: t.inkSoft,
              fontSize: 13,
              formatter: `−1.96 SD  ${lowerLoA.toFixed(1)}`,
            },
          },
        ],
      },
    },
  ],
});
