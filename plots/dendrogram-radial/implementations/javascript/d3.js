// anyplot.ai
// dendrogram-radial: Radial Dendrogram
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-04
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data: a stylized programming-language family tree ---------------------
// Leaves are languages; internal nodes are lineages. `cluster` tags the five
// top-level lineages and is inherited down to every descendant so branches
// and leaf labels can be colored by cluster, mirroring a clustering
// dendrogram's color-coded cluster assignment.
const familyTree = {
  name: "root",
  children: [
    {
      name: "Systems & Low-Level",
      cluster: 0,
      children: [
        {
          name: "C family",
          children: [{ name: "C" }, { name: "C++" }, { name: "Objective-C" }, { name: "D" }],
        },
        { name: "Rust" },
        { name: "Ada" },
        { name: "Zig" },
        { name: "Swift" },
      ],
    },
    {
      name: "Enterprise OOP",
      cluster: 1,
      children: [
        {
          name: "JVM family",
          children: [{ name: "Java" }, { name: "Kotlin" }, { name: "Scala" }, { name: "Groovy" }],
        },
        { name: "C#" },
        { name: "VB.NET" },
      ],
    },
    {
      name: "Functional",
      cluster: 2,
      children: [
        {
          name: "Lisp family",
          children: [
            { name: "Common Lisp" },
            { name: "Scheme" },
            { name: "Racket" },
            { name: "Clojure" },
          ],
        },
        {
          name: "ML family",
          children: [{ name: "OCaml" }, { name: "F#" }, { name: "Haskell" }, { name: "Elm" }],
        },
        {
          name: "BEAM family",
          children: [{ name: "Erlang" }, { name: "Elixir" }],
        },
      ],
    },
    {
      name: "Dynamic Scripting",
      cluster: 3,
      children: [
        { name: "Python" },
        { name: "Ruby" },
        { name: "PHP" },
        { name: "Perl" },
        {
          name: "Web family",
          children: [{ name: "JavaScript" }, { name: "TypeScript" }],
        },
        { name: "Lua" },
        { name: "Bash" },
      ],
    },
    {
      name: "Data & Scientific",
      cluster: 4,
      children: [
        { name: "R" },
        { name: "Julia" },
        { name: "MATLAB" },
        { name: "Fortran" },
        { name: "SQL" },
        { name: "SAS" },
        { name: "APL" },
        { name: "Mathematica" },
      ],
    },
  ],
};

// Deterministic LCG so merge-distance gaps are reproducible without Math.random.
let seed = 42;
const nextRandom = () => {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
};

// Bottom-up merge distance: leaves sit at distance 0, every internal node's
// distance is the max of its children plus a random positive gap — the same
// "later merges join at greater dissimilarity" property a linkage matrix encodes.
const assignDistance = (node) => {
  if (!node.children) {
    node.distance = 0;
    return 0;
  }
  const maxChild = Math.max(...node.children.map(assignDistance));
  node.distance = maxChild + 8 + nextRandom() * 12;
  return node.distance;
};
assignDistance(familyTree);
const maxDistance = familyTree.distance;

// Propagate each top-level lineage's cluster id down to its descendants.
const propagateCluster = (node, inherited) => {
  const cluster = node.cluster !== undefined ? node.cluster : inherited;
  node.cluster = cluster;
  if (node.children) node.children.forEach((child) => propagateCluster(child, cluster));
};
propagateCluster(familyTree, null);

// --- Layout ------------------------------------------------------------------
const titleSpace = 90;
const cx = width / 2;
const cy = titleSpace + (height - titleSpace) / 2;
const outerRadius = Math.min(width, height - titleSpace) / 2 - 150;

const root = d3.hierarchy(familyTree);
d3.cluster().size([2 * Math.PI, outerRadius])(root);
root.each((d) => {
  d.r = outerRadius * (1 - d.data.distance / maxDistance);
});

const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);

// --- Branches, colored by inherited cluster ----------------------------------
g.append("g")
  .attr("fill", "none")
  .selectAll("path")
  .data(root.links())
  .join("path")
  .attr(
    "d",
    d3
      .linkRadial()
      .angle((d) => d.x)
      .radius((d) => d.r),
  )
  .attr("stroke", (d) => (d.target.data.cluster != null ? t.palette[d.target.data.cluster] : t.inkSoft))
  .attr("stroke-width", (d) => (d.target.children ? 2.2 : 1.6))
  .attr("stroke-opacity", 0.85);

// --- Internal merge points ----------------------------------------------------
g.append("g")
  .selectAll("circle")
  .data(root.descendants().filter((d) => d.children))
  .join("circle")
  .attr("transform", (d) => `rotate(${(d.x * 180) / Math.PI - 90}) translate(${d.r},0)`)
  .attr("r", (d) => (d.depth === 0 ? 0 : 3))
  .attr("fill", t.pageBg)
  .attr("stroke", (d) => (d.data.cluster != null ? t.palette[d.data.cluster] : t.inkSoft))
  .attr("stroke-width", 1.6);

// --- Leaf tips -----------------------------------------------------------------
g.append("g")
  .selectAll("circle")
  .data(root.leaves())
  .join("circle")
  .attr("transform", (d) => `rotate(${(d.x * 180) / Math.PI - 90}) translate(${d.r},0)`)
  .attr("r", 4.5)
  .attr("fill", (d) => t.palette[d.data.cluster]);

// --- Leaf labels -----------------------------------------------------------------
g.append("g")
  .selectAll("text")
  .data(root.leaves())
  .join("text")
  .attr(
    "transform",
    (d) =>
      `rotate(${(d.x * 180) / Math.PI - 90}) translate(${d.r + 10},0) ${d.x >= Math.PI ? "rotate(180)" : ""}`,
  )
  .attr("text-anchor", (d) => (d.x < Math.PI ? "start" : "end"))
  .attr("dy", "0.32em")
  .attr("fill", (d) => t.palette[d.data.cluster])
  .style("font-size", "12px")
  .style("font-family", "sans-serif")
  .text((d) => d.data.name);

// --- Legend --------------------------------------------------------------------
const legendEntries = familyTree.children.map((node) => ({
  name: node.name,
  color: t.palette[node.cluster],
}));
const legend = svg.append("g").attr("transform", `translate(40, ${titleSpace + 10})`);
legend
  .selectAll("g")
  .data(legendEntries)
  .join("g")
  .attr("transform", (_, i) => `translate(0, ${i * 26})`)
  .call((sel) => {
    sel
      .append("rect")
      .attr("width", 14)
      .attr("height", 14)
      .attr("y", -11)
      .attr("fill", (d) => d.color);
    sel
      .append("text")
      .attr("x", 20)
      .attr("fill", t.inkSoft)
      .style("font-size", "13px")
      .style("font-family", "sans-serif")
      .text((d) => d.name);
  });

// --- Title -----------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .style("font-family", "sans-serif")
  .text("dendrogram-radial · javascript · d3 · anyplot.ai");
