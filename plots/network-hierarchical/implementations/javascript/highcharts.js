// anyplot.ai
// network-hierarchical: Hierarchical Network Graph with Tree Layout
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data: organizational chart, 4 levels (CEO -> VP -> Director -> Manager) ---
const org = {
  id: "ceo",
  name: "CEO",
  children: [
    {
      id: "vp-eng",
      name: "VP Engineering",
      children: [
        {
          id: "dir-fe",
          name: "Dir. Frontend",
          children: [
            { id: "mgr-a", name: "A. Kim" },
            { id: "mgr-b", name: "B. Diaz" },
          ],
        },
        {
          id: "dir-be",
          name: "Dir. Backend",
          children: [
            { id: "mgr-c", name: "C. Chen" },
            { id: "mgr-d", name: "D. Patel" },
          ],
        },
      ],
    },
    {
      id: "vp-sales",
      name: "VP Sales",
      children: [
        {
          id: "dir-ent",
          name: "Dir. Enterprise",
          children: [
            { id: "mgr-e", name: "E. Novak" },
            { id: "mgr-f", name: "F. Silva" },
          ],
        },
        {
          id: "dir-smb",
          name: "Dir. SMB",
          children: [{ id: "mgr-g", name: "G. Osei" }],
        },
      ],
    },
    {
      id: "vp-mkt",
      name: "VP Marketing",
      children: [
        {
          id: "dir-brand",
          name: "Dir. Brand",
          children: [{ id: "mgr-h", name: "H. Reyes" }],
        },
        {
          id: "dir-growth",
          name: "Dir. Growth",
          children: [{ id: "mgr-i", name: "I. Haddad" }],
        },
      ],
    },
    {
      id: "vp-fin",
      name: "VP Finance",
      children: [
        {
          id: "dir-acct",
          name: "Dir. Accounting",
          children: [{ id: "mgr-j", name: "J. Costa" }],
        },
        {
          id: "dir-treas",
          name: "Dir. Treasury",
          children: [{ id: "mgr-k", name: "K. Ibrahim" }],
        },
      ],
    },
  ],
};

// Flatten the tree into per-level nodes with a tidy-tree x layout (leaves get
// sequential x, internal nodes sit above the mean x of their children) plus
// parent-child edges for the connector overlay drawn in chart.events.render.
const LEVEL_NAMES = ["CEO", "VP", "Director", "Manager"];
const nodesByLevel = [[], [], [], []];
const edges = [];
let nextLeafX = 0;

function layout(node, level) {
  let x;
  if (!node.children) {
    x = nextLeafX;
    nextLeafX += 1;
  } else {
    const childXs = node.children.map((child) => {
      edges.push([node.id, child.id]);
      return layout(child, level + 1);
    });
    x = childXs.reduce((a, b) => a + b, 0) / childXs.length;
  }
  nodesByLevel[level].push({ id: node.id, name: node.name, x, y: level });
  return x;
}
layout(org, 0);

const nodeById = {};
nodesByLevel.forEach((level) => level.forEach((n) => { nodeById[n.id] = n; }));

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    events: {
      // Core Highcharts has no built-in tree/network series (those live in the
      // unloaded networkgraph/treegraph modules), so parent-child connectors
      // are drawn by hand as SVG paths between each pair's pixel coordinates.
      render() {
        const chart = this;
        if (chart.edgeGroup) chart.edgeGroup.destroy();
        chart.edgeGroup = chart.renderer.g("edges").attr({ zIndex: 2 }).add();
        edges.forEach(([parentId, childId]) => {
          const p = nodeById[parentId];
          const c = nodeById[childId];
          const x1 = chart.xAxis[0].toPixels(p.x);
          const y1 = chart.yAxis[0].toPixels(p.y);
          const x2 = chart.xAxis[0].toPixels(c.x);
          const y2 = chart.yAxis[0].toPixels(c.y);
          chart.renderer
            .path(["M", x1, y1, "L", x2, y2])
            .attr({ stroke: t.inkSoft, "stroke-width": 1.5, opacity: 0.45 })
            .add(chart.edgeGroup);
        });
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "network-hierarchical · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: { visible: false, min: -0.6, max: nextLeafX - 0.4 },
  yAxis: { visible: false, reversed: true, min: -0.4, max: 3.5 },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: { radius: 9, lineColor: t.pageBg, lineWidth: 1.5 },
      dataLabels: {
        enabled: true,
        format: "{point.name}",
        verticalAlign: "top",
        y: 16,
        crop: false,
        overflow: "allow",
        style: { color: t.inkSoft, fontSize: "13px", fontWeight: "normal", textOutline: "none" },
      },
    },
  },
  series: LEVEL_NAMES.map((name, level) => ({
    name,
    color: t.palette[level],
    data: nodesByLevel[level].map((n, i) => ({
      x: n.x,
      y: n.y,
      name: n.name,
      // The Manager row is the most crowded level — stagger label offsets so
      // adjacent short names don't collide horizontally.
      dataLabels: level === 3 ? { y: i % 2 === 0 ? 16 : 32 } : undefined,
    })),
  })),
});
