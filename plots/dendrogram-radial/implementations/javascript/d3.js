// anyplot.ai
// dendrogram-radial: Radial Dendrogram
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 87/100 | Updated: 2026-09-05
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data: a stylized programming-language family tree ---------------------
// Leaves are languages; internal nodes are lineages. `cluster` tags the five
// top-level lineages and is inherited down to every descendant so branches
// and leaf labels can be colored by cluster, mirroring a clustering
// dendrogram's color-coded cluster assignment. ~85 leaves showcases the
// radial layout's space-efficiency advantage over a linear dendrogram.
const familyTree = {
  name: "root",
  children: [
    {
      name: "Systems & Low-Level",
      cluster: 0,
      children: [
        {
          name: "C family",
          children: [
            { name: "C" },
            { name: "C++" },
            { name: "Objective-C" },
            { name: "D" },
            { name: "Cyclone" },
          ],
        },
        { name: "Rust" },
        { name: "Ada" },
        { name: "Zig" },
        { name: "Swift" },
        { name: "Go" },
        { name: "Nim" },
        { name: "Forth" },
        { name: "Assembly" },
        { name: "Pascal" },
        { name: "Modula-2" },
        { name: "Vala" },
        { name: "Odin" },
        { name: "Crystal" },
        { name: "V" },
      ],
    },
    {
      name: "Enterprise OOP",
      cluster: 1,
      children: [
        {
          name: "JVM family",
          children: [
            { name: "Java" },
            { name: "Kotlin" },
            { name: "Scala" },
            { name: "Groovy" },
            { name: "Xtend" },
            { name: "Ceylon" },
          ],
        },
        { name: "C#" },
        { name: "VB.NET" },
        { name: "Eiffel" },
        { name: "Smalltalk" },
        { name: "Dart" },
        { name: "COBOL" },
        { name: "Object Pascal" },
        { name: "ABAP" },
        { name: "PL/I" },
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
            { name: "Hy" },
          ],
        },
        {
          name: "ML family",
          children: [
            { name: "OCaml" },
            { name: "F#" },
            { name: "Haskell" },
            { name: "Elm" },
            { name: "Standard ML" },
            { name: "ReasonML" },
            { name: "PureScript" },
            { name: "Idris" },
          ],
        },
        {
          name: "BEAM family",
          children: [{ name: "Erlang" }, { name: "Elixir" }, { name: "Gleam" }],
        },
        { name: "Agda" },
        { name: "Lean" },
        { name: "Miranda" },
      ],
    },
    {
      name: "Dynamic Scripting",
      cluster: 3,
      children: [
        {
          name: "Web family",
          children: [{ name: "JavaScript" }, { name: "TypeScript" }, { name: "CoffeeScript" }],
        },
        { name: "Python" },
        { name: "Ruby" },
        { name: "PHP" },
        { name: "Perl" },
        { name: "Lua" },
        { name: "Bash" },
        { name: "PowerShell" },
        { name: "Tcl" },
        { name: "Raku" },
        { name: "AWK" },
        { name: "Io" },
        { name: "Zsh" },
        { name: "Fish" },
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
        { name: "Octave" },
        { name: "Stata" },
        { name: "J" },
        { name: "K" },
        { name: "SPSS" },
        { name: "GAMS" },
        { name: "AMPL" },
        { name: "MiniZinc" },
        { name: "Prolog" },
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
const outerRadius = Math.min(width, height - titleSpace) / 2 - 150;

const root = d3.hierarchy(familyTree);
d3.cluster().size([2 * Math.PI, outerRadius])(root);
root.each((d) => {
  d.r = outerRadius * (1 - d.data.distance / maxDistance);
});

const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
// The vertical translate is resolved after the content (including label
// extents) is drawn, so the visual bounding box — not just the layout
// radius — is centered in the space below the title.
const g = svg.append("g");

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
  .attr("r", 4)
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
  .style("font-size", "13px")
  .style("font-family", "sans-serif")
  .text((d) => d.data.name);

// Balance the visual bounding box (branches + markers + label extents)
// within the drawable band below the title, instead of only centering the
// bare layout radius — leaf labels near the bottom of the circle otherwise
// push further down than the top, leaving unequal whitespace.
const bbox = g.node().getBBox();
const cy = (height + titleSpace) / 2 - bbox.y - bbox.height / 2;
g.attr("transform", `translate(${cx},${cy})`);

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
  .attr("transform", (_, i) => `translate(0, ${i * 28})`)
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
      .style("font-size", "14px")
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
