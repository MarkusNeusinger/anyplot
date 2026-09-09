// anyplot.ai
// tree-phylogenetic: Phylogenetic Tree Diagram
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 100, right: 200, bottom: 150, left: 40 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: primate phylogeny from mitochondrial-DNA divergence estimates ---
// Each `length` is the branch length in millions of years (Mya) since the
// parent node split off — an ultrametric tree, so every tip lines up at the
// same cumulative distance from the common ancestor (a molecular-clock read).
const tree = {
  name: "Common ancestor",
  children: [
    { name: "Ring-tailed Lemur", length: 65, clade: 0 },
    {
      name: "Anthropoidea",
      length: 25,
      children: [
        { name: "Common Marmoset", length: 40, clade: 1 },
        {
          name: "Catarrhini",
          length: 11,
          children: [
            {
              name: "Cercopithecidae",
              length: 18,
              children: [
                { name: "Olive Baboon", length: 11, clade: 2 },
                { name: "Rhesus Macaque", length: 11, clade: 2 },
              ],
            },
            {
              name: "Hominoidea",
              length: 9,
              children: [
                { name: "White-handed Gibbon", length: 20, clade: 3 },
                {
                  name: "Hominidae",
                  length: 5,
                  children: [
                    { name: "Bornean Orangutan", length: 15, clade: 3 },
                    {
                      name: "Homininae",
                      length: 6,
                      children: [
                        { name: "Western Gorilla", length: 9, clade: 3 },
                        {
                          name: "Homo/Pan",
                          length: 3,
                          children: [
                            { name: "Human", length: 6, clade: 3 },
                            { name: "Chimpanzee", length: 6, clade: 3 },
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

const CLADE_NAMES = ["Strepsirrhini", "New World monkeys", "Old World monkeys", "Apes"];
const cladeColor = d3.scaleOrdinal().domain([0, 1, 2, 3]).range(t.palette.slice(0, 4));

// --- Hierarchy + phylogram layout -------------------------------------------
const root = d3.hierarchy(tree, (d) => d.children);

// cumulative branch length (Mya since the common ancestor); each.() visits
// in breadth-first order, so a parent's len is always set before its children
root.each((d) => {
  d.len = d.parent ? d.parent.len + d.data.length : 0;
});

// leaves evenly spaced top-to-bottom in traversal order
const leaves = root.leaves();
leaves.forEach((d, i) => {
  d.py = (i / (leaves.length - 1)) * ih;
});
// internal nodes settle at the midpoint of their children (post-order)
root.eachAfter((d) => {
  if (d.children) d.py = d3.mean(d.children, (c) => c.py);
});

// a node inherits a clade color only if every descendant shares one clade —
// this keeps the deep backbone branches neutral and highlights each clade
root.eachAfter((d) => {
  if (!d.children) {
    d.clade = d.data.clade;
  } else {
    const clades = new Set(d.children.map((c) => c.clade));
    d.clade = clades.size === 1 ? [...clades][0] : null;
  }
});

const maxLen = d3.max(root.descendants(), (d) => d.len);
const x = d3.scaleLinear().domain([0, maxLen]).range([0, iw]);

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Branches: elbow links (vertical at the parent's age, then horizontal) --
g.selectAll("path.branch")
  .data(root.links())
  .join("path")
  .attr("class", "branch")
  .attr("fill", "none")
  .attr("stroke", (d) => (d.target.clade !== null ? cladeColor(d.target.clade) : t.inkSoft))
  .attr("stroke-width", 2.5)
  .attr("d", (d) => `M${x(d.source.len)},${d.source.py} V${d.target.py} H${x(d.target.len)}`);

// --- Nodes ---------------------------------------------------------------------
const nodes = g
  .selectAll("g.node")
  .data(root.descendants())
  .join("g")
  .attr("class", "node")
  .attr("transform", (d) => `translate(${x(d.len)},${d.py})`);

nodes
  .append("circle")
  .attr("r", (d) => (d.children ? 4 : 6))
  .attr("fill", (d) => (d.clade !== null ? cladeColor(d.clade) : t.pageBg))
  .attr("stroke", (d) => (d.clade !== null ? cladeColor(d.clade) : t.inkSoft))
  .attr("stroke-width", 1.5);

// --- Leaf labels (species names, italicized per taxonomic convention) -------
nodes
  .filter((d) => !d.children)
  .append("text")
  .attr("x", 12)
  .attr("dy", "0.32em")
  .style("font-size", "16px")
  .style("font-style", "italic")
  .attr("fill", t.ink)
  .text((d) => d.data.name);

// --- X axis: divergence time (doubles as the branch-length scale bar) -------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih + 20})`)
  .call(d3.axisBottom(x).ticks(6));
xAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
xAxis.selectAll("line").attr("stroke", t.grid);
xAxis.select(".domain").attr("stroke", t.inkSoft);

g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("Divergence time since common ancestor (million years, mtDNA estimate)");

// --- Clade legend --------------------------------------------------------------
const legendSpacing = 240;
const legendStartX = (iw - legendSpacing * (CLADE_NAMES.length - 1)) / 2 - 70;
const legend = g.append("g").attr("transform", `translate(${legendStartX},${ih + 90})`);
CLADE_NAMES.forEach((name, i) => {
  const item = legend.append("g").attr("transform", `translate(${i * legendSpacing},0)`);
  item.append("circle").attr("r", 6).attr("fill", cladeColor(i));
  item
    .append("text")
    .attr("x", 14)
    .attr("dy", "0.32em")
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(name);
});

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("tree-phylogenetic · javascript · d3 · anyplot.ai");
