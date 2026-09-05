// anyplot.ai
// elbow-curve: Elbow Curve for K-Means Clustering
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Customer segmentation: within-cluster sum of squares (inertia) for k-means
// run on RFM (recency, frequency, monetary) features across 500 customers.
const kValues = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const inertia = [18200, 9800, 6200, 4100, 3400, 2950, 2650, 2420, 2250, 2120];
const elbowK = 4;
const elbowIndex = kValues.indexOf(elbowK);

const seriesData = kValues.map((k, i) => ({
  value: [k, inertia[i]],
  itemStyle:
    k === elbowK
      ? { color: t.palette[2], borderColor: t.pageBg, borderWidth: 2 }
      : { color: t.palette[0], borderColor: t.pageBg, borderWidth: 2 },
  symbolSize: k === elbowK ? 22 : 14,
}));

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "elbow-curve · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 130, right: 80, top: 100, bottom: 110, containLabel: false },
  tooltip: {
    trigger: "axis",
    formatter: (params) => {
      const [k, value] = params[0].value;
      return `k = ${k}<br/>inertia = ${value.toLocaleString("en-US")}`;
    },
  },
  xAxis: {
    type: "value",
    min: 1,
    max: 10,
    interval: 1,
    name: "Number of Clusters (k)",
    nameLocation: "middle",
    nameGap: 46,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    axisLabel: { color: t.inkSoft, fontSize: 15 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Inertia (within-cluster sum of squares)",
    nameLocation: "middle",
    nameGap: 90,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 15,
      formatter: (v) => v.toLocaleString("en-US"),
    },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "line",
      data: seriesData,
      lineStyle: { color: t.palette[0], width: 3.5 },
      symbol: "circle",
      smooth: 0.25,
      z: 2,
      markLine: {
        symbol: "none",
        silent: true,
        lineStyle: { color: t.inkSoft, type: "dashed", width: 2 },
        label: {
          formatter: `Elbow · k = ${elbowK}`,
          position: "end",
          rotate: 0,
          align: "left",
          offset: [8, -10],
          color: t.ink,
          fontSize: 16,
        },
        data: [{ xAxis: elbowK }],
      },
    },
  ],
});
