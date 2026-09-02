// anyplot.ai
// network-hierarchical: Hierarchical Network Graph with Tree Layout
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 70, right: 380, bottom: 40, left: 150 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: a repository directory tree, root -> file leaves --------------
const projectTree = {
  name: "project/",
  children: [
    {
      name: "src/",
      children: [
        {
          name: "components/",
          children: [{ name: "Button.tsx" }, { name: "Card.tsx" }, { name: "Modal.tsx" }],
        },
        { name: "utils/", children: [{ name: "format.ts" }, { name: "validate.ts" }] },
        { name: "api/", children: [{ name: "client.ts" }, { name: "endpoints.ts" }] },
        { name: "hooks/", children: [{ name: "useAuth.ts" }] },
      ],
    },
    {
      name: "tests/",
      children: [
        { name: "unit/", children: [{ name: "button.test.ts" }, { name: "utils.test.ts" }] },
        { name: "integration/", children: [{ name: "api.test.ts" }] },
      ],
    },
    {
      name: "docs/",
      children: [
        { name: "guides/", children: [{ name: "quickstart.md" }] },
        { name: "reference/", children: [{ name: "api.md" }] },
      ],
    },
    { name: "config/", children: [{ name: "env/", children: [{ name: ".env.example" }] }] },
  ],
};

// --- Layout -----------------------------------------------------------------
const root = d3.hierarchy(projectTree);
const treeLayout = d3.tree().size([ih, iw]).separation((a, b) => (a.parent === b.parent ? 1 : 1.3));
treeLayout(root);

const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Edges: parent-child links, no arrows ------------------------------------
const linkGen = d3
  .linkHorizontal()
  .x((d) => d.y)
  .y((d) => d.x);

g.selectAll("path.link")
  .data(root.links())
  .join("path")
  .attr("class", "link")
  .attr("d", linkGen)
  .attr("fill", "none")
  .attr("stroke", t.grid)
  .attr("stroke-width", 1.6);

// --- Nodes: one categorical color per depth level (root always palette[0]) --
const depthColor = (depth) => t.palette[Math.min(depth, t.palette.length - 1)];
const depthRadius = (depth) => [11, 8.5, 7, 5.5][Math.min(depth, 3)];

const node = g
  .selectAll("g.node")
  .data(root.descendants())
  .join("g")
  .attr("class", "node")
  .attr("transform", (d) => `translate(${d.y},${d.x})`);

node
  .append("circle")
  .attr("r", (d) => depthRadius(d.depth))
  .attr("fill", (d) => depthColor(d.depth))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

node
  .append("text")
  .attr("x", (d) => (d.children ? -(depthRadius(d.depth) + 8) : depthRadius(d.depth) + 8))
  .attr("dy", "0.32em")
  .attr("text-anchor", (d) => (d.children ? "end" : "start"))
  .attr("fill", t.inkSoft)
  .style("font-size", (d) => (d.depth === 0 ? "16px" : "14px"))
  .style("font-weight", (d) => (d.depth === 0 ? "600" : "400"))
  .text((d) => d.data.name);

// --- Legend: depth level meaning ---------------------------------------------
const legendLabels = ["Root", "Top-level dir", "Subdirectory", "File"];
const legend = svg
  .append("g")
  .attr("transform", `translate(${width - 190},${margin.top + 30})`);

legend
  .append("text")
  .attr("x", 0)
  .attr("y", 0)
  .attr("fill", t.ink)
  .style("font-size", "15px")
  .style("font-weight", "600")
  .text("Depth level");

legendLabels.forEach((label, i) => {
  const row = legend.append("g").attr("transform", `translate(0,${34 + i * 32})`);
  row.append("circle").attr("r", 8).attr("fill", depthColor(i)).attr("stroke", t.pageBg).attr("stroke-width", 1.5);
  row
    .append("text")
    .attr("x", 18)
    .attr("y", 0)
    .attr("dy", "0.32em")
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(label);
});

// --- Title --------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("network-hierarchical · javascript · d3 · anyplot.ai");
