// anyplot.ai
// range-interval: Range Interval Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic): Berlin monthly temperature range (°C) -
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const lowTemps = [-3, -2, 1, 4, 9, 12, 14, 13, 10, 6, 2, -1];
const highTemps = [3, 5, 10, 15, 20, 23, 25, 24, 20, 14, 7, 4];

// Widest low-to-high span gets a callout label — a focal point beyond plain
// chronological ordering.
const rangeWidths = months.map((_, i) => highTemps[i] - lowTemps[i]);
const widestIndex = rangeWidths.indexOf(Math.max(...rangeWidths));

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
  if (!shape) return;
  const rect = { type: "rect", shape, style: api.style() };
  if (params.dataIndex !== widestIndex) return rect;
  const label = {
    type: "text",
    style: {
      text: `Widest range (${rangeWidths[widestIndex]}°C)`,
      x: low[0],
      y: high[1] - 14,
      fill: t.inkSoft,
      fontSize: 12,
      align: "center",
      verticalAlign: "bottom",
    },
    z2: 10,
  };
  return { type: "group", children: [rect, label] };
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
      data: months.flatMap((_, i) => [
        [i, lowTemps[i]],
        [i, highTemps[i]],
      ]),
      symbolSize: 9,
      itemStyle: { color: t.ink, borderColor: t.pageBg, borderWidth: 1.5 },
      z: 3,
    },
  ],
});
