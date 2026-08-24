// anyplot.ai
// campbell-basic: Campbell Diagram
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Rotational speed sweep, 0-6000 RPM.
const SPEED_MAX = 6000;
const N = 61;
const speed = Array.from({ length: N }, (_, i) => (i * SPEED_MAX) / (N - 1));

// Natural frequency curves: base frequency plus a mild linear drift with speed
// (gyroscopic stiffening/softening) — some modes rise, some fall.
const modes = [
  { name: "1st Bending", base: 35, drift: 20, color: t.palette[0] },
  { name: "2nd Bending", base: 95, drift: -15, color: t.palette[1] },
  { name: "1st Torsional", base: 145, drift: 10, color: t.palette[2] },
  { name: "2nd Torsional", base: 230, drift: -25, color: t.palette[3] },
  { name: "Axial", base: 270, drift: 5, color: t.palette[5] },
].map((mode) => ({
  ...mode,
  freq: speed.map((s) => mode.base + mode.drift * (s / SPEED_MAX)),
}));

// Engine order excitation lines: straight lines from the origin, slope =
// order / 60 (RPM -> Hz).
const orders = [1, 2, 3].map((order) => ({
  name: `${order}x`,
  freq: speed.map((s) => (order * s) / 60),
}));

// Critical speeds: RPM where an engine order line crosses a natural
// frequency curve, found by scanning for a sign change and interpolating.
const criticalSpeeds = [];
orders.forEach((order) => {
  modes.forEach((mode) => {
    for (let i = 1; i < N; i++) {
      const prevDiff = order.freq[i - 1] - mode.freq[i - 1];
      const currDiff = order.freq[i] - mode.freq[i];
      if (prevDiff === 0 || prevDiff * currDiff < 0) {
        const frac = prevDiff === 0 ? 0 : prevDiff / (prevDiff - currDiff);
        const s = speed[i - 1] + frac * (speed[i] - speed[i - 1]);
        const f = order.freq[i - 1] + frac * (order.freq[i] - order.freq[i - 1]);
        criticalSpeeds.push([s, f]);
      }
    }
  });
});

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "campbell-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 90, right: 90, top: 110, bottom: 150, containLabel: true },
  legend: {
    bottom: 10,
    type: "scroll",
    textStyle: { color: t.inkSoft, fontSize: 14 },
    itemWidth: 20,
    itemHeight: 12,
  },
  xAxis: {
    type: "value",
    name: "Rotational Speed (RPM)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    max: SPEED_MAX,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Natural Frequency (Hz)",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 0,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    ...modes.map((mode) => ({
      name: mode.name,
      type: "line",
      data: speed.map((s, i) => [s, mode.freq[i]]),
      showSymbol: false,
      smooth: 0.2,
      lineStyle: { width: 3.5, color: mode.color },
      itemStyle: { color: mode.color },
    })),
    ...orders.map((order) => ({
      name: order.name,
      type: "line",
      data: speed.map((s, i) => [s, order.freq[i]]),
      showSymbol: false,
      lineStyle: { width: 2, type: "dashed", color: t.ink, opacity: 0.55 },
      itemStyle: { color: t.ink },
      endLabel: {
        show: true,
        formatter: "{a}",
        color: t.ink,
        fontSize: 14,
      },
    })),
    {
      name: "Critical Speed",
      type: "scatter",
      data: criticalSpeeds,
      symbol: "diamond",
      symbolSize: 18,
      itemStyle: {
        color: t.amber,
        borderColor: t.ink,
        borderWidth: 1.5,
      },
      z: 10,
    },
  ],
});
