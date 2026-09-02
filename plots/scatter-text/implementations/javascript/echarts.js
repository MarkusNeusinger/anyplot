// anyplot.ai
// scatter-text: Scatter Plot with Text Labels Instead of Points
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-02
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// World cities: average annual temperature vs. average annual rainfall,
// grouped by continent. Each point is rendered as its city name only.
const REGIONS = [
  {
    name: "Africa",
    cities: [
      ["Cairo", 21.4, 25],
      ["Lagos", 26.9, 1700],
      ["Nairobi", 19.0, 800],
      ["Cape Town", 17.0, 515],
      ["Casablanca", 17.7, 400],
    ],
  },
  {
    name: "Asia",
    cities: [
      ["Tokyo", 15.4, 1520],
      ["Singapore", 27.0, 2340],
      ["Mumbai", 27.2, 2200],
      ["Bangkok", 28.3, 1500],
      ["Seoul", 12.5, 1370],
      ["Riyadh", 26.0, 100],
    ],
  },
  {
    name: "Europe",
    cities: [
      ["London", 11.3, 600],
      ["Paris", 12.3, 640],
      ["Berlin", 9.8, 570],
      ["Madrid", 14.8, 430],
      ["Moscow", 5.8, 700],
      ["Rome", 13.5, 990],
    ],
  },
  {
    name: "Americas",
    cities: [
      ["New York", 12.9, 1200],
      ["Mexico City", 16.0, 800],
      ["Sao Paulo", 19.2, 1400],
      ["Toronto", 9.4, 830],
      ["Lima", 18.9, 15],
      ["Buenos Aires", 20.2, 1050],
    ],
  },
  {
    name: "Oceania",
    cities: [
      ["Sydney", 17.9, 1200],
      ["Auckland", 15.5, 1240],
      ["Perth", 18.6, 730],
    ],
  },
];

// Pixel offsets [dx, dy] for labels that would otherwise collide with a
// neighbor or sit on the y=0 gridline (screen y grows downward).
const LABEL_OFFSETS = {
  Nairobi: [20, -18],
  Perth: [-20, 18],
  Berlin: [-20, 0],
  London: [20, 0],
  Lima: [0, -22],
  Cairo: [0, -22],
};

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Title (fontsize scales down for long titles, see plot-generator.md) ---
const TITLE = "scatter-text · javascript · echarts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / TITLE.length));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: TITLE,
    left: "center",
    top: 34,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  legend: {
    top: 96,
    left: "center",
    itemWidth: 16,
    itemHeight: 16,
    textStyle: { color: t.inkSoft, fontSize: 16 },
  },
  tooltip: {
    trigger: "item",
    formatter: (p) =>
      `${p.marker}${p.data.name}<br/>Temperature: ${p.data.value[0]}°C<br/>Rainfall: ${p.data.value[1]} mm`,
  },
  grid: { left: 130, right: 80, top: 190, bottom: 110 },
  xAxis: {
    type: "value",
    name: "Average Temperature (°C)",
    nameLocation: "middle",
    nameGap: 46,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    min: 0,
    max: 32,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Average Annual Rainfall (mm)",
    nameLocation: "middle",
    nameGap: 80,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    min: 0,
    max: 2500,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: REGIONS.map((region, i) => ({
    name: region.name,
    type: "scatter",
    symbol: "circle",
    symbolSize: 0,
    data: region.cities.map(([city, temp, rain]) => {
      const offset = LABEL_OFFSETS[city];
      return {
        name: city,
        value: [temp, rain],
        ...(offset ? { label: { position: offset } } : {}),
      };
    }),
    label: {
      show: true,
      formatter: "{b}",
      position: "inside",
      color: t.palette[i],
      fontSize: 16,
      fontWeight: 600,
      textBorderColor: t.pageBg,
      textBorderWidth: 3,
    },
    emphasis: {
      label: { fontSize: 19 },
    },
  })),
});
