// anyplot.ai
// parallel-categories-basic: Basic Parallel Categories Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Customer journey: acquisition channel -> product category -> purchase outcome.
// ECharts has no dedicated "parallel categories" chart (that's a numeric
// parallel-coordinates variant); a Sankey diagram is its native equivalent for
// width-proportional ribbons flowing between categorical stages.
const CHANNELS = [
  "Organic Search",
  "Paid Ads",
  "Social Media",
  "Email Campaign",
];
const CATEGORIES = ["Electronics", "Apparel", "Home & Garden"];
const OUTCOMES = ["Purchased", "Abandoned"];

// channel -> category visit counts
const channelToCategory = [
  ["Organic Search", "Electronics", 420],
  ["Organic Search", "Apparel", 280],
  ["Organic Search", "Home & Garden", 150],
  ["Paid Ads", "Electronics", 380],
  ["Paid Ads", "Apparel", 210],
  ["Paid Ads", "Home & Garden", 90],
  ["Social Media", "Electronics", 160],
  ["Social Media", "Apparel", 340],
  ["Social Media", "Home & Garden", 120],
  ["Email Campaign", "Electronics", 90],
  ["Email Campaign", "Apparel", 130],
  ["Email Campaign", "Home & Garden", 60],
];

// category -> outcome counts
const categoryToOutcome = [
  ["Electronics", "Purchased", 720],
  ["Electronics", "Abandoned", 330],
  ["Apparel", "Purchased", 520],
  ["Apparel", "Abandoned", 440],
  ["Home & Garden", "Purchased", 230],
  ["Home & Garden", "Abandoned", 190],
];

// Color by first dimension (source channel); category nodes stay neutral so the
// channel provenance reads through the ribbons, outcome nodes carry the
// pass/fail semantic (Purchased -> brand green, Abandoned -> matte red).
const channelColor = Object.fromEntries(
  CHANNELS.map((name, i) => [name, t.palette[i]]),
);
const outcomeColor = { Purchased: t.palette[0], Abandoned: t.palette[4] };

const nodes = [
  ...CHANNELS.map((name) => ({
    name,
    itemStyle: { color: channelColor[name] },
  })),
  ...CATEGORIES.map((name) => ({
    name,
    itemStyle: {
      color: t.elevatedBg,
      borderColor: t.inkSoft,
      borderWidth: 1.5,
    },
  })),
  ...OUTCOMES.map((name) => ({
    name,
    itemStyle: { color: outcomeColor[name] },
  })),
];

// First stage ribbons take the channel (source) color; second stage ribbons
// take the outcome (target) color, so the terminal green/red split reads
// clearly instead of fading into the neutral category-node color.
const links = [
  ...channelToCategory.map(([source, target, value]) => ({
    source,
    target,
    value,
    lineStyle: { color: channelColor[source], opacity: 0.5, curveness: 0.5 },
  })),
  ...categoryToOutcome.map(([source, target, value]) => ({
    source,
    target,
    value,
    lineStyle: { color: outcomeColor[target], opacity: 0.5, curveness: 0.5 },
  })),
];

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "parallel-categories-basic · javascript · echarts · anyplot.ai",
    subtext:
      "Customer journey: acquisition channel → product category → purchase outcome",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 600 },
    subtextStyle: { color: t.inkSoft, fontSize: 16 },
  },
  tooltip: { trigger: "item" },
  series: [
    {
      type: "sankey",
      left: 40,
      right: 220,
      top: 130,
      bottom: 60,
      nodeWidth: 26,
      nodeGap: 26,
      orient: "horizontal",
      draggable: false,
      emphasis: { focus: "adjacency" },
      label: {
        color: t.ink,
        fontSize: 16,
        fontWeight: 500,
      },
      data: nodes,
      links,
    },
  ],
});
