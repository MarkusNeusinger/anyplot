// anyplot.ai
// parallel-categories-basic: Basic Parallel Categories Plot
// Library: echarts 6.1.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-09

const t = window.ANYPLOT_TOKENS;

// Constants
// Outcome colors by meaning, with the Imprint palette as fallback for other outcomes
const OUTCOME_COLORS = { Purchased: t.palette[0], Abandoned: t.palette[4] };

// Columns: set these to your data's column names, the dimensions in axis order
const DIMENSIONS = ["Acquisition channel", "Product category", "Device", "Purchase outcome"]; // role: dimension
const VISITORS = "Visitors"; // role: count

// Data: replace this block with your own records, one object per combination of categories
// Visitors of an online shop: visits per channel and product category, each category's
// desktop share, and a purchase rate per device that each channel shifts up or down.
const visits = {
  "Organic Search": { Electronics: 420, Apparel: 280, "Home & Garden": 150 },
  "Paid Ads": { Electronics: 380, Apparel: 210, "Home & Garden": 90 },
  "Social Media": { Electronics: 160, Apparel: 340, "Home & Garden": 120 },
  "Email Campaign": { Electronics: 90, Apparel: 130, "Home & Garden": 60 },
};
const desktopShare = { Electronics: 0.6, Apparel: 0.55, "Home & Garden": 0.5 };
const purchaseRate = { Desktop: 0.72, Mobile: 0.44 };
const channelLift = { "Organic Search": 0.04, "Paid Ads": -0.02, "Social Media": -0.12, "Email Campaign": 0.12 };
const [CHANNEL, CATEGORY, DEVICE, OUTCOME] = DIMENSIONS;
const data = [];
for (const [channel, byCategory] of Object.entries(visits)) {
  for (const [category, total] of Object.entries(byCategory)) {
    const desktop = Math.round(total * desktopShare[category]);
    for (const [device, visitors] of [
      ["Desktop", desktop],
      ["Mobile", total - desktop],
    ]) {
      const purchased = Math.round(visitors * (purchaseRate[device] + channelLift[channel]));
      for (const [outcome, count] of [
        ["Purchased", purchased],
        ["Abandoned", visitors - purchased],
      ]) {
        data.push({ [CHANNEL]: channel, [CATEGORY]: category, [DEVICE]: device, [OUTCOME]: outcome, [VISITORS]: count });
      }
    }
  }
}

// Plot: reads only data and the constants above
// ECharts has no parallel-categories series; a Sankey with one node column per
// dimension, one node per category and one ribbon per path segment draws it natively.
// Ribbons take the color of the last dimension, the outcome.
const last = DIMENSIONS.at(-1);
const outcomes = [...new Set(data.map((d) => d[last]))];
const outcomeColor = Object.fromEntries(
  outcomes.map((outcome, i) => [outcome, OUTCOME_COLORS[outcome] ?? t.palette[i]]),
);

// One node per category of each dimension, keyed by its dimension so that equal
// category names on two axes stay apart; only the outcome segments carry color.
const nodes = DIMENSIONS.flatMap((dim) =>
  [...new Set(data.map((d) => d[dim]))].map((value) => ({
    name: `${dim}: ${value}`,
    label: { formatter: value },
    itemStyle: { color: dim === last ? outcomeColor[value] : t.inkSoft },
  })),
);

// Ribbons: every path segment between neighbouring axes, split by the path's outcome
// so each ribbon keeps its outcome color from the first axis to the last.
const linkTotals = new Map();
data.forEach((d) => {
  DIMENSIONS.slice(0, -1).forEach((dim, k) => {
    const source = `${dim}: ${d[dim]}`;
    const target = `${DIMENSIONS[k + 1]}: ${d[DIMENSIONS[k + 1]]}`;
    const key = `${source}\u0000${target}\u0000${d[last]}`;
    const link = linkTotals.get(key) ?? { source, target, outcome: d[last], value: 0 };
    link.value += d[VISITORS];
    linkTotals.set(key, link);
  });
});
const links = [...linkTotals.values()].map(({ source, target, outcome, value }) => ({
  source,
  target,
  value,
  lineStyle: { color: outcomeColor[outcome] },
}));

const totalVisitors = data.reduce((sum, d) => sum + d[VISITORS], 0);

// Axis names above the node columns: justified columns sit at equal steps across the
// series' width, and each name starts at its column's left edge like the node labels.
const layout = { left: 40, right: 170, top: 150, bottom: 50, nodeWidth: 22 };
const columnStep =
  (window.ANYPLOT_SIZE.width - layout.left - layout.right - layout.nodeWidth) / (DIMENSIONS.length - 1);
const axisNames = DIMENSIONS.map((dim, k) => ({
  type: "text",
  left: layout.left + k * columnStep,
  top: layout.top - 38,
  style: { text: dim, fill: t.ink, fontSize: 17, fontWeight: 600 },
}));

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "parallel-categories-basic · javascript · echarts · anyplot.ai",
    subtext: `${totalVisitors.toLocaleString("en-US")} ${VISITORS.toLowerCase()} · ribbon width shows ${VISITORS.toLowerCase()}, color shows ${last.toLowerCase()}`,
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 600 },
    subtextStyle: { color: t.inkSoft, fontSize: 16 },
  },
  tooltip: { trigger: "item" },
  graphic: axisNames,
  series: [
    {
      type: "sankey",
      left: layout.left,
      right: layout.right,
      top: layout.top,
      bottom: layout.bottom,
      nodeWidth: layout.nodeWidth,
      nodeGap: 22,
      nodeAlign: "justify",
      // More relaxation passes than the default 32 let the layout settle on an
      // order of categories within each axis with fewer ribbon crossings.
      layoutIterations: 100,
      orient: "horizontal",
      draggable: false,
      emphasis: { focus: "trajectory" },
      lineStyle: { opacity: 0.6, curveness: 0.5 },
      label: {
        color: t.ink,
        fontSize: 15,
        fontWeight: 500,
        backgroundColor: t.pageBg,
        padding: [3, 6],
        borderRadius: 3,
      },
      data: nodes,
      links,
    },
  ],
});
