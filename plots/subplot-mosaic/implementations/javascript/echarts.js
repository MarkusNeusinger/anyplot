// anyplot.ai
// subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-09-09
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (LCG) -----------------------------------------------
function makeLcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

// --- Data --------------------------------------------------------------
// Panel A: dominant overview — weekly website traffic across a full year.
const weeks = Array.from({ length: 52 }, (_, i) => `W${i + 1}`);
const weeklyVisits = weeks.map((_, i) => {
  const trend = 8200 + i * 42;
  const seasonal = 900 * Math.sin((i / 52) * 4 * Math.PI) + (i > 40 ? 2400 * ((i - 40) / 12) : 0);
  const noise = (rand() - 0.5) * 800;
  return Math.round(trend + seasonal + noise);
});

// Panel B: medium detail — traffic share by device.
const devices = ["Desktop", "Mobile", "Tablet"];
const deviceVisits = [186000, 142000, 31000];

// Panel C: medium detail — session duration vs. pages viewed.
const sessionPoints = Array.from({ length: 45 }, () => {
  const pages = Number((1 + rand() * 9).toFixed(1));
  const duration = Number((pages * 1.7 + rand() * 3.5).toFixed(1));
  return [pages, duration];
});

// Panels D/E/F: small quarterly metric tiles.
const quarters = ["Q1", "Q2", "Q3", "Q4"];
const bounceRate = [52, 47, 44, 41];
const avgSessionMin = [3.1, 3.4, 3.8, 4.2];
const conversionRate = [2.1, 2.4, 2.9, 3.3];

// --- Mosaic layout geometry (percent of container) --------------------------
// Pattern:  AAAA
//           BBCC
//           DEF
// A wide overview on top, two medium detail panels in the middle row,
// three small metric tiles on the bottom row.
const GRID_A = { left: "5%", right: "5%", top: "13%", height: "26%", containLabel: true };
const GRID_B = { left: "5%", width: "42%", top: "46%", height: "22%", containLabel: true };
const GRID_C = { left: "53%", width: "42%", top: "46%", height: "22%", containLabel: true };
const GRID_D = { left: "5%", width: "27%", top: "76%", height: "18%", containLabel: true };
const GRID_E = { left: "36.5%", width: "27%", top: "76%", height: "18%", containLabel: true };
const GRID_F = { left: "68%", width: "27%", top: "76%", height: "18%", containLabel: true };

