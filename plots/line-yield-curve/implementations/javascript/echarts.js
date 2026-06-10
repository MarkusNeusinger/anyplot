// anyplot.ai
// line-yield-curve: Yield Curve (Interest Rate Term Structure)
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-10

const t = window.ANYPLOT_TOKENS;

// U.S. Treasury yield curve snapshots — normal, flattening, and inverted
const maturities = [
  { label: "1M",  years: 0.083 },
  { label: "3M",  years: 0.25  },
  { label: "6M",  years: 0.5   },
  { label: "1Y",  years: 1     },
  { label: "2Y",  years: 2     },
  { label: "3Y",  years: 3     },
  { label: "5Y",  years: 5     },
  { label: "7Y",  years: 7     },
  { label: "10Y", years: 10    },
  { label: "20Y", years: 20    },
  { label: "30Y", years: 30    },
];

const curves = [
  {
    date: "Jan 2021",
    yields: [0.07, 0.07, 0.08, 0.09, 0.15, 0.22, 0.47, 0.77, 1.10, 1.74, 1.86],
  },
  {
    date: "Jul 2022",
    yields: [1.87, 2.35, 2.89, 3.15, 3.17, 3.15, 3.13, 3.14, 3.02, 3.32, 3.15],
  },
  {
    date: "Mar 2023",
    yields: [4.57, 4.82, 5.02, 5.01, 4.60, 4.35, 4.05, 3.97, 3.96, 4.12, 3.96],
  },
];

// Build [maturity_years, yield_pct] pairs for each curve
const seriesData = curves.map(c =>
  maturities.map((m, i) => [m.years, c.yields[i]])
);

// Title sizing — scale down if longer than ~67-char baseline
const titleText = "U.S. Treasury Yield Curves · line-yield-curve · javascript · echarts · anyplot.ai";
const titleFontSize = Math.max(14, Math.round(22 * 67 / titleText.length));

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",

  title: {
    text: titleText,
    left: "center",
    top: 24,
    textStyle: {
      color: t.ink,
      fontSize: titleFontSize,
      fontWeight: "bold",
    },
  },

  legend: {
    data: curves.map(c => c.date),
    bottom: 32,
    itemGap: 50,
    icon: "roundRect",
    textStyle: { color: t.inkSoft, fontSize: 16 },
  },

  grid: {
    left: 100,
    right: 70,
    top: 90,
    bottom: 110,
  },

  tooltip: {
    trigger: "axis",
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    borderWidth: 1,
    textStyle: { color: t.ink, fontSize: 14 },
    padding: [10, 14],
    axisPointer: {
      type: "line",
      lineStyle: { color: t.inkSoft, width: 1, type: "dashed" },
    },
    formatter: function(params) {
      const xVal = params[0].value[0];
      const mat = maturities.reduce((prev, cur) =>
        Math.abs(cur.years - xVal) < Math.abs(prev.years - xVal) ? cur : prev
      );
      let html = `<div style="font-weight:600;margin-bottom:6px">${mat.label}</div>`;
      params.forEach(p => {
        html += `${p.marker}&nbsp;${p.seriesName}:&nbsp;<b>${p.value[1].toFixed(2)}%</b><br/>`;
      });
      return html;
    },
  },

  // Log scale reflects true time spacing of the term structure
  xAxis: {
    type: "log",
    logBase: 10,
    min: 0.06,
    max: 35,
    name: "Maturity",
    nameLocation: "middle",
    nameGap: 42,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      formatter: function(val) {
        // Match only the major decade ticks (0.1, 1, 10) via log-distance
        const lv = Math.log10(val);
        if (Math.abs(lv + 1) < 0.05) return "1M";   // 0.1 yr ≈ 1.2 months
        if (Math.abs(lv)     < 0.05) return "1Y";
        if (Math.abs(lv - 1) < 0.05) return "10Y";
        return "";
      },
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
    axisTick: { lineStyle: { color: t.inkSoft } },
  },

  yAxis: {
    type: "value",
    name: "Yield (%)",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    min: 0,
    max: 6,
    interval: 1,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      formatter: "{value}%",
    },
    axisLine: { show: true, lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },

  series: [
    // Normal upward-sloping curve — Jan 2021 (Imprint palette[0], brand green)
    {
      name: curves[0].date,
      type: "line",
      data: seriesData[0],
      lineStyle: { width: 3.5, color: t.palette[0] },
      itemStyle: { color: t.palette[0] },
      symbol: "circle",
      symbolSize: 10,
    },
    // Flattening curve — Jul 2022 (short end rising, long end flat)
    {
      name: curves[1].date,
      type: "line",
      data: seriesData[1],
      lineStyle: { width: 3.5, color: t.palette[1] },
      itemStyle: { color: t.palette[1] },
      symbol: "circle",
      symbolSize: 10,
    },
    // Inverted curve — Mar 2023, with 1Y–10Y inversion zone shaded
    {
      name: curves[2].date,
      type: "line",
      data: seriesData[2],
      lineStyle: { width: 3.5, color: t.palette[2] },
      itemStyle: { color: t.palette[2] },
      symbol: "circle",
      symbolSize: 10,
      markArea: {
        silent: true,
        itemStyle: {
          color: t.palette[2],
          opacity: 0.08,
        },
        data: [[
          { xAxis: 1, name: "Inversion Zone" },
          { xAxis: 10 },
        ]],
        label: {
          show: true,
          position: "insideBottom",
          color: t.inkSoft,
          fontSize: 13,
          fontStyle: "italic",
          formatter: "Inversion Zone",
        },
      },
    },
  ],
});
