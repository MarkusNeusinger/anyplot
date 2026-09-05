// anyplot.ai
// dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-05
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
// ANYPLOT_TOKENS has no "muted" field — derive the theme-adaptive muted-ink
// anchor locally (see prompts/default-style-guide.md "Theme-adaptive Chrome").
const inkMuted = t.theme === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ---------------------------------------
const total = 100;
const gridCols = 10;
const gridRows = 10;

// Sentiment/polarity semantic exception: satisfied -> green, dissatisfied ->
// red, neutral -> the theme-adaptive muted anchor (default-style-guide.md
// "Color Philosophy" -> "Semantic exception").
const categories = [
  { name: "Satisfied", count: 47, color: t.palette[0] },
  { name: "Neutral", count: 31, color: inkMuted },
  { name: "Dissatisfied", count: 22, color: t.palette[4] },
];

const majority = categories.reduce((a, b) => (b.count > a.count ? b : a));
const majorityPct = Math.round((majority.count / total) * 100);

// Extra breathing room between dots (uniform size is a spec requirement, so
// the gutter comes from spacing the grid coordinates, not shrinking dots).
const gutter = 1.12;

// Fill dots left-to-right, top-to-bottom, sequentially across categories.
let cursor = 0;
const series = categories.map((cat) => {
  const data = [];
  for (let i = 0; i < cat.count; i += 1, cursor += 1) {
    data.push([
      (cursor % gridCols) * gutter,
      Math.floor(cursor / gridCols) * gutter,
    ]);
  }
  const pct = Math.round((cat.count / total) * 100);
  return {
    name: cat.name,
    color: cat.color,
    // Arbitrary user data slot (Highcharts "custom" option) so the legend
    // formatter and tooltip below can surface count/pct without re-parsing
    // the series name.
    custom: { count: cat.count, pct },
    // Subtle radial gradient (via Highcharts' own Color.brighten helper)
    // gives the flat circles a touch of depth while keeping uniform size.
    marker: {
      fillColor: {
        radialGradient: { cx: 0.35, cy: 0.35, r: 0.75 },
        stops: [
          [0, Highcharts.color(cat.color).brighten(0.3).get()],
          [1, cat.color],
        ],
      },
    },
    data,
  };
});

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "dot-matrix-proportional · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: `Customer satisfaction survey · 100 respondents, one dot each — ${majority.name} leads at ${majorityPct}%`,
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: -0.65,
    max: (gridCols - 1) * gutter + 0.65,
    visible: false,
  },
  yAxis: {
    min: -0.65,
    max: (gridRows - 1) * gutter + 0.65,
    reversed: true,
    title: { text: null },
    visible: false,
  },
  legend: {
    align: "center",
    verticalAlign: "bottom",
    symbolRadius: 6,
    useHTML: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
    // Highcharts-distinctive touch: useHTML legend items with an inline
    // mini count-bar next to each label, instead of plain text.
    labelFormatter: function () {
      const { count, pct } = this.userOptions.custom;
      const barWidth = Math.max(4, Math.round((pct / 100) * 60));
      return (
        `<span style="display:inline-flex;align-items:center;gap:8px;color:${t.inkSoft};font-size:14px;">` +
        `<span>${this.name}</span>` +
        `<span style="display:inline-block;width:60px;height:6px;border-radius:3px;background:${t.grid};overflow:hidden;">` +
        `<span style="display:block;width:${barWidth}px;height:100%;background:${this.color};"></span>` +
        `</span>` +
        `<span style="font-variant-numeric:tabular-nums;">${count} (${pct}%)</span>` +
        `</span>`
      );
    },
  },
  tooltip: {
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    style: { color: t.ink, fontSize: "13px" },
    headerFormat: "",
    pointFormatter: function () {
      const { count, pct } = this.series.userOptions.custom;
      return `${this.series.name}: ${count} (${pct}%)`;
    },
  },
  plotOptions: {
    series: {
      animation: false,
      marker: {
        radius: 36,
        symbol: "circle",
        lineWidth: 2,
        lineColor: t.pageBg,
      },
      shadow: { color: "rgba(0,0,0,0.18)", offsetX: 0, offsetY: 2, width: 4 },
      states: { hover: { halo: { size: 0 } } },
    },
  },
  series,
});
