// anyplot.ai
// dendrogram-basic: Basic Dendrogram
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-18

const t = window.ANYPLOT_TOKENS;

const COOL = t.palette[0];  // #009E73 brand green — cool climates branch
const WARM = t.palette[3];  // #BD8233 ochre — warm climates branch

// Leaf label style — shown to the right of each city node
const LEAF_LABEL = {
  show: true,
  position: "right",
  verticalAlign: "middle",
  align: "left",
  fontSize: 14,
  color: t.inkSoft,
  distance: 10,
};

// 12 world cities hierarchically clustered by climate profile
// Cool branch (green): Nordic — Oslo, Stockholm, Helsinki
//                      Temperate — London, Paris, Amsterdam
// Warm branch (ochre): Mediterranean — Barcelona, Rome, Athens
//                      Tropical — Singapore, Bangkok, Mumbai
const treeData = {
  name: "root",
  label: { show: false },
  symbolSize: 4,
  itemStyle: { color: t.inkSoft },
  children: [
    {
      name: "cool",
      label: { show: false },
      lineStyle: { color: COOL },
      itemStyle: { color: COOL },
      children: [
        {
          name: "nordic",
          label: { show: false },
          lineStyle: { color: COOL },
          itemStyle: { color: COOL },
          children: [
            { name: "Oslo",      label: LEAF_LABEL, lineStyle: { color: COOL }, itemStyle: { color: COOL } },
            { name: "Stockholm", label: LEAF_LABEL, lineStyle: { color: COOL }, itemStyle: { color: COOL } },
            { name: "Helsinki",  label: LEAF_LABEL, lineStyle: { color: COOL }, itemStyle: { color: COOL } },
          ],
        },
        {
          name: "temperate",
          label: { show: false },
          lineStyle: { color: COOL },
          itemStyle: { color: COOL },
          children: [
            { name: "London",    label: LEAF_LABEL, lineStyle: { color: COOL }, itemStyle: { color: COOL } },
            { name: "Paris",     label: LEAF_LABEL, lineStyle: { color: COOL }, itemStyle: { color: COOL } },
            { name: "Amsterdam", label: LEAF_LABEL, lineStyle: { color: COOL }, itemStyle: { color: COOL } },
          ],
        },
      ],
    },
    {
      name: "warm",
      label: { show: false },
      lineStyle: { color: WARM },
      itemStyle: { color: WARM },
      children: [
        {
          name: "mediterranean",
          label: { show: false },
          lineStyle: { color: WARM },
          itemStyle: { color: WARM },
          children: [
            { name: "Barcelona", label: LEAF_LABEL, lineStyle: { color: WARM }, itemStyle: { color: WARM } },
            { name: "Rome",      label: LEAF_LABEL, lineStyle: { color: WARM }, itemStyle: { color: WARM } },
            { name: "Athens",    label: LEAF_LABEL, lineStyle: { color: WARM }, itemStyle: { color: WARM } },
          ],
        },
        {
          name: "tropical",
          label: { show: false },
          lineStyle: { color: WARM },
          itemStyle: { color: WARM },
          children: [
            { name: "Singapore", label: LEAF_LABEL, lineStyle: { color: WARM }, itemStyle: { color: WARM } },
            { name: "Bangkok",   label: LEAF_LABEL, lineStyle: { color: WARM }, itemStyle: { color: WARM } },
            { name: "Mumbai",    label: LEAF_LABEL, lineStyle: { color: WARM }, itemStyle: { color: WARM } },
          ],
        },
      ],
    },
  ],
};

// Init
const chart = echarts.init(document.getElementById("container"));

// Option
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "dendrogram-basic · javascript · echarts · anyplot.ai",
    subtext: "Hierarchical clustering of 12 world cities by climate profile",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "500" },
    subtextStyle: { color: t.inkSoft, fontSize: 14 },
  },
  graphic: [
    {
      type: "group",
      left: 80,
      bottom: 28,
      children: [
        {
          type: "circle",
          shape: { cx: 8, cy: 8, r: 7 },
          style: { fill: COOL },
        },
        {
          type: "text",
          left: 22,
          top: 0,
          style: { text: "Cool Climates", fill: t.inkSoft, fontSize: 13, fontFamily: "sans-serif" },
        },
        {
          type: "circle",
          shape: { cx: 166, cy: 8, r: 7 },
          style: { fill: WARM },
        },
        {
          type: "text",
          left: 180,
          top: 0,
          style: { text: "Warm Climates", fill: t.inkSoft, fontSize: 13, fontFamily: "sans-serif" },
        },
      ],
    },
  ],
  series: [
    {
      type: "tree",
      data: [treeData],
      layout: "orthogonal",
      orient: "LR",
      left: "6%",
      right: "18%",
      top: "15%",
      bottom: "12%",
      symbol: "circle",
      symbolSize: 8,
      expandAndCollapse: false,
      initialTreeDepth: -1,
      roam: false,
      lineStyle: {
        width: 1.8,
        curveness: 0,
      },
      label: {
        show: false,
      },
    },
  ],
});
