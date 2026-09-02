// anyplot.ai
// range-interval: Range Interval Chart
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic): Berlin monthly temperature range (°C) -
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const lowTemps = [-3, -2, 1, 4, 9, 12, 14, 13, 10, 6, 2, -1];
const highTemps = [3, 5, 10, 15, 20, 23, 25, 24, 20, 14, 7, 4];

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Range bar geometry (custom renderItem — draws [low, high] directly) ----
// A stacked-bar "invisible base" trick breaks once low is negative, because
// ECharts accumulates positive and negative stack values separately instead
// of letting a negative base shift a positive bar downward. Drawing the rect
// explicitly from the low to the high coordinate avoids that edge case.
function renderRangeBar(params, api) {
  const categoryIndex = api.value(0);
  const low = api.coord([categoryIndex, api.value(1)]);
  const high = api.coord([categoryIndex, api.value(2)]);
  const halfWidth = api.size([1, 0])[0] * 0.225;
  const shape = echarts.graphic.clipRectByRect(
    { x: low[0] - halfWidth, y: high[1], width: halfWidth * 2, height: low[1] - high[1] },
    { x: params.coordSys.x, y: params.coordSys.y, width: params.coordSys.width, height: params.coordSys.height }
  );
  return shape && { type: "rect", shape, style: api.style() };
}

// --- Option -------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "Berlin Monthly Temperature Range · range-interval · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 17, fontWeight: 500 },
  },
  grid: { left: 90, right: 60, top: 100, bottom: 70 },
  xAxis: {
    type: "category",
    data: months,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Temperature (°C)",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.ink, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}°" },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Temperature range",
      type: "custom",
      renderItem: renderRangeBar,
      data: months.map((_, i) => [i, lowTemps[i], highTemps[i]]),
      itemStyle: { color: t.palette[0], borderRadius: 3 },
      z: 2,
    },
    {
      name: "Low / high",
      type: "scatter",
      data: lowTemps,
      symbolSize: 9,
      itemStyle: { color: t.ink, borderColor: t.pageBg, borderWidth: 1.5 },
      z: 3,
    },
    {
      name: "Low / high",
      type: "scatter",
      data: highTemps,
      symbolSize: 9,
      itemStyle: { color: t.ink, borderColor: t.pageBg, borderWidth: 1.5 },
      z: 3,
    },
  ],
});
