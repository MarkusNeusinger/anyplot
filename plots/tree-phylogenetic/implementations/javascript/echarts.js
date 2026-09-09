// anyplot.ai
// tree-phylogenetic: Phylogenetic Tree Diagram
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data: primate phylogeny from mitochondrial DNA divergence --------------
// Each node carries `length` = branch length to its parent, in substitutions
// per site. `clade` marks the root of one of the four highlighted lineages;
// descendants inherit it. Values are illustrative, not a literal alignment.
const TREE = {
  name: "Root",
  length: 0,
  children: [
    {
      name: "Prosimians",
      length: 0.32,
      clade: 0,
      children: [
        { name: "Lemur", length: 0.28, children: [] },
        { name: "Galago", length: 0.3, children: [] },
      ],
    },
    {
      name: "Anthropoidea",
      length: 0.32,
      children: [
        {
          name: "New World Monkeys",
          length: 0.18,
          clade: 1,
          children: [
            { name: "Marmoset", length: 0.14, children: [] },
            { name: "Squirrel Monkey", length: 0.13, children: [] },
          ],
        },
        {
          name: "Catarrhini",
          length: 0.14,
          children: [
            {
              name: "Old World Monkeys",
              length: 0.1,
              clade: 2,
              children: [
                { name: "Baboon", length: 0.06, children: [] },
                { name: "Macaque", length: 0.055, children: [] },
              ],
            },
            {
              name: "Apes",
              length: 0.09,
              clade: 3,
              children: [
                { name: "Gibbon", length: 0.085, children: [] },
                {
                  name: "Great Apes",
                  length: 0.045,
                  children: [
                    { name: "Orangutan", length: 0.065, children: [] },
                    {
                      name: "African Apes",
                      length: 0.035,
                      children: [
                        { name: "Gorilla", length: 0.045, children: [] },
                        {
                          name: "Human-Chimp",
                          length: 0.02,
                          children: [
                            { name: "Chimpanzee", length: 0.018, children: [] },
                            { name: "Human", length: 0.018, children: [] },
                          ],
                        },
                      ],
                    },
                  ],
                },
              ],
            },
          ],
        },
      ],
    },
  ],
};

const CLADE_NAMES = ["Prosimians", "New World Monkeys", "Old World Monkeys", "Apes (Hominoidea)"];

// --- Layout: cumulative branch length -> x, leaf order -> y -----------------
// Rectangular phylogram: each parent/child pair is joined via an invisible
// corner node so branches meet at right angles, the classic cladogram style.
const nodes = [];
const edges = [];
let leafCount = 0;

function colorFor(clade) {
  return clade == null ? t.muted : t.palette[clade];
}

function walk(node, parentX, inheritedClade) {
  const x = parentX + node.length;
  const clade = node.clade != null ? node.clade : inheritedClade;
  const isLeaf = node.children.length === 0;

  if (isLeaf) {
    const y = leafCount;
    leafCount += 1;
    nodes.push({
      name: node.name,
      x,
      y,
      symbolSize: 16,
      category: clade,
      itemStyle: clade == null ? { color: t.muted } : undefined,
      label: { show: true, position: "right", distance: 8, color: t.ink, fontSize: 15, fontWeight: 500 },
    });
    return { x, y, name: node.name };
  }

  const childResults = node.children.map((child) => walk(child, x, clade));
  const ys = childResults.map((c) => c.y);
  const y = (Math.min(...ys) + Math.max(...ys)) / 2;

  nodes.push({
    name: node.name,
    x,
    y,
    symbolSize: 9,
    category: clade,
    itemStyle: clade == null ? { color: t.muted } : undefined,
    label: { show: false },
  });

  childResults.forEach((child, i) => {
    const childClade = node.children[i].clade != null ? node.children[i].clade : clade;
    const corner = `${node.name}->${child.name}`;
    nodes.push({ name: corner, x, y: child.y, symbolSize: 0, silent: true, label: { show: false } });
    edges.push({ source: node.name, target: corner, color: colorFor(childClade) });
    edges.push({ source: corner, target: child.name, color: colorFor(childClade) });
  });

  return { x, y, name: node.name };
}

walk(TREE, 0, null);

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "tree-phylogenetic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 16,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 600 },
  },
  legend: {
    data: CLADE_NAMES,
    top: 58,
    left: "center",
    itemWidth: 16,
    itemHeight: 12,
    textStyle: { color: t.ink, fontSize: 15 },
  },
  tooltip: { show: false },
  grid: { left: 24, right: 300, top: 108, bottom: 90 },
  xAxis: {
    type: "value",
    min: 0,
    name: "Evolutionary distance (substitutions per site)",
    nameLocation: "middle",
    nameGap: 42,
    nameTextStyle: { color: t.inkSoft, fontSize: 15 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { onZero: false, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    show: false,
    min: -1,
    max: leafCount,
    inverse: true,
    axisLine: { onZero: false },
  },
  series: [
    {
      type: "graph",
      coordinateSystem: "cartesian2d",
      layout: "none",
      symbol: "circle",
      edgeSymbol: ["none", "none"],
      categories: CLADE_NAMES.map((name, i) => ({ name, itemStyle: { color: t.palette[i] } })),
      data: nodes.map((n) => ({
        name: n.name,
        value: [n.x, n.y],
        symbolSize: n.symbolSize,
        category: n.category,
        itemStyle: n.itemStyle,
        label: n.label,
        silent: n.silent,
      })),
      edges: edges.map((e) => ({
        source: e.source,
        target: e.target,
        lineStyle: { color: e.color, width: e.color === t.muted ? 2.2 : 3, curveness: 0 },
      })),
      z: 2,
    },
  ],
});