const tileAxis = {
  axisLabel: { color: t.inkSoft, fontSize: 11 },
  axisLine: { show: false },
  axisTick: { show: false },
};

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  textStyle: { color: t.inkSoft },
  title: [
    {
      text: "subplot-mosaic · javascript · echarts · anyplot.ai",
      left: "center",
      top: "2%",
      textStyle: { color: t.ink, fontSize: 22 },
    },
    { text: "Weekly Website Traffic — Full Year", left: "5%", top: "9%",
      textStyle: { color: t.ink, fontSize: 16, fontWeight: 500 } },
    { text: "Traffic Share by Device", left: "5%", top: "42%",
      textStyle: { color: t.ink, fontSize: 15, fontWeight: 500 } },
    { text: "Session Duration vs. Pages Viewed", left: "53%", top: "42%",
      textStyle: { color: t.ink, fontSize: 15, fontWeight: 500 } },
    { text: "Bounce Rate (%)", left: "5%", top: "72%",
      textStyle: { color: t.inkSoft, fontSize: 13, fontWeight: 500 } },
    { text: "Avg. Session (min)", left: "36.5%", top: "72%",
      textStyle: { color: t.inkSoft, fontSize: 13, fontWeight: 500 } },
    { text: "Conversion Rate (%)", left: "68%", top: "72%",
      textStyle: { color: t.inkSoft, fontSize: 13, fontWeight: 500 } },
  ],
  grid: [GRID_A, GRID_B, GRID_C, GRID_D, GRID_E, GRID_F],
  xAxis: [
    { gridIndex: 0, type: "category", data: weeks, boundaryGap: false,
      axisLabel: { color: t.inkSoft, fontSize: 12, interval: 7 },
      axisLine: { lineStyle: { color: t.inkSoft } }, axisTick: { show: false } },
    { gridIndex: 1, type: "category", data: devices,
      axisLabel: { color: t.inkSoft, fontSize: 13 },
      axisLine: { lineStyle: { color: t.inkSoft } }, axisTick: { show: false } },
    { gridIndex: 2, type: "value", name: "Pages / Session", nameLocation: "middle", nameGap: 28,
      nameTextStyle: { color: t.inkSoft, fontSize: 12 },
      axisLabel: { color: t.inkSoft, fontSize: 12 },
      axisLine: { lineStyle: { color: t.inkSoft } }, axisTick: { show: false },
      splitLine: { lineStyle: { color: t.grid } } },
    { gridIndex: 3, type: "category", data: quarters, ...tileAxis },
    { gridIndex: 4, type: "category", data: quarters, ...tileAxis },
    { gridIndex: 5, type: "category", data: quarters, ...tileAxis },
  ],
  yAxis: [
    { gridIndex: 0, type: "value",
      axisLabel: { color: t.inkSoft, fontSize: 12 },
      axisLine: { lineStyle: { color: t.inkSoft } }, axisTick: { show: false },
      splitLine: { lineStyle: { color: t.grid } } },
    { gridIndex: 1, type: "value",
      axisLabel: { color: t.inkSoft, fontSize: 12 },
      axisLine: { lineStyle: { color: t.inkSoft } }, axisTick: { show: false },
      splitLine: { lineStyle: { color: t.grid } } },
    { gridIndex: 2, type: "value", name: "Duration (min)", nameLocation: "middle", nameGap: 40,
      nameTextStyle: { color: t.inkSoft, fontSize: 12 },
      axisLabel: { color: t.inkSoft, fontSize: 12 },
      axisLine: { lineStyle: { color: t.inkSoft } }, axisTick: { show: false },
      splitLine: { lineStyle: { color: t.grid } } },
    { gridIndex: 3, type: "value", ...tileAxis, splitLine: { show: false } },
    { gridIndex: 4, type: "value", ...tileAxis, splitLine: { show: false } },
    { gridIndex: 5, type: "value", ...tileAxis, splitLine: { show: false } },
  ],
  series: [
    { name: "Weekly Visits", type: "line", xAxisIndex: 0, yAxisIndex: 0,
      data: weeklyVisits, smooth: true, symbol: "none",
      lineStyle: { width: 3 }, areaStyle: { opacity: 0.15 },
      markLine: {
        symbol: "none",
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
        label: { color: t.inkSoft, fontSize: 12, formatter: (p) => `avg ${Math.round(p.value).toLocaleString()}` },
        data: [{ type: "average", name: "Average" }],
      },
      markPoint: {
        symbol: "circle",
        symbolSize: 11,
        itemStyle: { color: t.palette[0], borderColor: t.pageBg, borderWidth: 2 },
        label: { position: "top", color: t.ink, fontSize: 13, fontWeight: 600,
          formatter: (p) => Math.round(p.value).toLocaleString() },
        data: [{ type: "max", name: "Peak" }],
      } },
    { name: "Visits by Device", type: "bar", xAxisIndex: 1, yAxisIndex: 1,
      data: deviceVisits, barWidth: "50%", itemStyle: { opacity: 0.85 } },
    { name: "Sessions", type: "scatter", xAxisIndex: 2, yAxisIndex: 2,
      data: sessionPoints, symbolSize: 12, itemStyle: { opacity: 0.85 } },
    { name: "Bounce Rate", type: "bar", xAxisIndex: 3, yAxisIndex: 3,
      data: bounceRate, barWidth: "55%", itemStyle: { opacity: 0.6 } },
    { name: "Avg Session", type: "line", xAxisIndex: 4, yAxisIndex: 4,
      data: avgSessionMin, smooth: true, symbol: "circle", symbolSize: 8,
      lineStyle: { width: 3, opacity: 0.6 }, itemStyle: { opacity: 0.6 } },
    { name: "Conversion", type: "bar", xAxisIndex: 5, yAxisIndex: 5,
      data: conversionRate, barWidth: "55%", itemStyle: { opacity: 0.6 } },
  ],
});
