// anyplot.ai
// bar-diverging-likert: Likert Scale Diverging Bar Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-08-24
//# anyplot-orientation: landscape

const THEME = window.ANYPLOT_THEME;
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Employee engagement survey, 5-point Likert scale, percentages sum to 100 per
// question. Pre-sorted by net agreement (Agree + Strongly Agree - Disagree -
// Strongly Disagree), highest net agreement first.
const rows = [
  { question: "I'd recommend this company as a great place to work", sd: 3, d: 7, n: 10, a: 45, sa: 35 },
  { question: "I understand how my role contributes to company goals", sd: 2, d: 8, n: 15, a: 42, sa: 33 },
  { question: "I feel valued by my manager", sd: 4, d: 9, n: 12, a: 40, sa: 35 },
  { question: "I have the resources I need to do my job well", sd: 5, d: 12, n: 18, a: 38, sa: 27 },
  { question: "I see a clear path for career growth here", sd: 8, d: 18, n: 22, a: 32, sa: 20 },
  { question: "I trust leadership to make the right decisions during organizational change", sd: 25, d: 9, n: 8, a: 15, sa: 43 },
  { question: "I receive regular, constructive feedback", sd: 9, d: 19, n: 24, a: 31, sa: 17 },
  { question: "Leadership communicates changes effectively", sd: 12, d: 23, n: 20, a: 28, sa: 17 },
  { question: "I feel comfortable raising concerns to leadership", sd: 15, d: 22, n: 18, a: 27, sa: 18 },
  { question: "I'm satisfied with our compensation and benefits", sd: 18, d: 27, n: 15, a: 25, sa: 15 },
];

const categories = rows.map((r) => r.question);

// --- Diverging red-to-blue palette, muted neutral -----------------------------
const RED = "#AE3030"; // Imprint matte red — semantic anchor for disagreement
// Precomputed opaque tint (RED blended 55% over white) — a plain hex, not an
// alpha-blend over the mount background, so it stays pixel-identical across
// the light (#FAF8F1) and dark (#1A1A17) themes.
const RED_SOFT = "#D28D8D";
const BLUE = "#4467A3"; // Imprint blue — agreement
const BLUE_SOFT = "#98ABCC"; // Precomputed opaque tint (BLUE blended 55% over white)
// ANYPLOT_TOKENS has no "muted" key (only pageBg/elevatedBg/ink/inkSoft/grid/
// palette/amber/seq/div) — hardcode the theme-adaptive muted anchor from
// prompts/default-style-guide.md "Semantic anchors".
const NEUTRAL = THEME === "dark" ? "#A8A79F" : "#6B6A63";

const LABEL_STYLE = {
  fontSize: "13px",
  fontWeight: "600",
  color: "#FFFFFF",
  textOutline: "1px contrast",
};

// Highcharts stacks each subsequent same-signed series CLOSER to zero than the
// one before it, so the array order (per sign) is farthest-from-zero first:
// Strongly D/A, then Disagree/Agree, then the Neutral half last (closest to
// the center, where the two Neutral halves meet). legendIndex keeps the
// legend in the natural SD -> D -> Neutral -> A -> SA reading order.
const series = [
  {
    name: "Strongly Disagree",
    legendIndex: 0,
    data: rows.map((r) => ({ y: -r.sd, pct: r.sd })),
    color: RED,
    dataLabels: {
      formatter: function () {
        return Math.abs(this.y) >= 6 ? this.point.pct + "%" : null;
      },
    },
  },
  {
    name: "Strongly Agree",
    legendIndex: 4,
    data: rows.map((r) => ({ y: r.sa, pct: r.sa })),
    color: BLUE,
    dataLabels: {
      formatter: function () {
        return Math.abs(this.y) >= 6 ? this.point.pct + "%" : null;
      },
    },
  },
  {
    name: "Disagree",
    legendIndex: 1,
    data: rows.map((r) => ({ y: -r.d, pct: r.d })),
    color: RED_SOFT,
    dataLabels: {
      formatter: function () {
        return Math.abs(this.y) >= 6 ? this.point.pct + "%" : null;
      },
    },
  },
  {
    name: "Agree",
    legendIndex: 3,
    data: rows.map((r) => ({ y: r.a, pct: r.a })),
    color: BLUE_SOFT,
    dataLabels: {
      formatter: function () {
        return Math.abs(this.y) >= 6 ? this.point.pct + "%" : null;
      },
    },
  },
  {
    id: "neutral-left",
    name: "Neutral",
    data: rows.map((r) => ({ y: -r.n / 2, pct: r.n })),
    color: NEUTRAL,
    showInLegend: false,
    dataLabels: { enabled: false },
  },
  {
    id: "neutral-right",
    name: "Neutral",
    legendIndex: 2,
    data: rows.map((r) => ({ y: r.n / 2, pct: r.n })),
    color: NEUTRAL,
    dataLabels: {
      formatter: function () {
        return this.point.pct >= 8 ? this.point.pct + "%" : null;
      },
    },
  },
];

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "bar",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "bar-diverging-likert · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Employee engagement survey · sorted by net agreement",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    categories,
    reversed: true,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    min: -100,
    max: 100,
    tickInterval: 25,
    gridLineColor: t.grid,
    title: {
      text: "Share of responses",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      formatter: function () {
        return Math.abs(this.value) + "%";
      },
    },
    plotLines: [{ value: 0, width: 2, color: t.inkSoft, zIndex: 5 }],
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    shared: true,
    formatter: function () {
      const rowIndex = this.points[0].point.index;
      const r = rows[rowIndex];
      return (
        `<b>${r.question}</b><br/>` +
        `Strongly Disagree: ${r.sd}%<br/>` +
        `Disagree: ${r.d}%<br/>` +
        `Neutral: ${r.n}%<br/>` +
        `Agree: ${r.a}%<br/>` +
        `Strongly Agree: ${r.sa}%`
      );
    },
  },
  plotOptions: {
    series: {
      animation: false,
      stacking: "normal",
      dataLabels: { enabled: true, inside: true, style: LABEL_STYLE },
    },
    bar: { groupPadding: 0.12, pointPadding: 0.02, borderWidth: 0, borderRadius: 2 },
  },
  series,
});
