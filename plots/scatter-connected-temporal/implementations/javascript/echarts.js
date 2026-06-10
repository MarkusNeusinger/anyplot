// anyplot.ai
// scatter-connected-temporal: Connected Scatter Plot with Temporal Path
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 93/100 | Updated: 2026-06-10

const t = window.ANYPLOT_TOKENS;

// Annual CO₂ concentration (ppm) vs. global temperature anomaly (°C), 1980–2023
const years = [
  1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989,
  1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999,
  2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
  2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
  2020, 2021, 2022, 2023
];

const co2 = [
  338.7, 340.1, 341.4, 343.0, 344.4, 345.9, 347.2, 348.9, 351.5, 352.9,
  354.4, 355.6, 356.3, 357.1, 358.9, 360.6, 362.4, 363.8, 366.6, 368.3,
  369.5, 371.1, 373.2, 375.8, 377.5, 379.8, 381.9, 383.8, 385.6, 387.4,
  389.9, 391.6, 394.0, 396.5, 398.6, 400.9, 404.2, 406.5, 408.5, 411.4,
  413.9, 416.2, 418.6, 421.1
];

const tempAnomaly = [
  0.26, 0.32, 0.14, 0.31, 0.16, 0.12, 0.18, 0.33, 0.40, 0.29,
  0.45, 0.41, 0.22, 0.24, 0.31, 0.45, 0.35, 0.46, 0.61, 0.40,
  0.42, 0.54, 0.63, 0.62, 0.54, 0.68, 0.61, 0.66, 0.54, 0.64,
  0.72, 0.61, 0.64, 0.68, 0.75, 0.87, 1.01, 0.92, 0.83, 0.98,
  1.02, 0.85, 0.89, 1.17
];

const keyYears = new Set([1980, 2000, 2010, 2023]);
const labelPos = { 1980: "left", 2000: "top", 2010: "top", 2023: "right" };
const n = years.length;

// Encode temporal index as 3rd dimension for native visualMap coloring
const seriesData = years.map((year, i) => {
  const isKey = keyYears.has(year);
  return {
    value: [co2[i], tempAnomaly[i], i],
    name: String(year),
    symbolSize: isKey ? 16 : 8,
    itemStyle: { borderColor: t.pageBg, borderWidth: 1.5 },
    label: {
      show: isKey,
      formatter: String(year),
      position: labelPos[year] || "top",
      color: t.inkSoft,
      fontSize: 14,
      fontWeight: "bold",
      distance: 10
    }
  };
});

const titleText =
  "Temperature Anomaly vs CO₂ · scatter-connected-temporal · javascript · echarts · anyplot.ai";
const titleFontSize = Math.max(13, Math.round(22 * (67 / titleText.length)));

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  // Native ECharts continuous colormap for temporal gradient — no manual lerp needed
  visualMap: {
    show: false,
    type: "continuous",
    min: 0,
    max: n - 1,
    dimension: 2,
    inRange: { color: t.seq }
  },
  title: {
    text: titleText,
    left: "center",
    top: 18,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: "bold" }
  },
  grid: { left: 110, right: 50, top: 80, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Atmospheric CO₂ (ppm)",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 15 },
    min: 334,
    max: 426,
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } }
  },
  yAxis: {
    type: "value",
    name: "Global Temperature Anomaly (°C)",
    nameLocation: "middle",
    nameGap: 65,
    nameTextStyle: { color: t.ink, fontSize: 15 },
    min: -0.1,
    max: 1.3,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 13,
      formatter: (v) => v.toFixed(1)
    },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } }
  },
  series: [
    {
      type: "line",
      showSymbol: true,
      label: { show: false },
      lineStyle: { width: 2.5, opacity: 0.65 },
      // Arrow at path terminus: ECharts markLine makes time direction unmissable
      markLine: {
        silent: true,
        label: { show: false },
        lineStyle: { color: t.seq[1], width: 2.5, opacity: 0.85 },
        symbol: ["none", "arrow"],
        symbolSize: 14,
        data: [[
          { coord: [co2[n - 2], tempAnomaly[n - 2]] },
          { coord: [co2[n - 1], tempAnomaly[n - 1]] }
        ]]
      },
      data: seriesData
    }
  ]
});
