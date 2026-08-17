// anyplot.ai
// area-stacked: Stacked Area Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-17

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Electricity consumption by sector for a regional utility service area,
// 2010-2024 (TWh, illustrative). Ranking follows real-world sector order
// (residential and commercial are the two largest loads, industrial third);
// transportation is the small-but-fast-growing EV-charging load.
const years = Array.from({ length: 15 }, (_, i) => String(2010 + i));

const residential = [700, 695, 715, 690, 725, 735, 705, 730, 745, 738, 750, 758, 748, 765, 780];
const commercial = [615, 620, 628, 632, 640, 645, 652, 658, 665, 670, 676, 683, 690, 697, 705];
const industrial = [480, 475, 490, 485, 495, 488, 500, 495, 505, 498, 508, 502, 510, 505, 515];
const transportation = [5, 6, 7, 9, 11, 14, 18, 23, 30, 39, 51, 65, 82, 98, 115];

// Order largest-to-smallest so the stack reads largest-at-bottom.
const series = [
  { name: "Residential", data: residential },
  { name: "Commercial", data: commercial },
  { name: "Industrial", data: industrial },
  { name: "Transportation", data: transportation },
];

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "area-stacked · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 28, fontWeight: 500 },
  },
  tooltip: { trigger: "axis" },
  legend: {
    bottom: 10,
    textStyle: { color: t.inkSoft, fontSize: 14 },
    itemWidth: 18,
    itemHeight: 12,
  },
  grid: { left: 90, right: 60, top: 110, bottom: 90 },
  xAxis: {
    type: "category",
    data: years,
    boundaryGap: false,
    name: "Year",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: 0,
    name: "Electricity Consumption (TWh)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: series.map((s, i) => {
    const isTransportation = s.name === "Transportation";
    return {
      name: s.name,
      type: "line",
      stack: "total",
      smooth: 0.2,
      showSymbol: false,
      // Transportation carries the story of this dataset (EV-charging load
      // growing ~23x over the period) — a bolder stroke pulls the eye to it
      // even though its absolute magnitude is the smallest of the four.
      lineStyle: { width: isTransportation ? 3.5 : 2, color: t.palette[i] },
      itemStyle: { color: t.palette[i] },
      // Full opacity on the (visually thin) Transportation band keeps it crisp
      // against the Industrial band beneath it; the other bands stay
      // semi-transparent so the boundary lines between them read clearly.
      areaStyle: { color: t.palette[i], opacity: isTransportation ? 1 : 0.82 },
      emphasis: { focus: "series" },
      data: s.data,
      ...(isTransportation && {
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { color: t.palette[i], type: "dashed", width: 1.5, opacity: 0.7 },
          label: {
            color: t.ink,
            fontSize: 12,
            fontWeight: 600,
            formatter: "EV adoption accelerates",
            position: "insideEndTop",
          },
          data: [{ xAxis: "2018" }],
        },
      }),
    };
  }),
});
