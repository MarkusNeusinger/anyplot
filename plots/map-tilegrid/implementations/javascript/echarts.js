// anyplot.ai
// map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// European countries on a hand-placed tile grid approximating their real
// geographic layout, colored by share of electricity from renewable sources.
// [col, row, renewablePct, abbreviation, countryName]
const countries = [
  [0, 0, 85, "IS", "Iceland"],
  [4, 0, 98, "NO", "Norway"],
  [5, 0, 65, "SE", "Sweden"],
  [6, 0, 47, "FI", "Finland"],
  [1, 1, 43, "GB", "United Kingdom"],
  [4, 1, 62, "DK", "Denmark"],
  [0, 2, 38, "IE", "Ireland"],
  [1, 2, 24, "BE", "Belgium"],
  [2, 2, 33, "NL", "Netherlands"],
  [3, 2, 46, "DE", "Germany"],
  [4, 2, 19, "CZ", "Czechia"],
  [5, 2, 17, "PL", "Poland"],
  [2, 3, 27, "FR", "France"],
  [3, 3, 78, "CH", "Switzerland"],
  [4, 3, 80, "AT", "Austria"],
  [5, 3, 15, "HU", "Hungary"],
  [0, 4, 61, "PT", "Portugal"],
  [1, 4, 50, "ES", "Spain"],
  [3, 4, 40, "IT", "Italy"],
  [5, 5, 45, "GR", "Greece"],
];

const colCount = Math.max(...countries.map((c) => c[0])) + 1;
const rowCount = Math.max(...countries.map((c) => c[1])) + 1;
const values = countries.map((c) => c[2]);

// --- Title --------------------------------------------------------------
const title =
  "Renewable Electricity Share, Europe · map-tilegrid · javascript · echarts · anyplot.ai";
const titleFontSize = Math.max(
  14,
  Math.round(22 * Math.min(1, 67 / title.length)),
);

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  tooltip: {
    formatter: (params) => {
      const c = countries[params.dataIndex];
      return `${c[4]} (${c[3]}): ${c[2]}% renewable`;
    },
  },
  grid: { left: 60, right: 60, top: 140, bottom: 200, containLabel: false },
  xAxis: {
    type: "category",
    data: Array.from({ length: colCount }, (_, i) => i),
    show: false,
  },
  yAxis: {
    type: "category",
    data: Array.from({ length: rowCount }, (_, i) => i),
    inverse: true,
    show: false,
  },
  visualMap: {
    type: "continuous",
    min: Math.min(...values),
    max: Math.max(...values),
    orient: "horizontal",
    left: "center",
    bottom: 70,
    itemWidth: 22,
    itemHeight: 260,
    text: ["High", "Low"],
    textGap: 16,
    textStyle: { color: t.inkSoft, fontSize: 16 },
    inRange: { color: t.seq },
    formatter: (value) => `${Math.round(value)}%`,
  },
  series: [
    {
      type: "heatmap",
      data: countries.map((c) => [c[0], c[1], c[2]]),
      itemStyle: {
        borderColor: t.pageBg,
        borderWidth: 8,
        borderRadius: 8,
      },
      label: {
        show: true,
        formatter: (params) => countries[params.dataIndex][3],
        color: "#FFFFFF",
        fontSize: 26,
        fontWeight: 600,
        textBorderColor: "rgba(0,0,0,0.35)",
        textBorderWidth: 3,
      },
      emphasis: {
        itemStyle: { borderColor: t.ink, borderWidth: 3 },
      },
    },
  ],
});
