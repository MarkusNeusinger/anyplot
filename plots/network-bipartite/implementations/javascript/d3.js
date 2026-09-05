// anyplot.ai
// network-bipartite: Bipartite Network Graph
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Gene-disease association network: which genetic markers are linked to which
// conditions, and how strong the evidence for each link is.
const genes = [
  "BRCA1", "BRCA2", "TP53", "EGFR", "KRAS", "MYC", "PTEN",
  "APC", "VHL", "RB1", "ATM", "CDKN2A", "MLH1", "APOE",
];
const diseases = [
  "Breast Cancer", "Ovarian Cancer", "Lung Cancer", "Colorectal Cancer",
  "Pancreatic Cancer", "Renal Cell Carcinoma", "Retinoblastoma",
  "Melanoma", "Lynch Syndrome", "Alzheimer's Disease",
];
const links = [
  { source: "BRCA1", target: "Breast Cancer", weight: 0.95 },
  { source: "BRCA1", target: "Ovarian Cancer", weight: 0.85 },
  { source: "BRCA2", target: "Breast Cancer", weight: 0.9 },
  { source: "BRCA2", target: "Ovarian Cancer", weight: 0.75 },
  { source: "BRCA2", target: "Pancreatic Cancer", weight: 0.35 },
  { source: "TP53", target: "Breast Cancer", weight: 0.6 },
  { source: "TP53", target: "Lung Cancer", weight: 0.7 },
  { source: "TP53", target: "Colorectal Cancer", weight: 0.55 },
  { source: "TP53", target: "Pancreatic Cancer", weight: 0.4 },
  { source: "TP53", target: "Melanoma", weight: 0.4 },
  { source: "EGFR", target: "Lung Cancer", weight: 0.9 },
  { source: "EGFR", target: "Colorectal Cancer", weight: 0.35 },
  { source: "KRAS", target: "Lung Cancer", weight: 0.65 },
  { source: "KRAS", target: "Colorectal Cancer", weight: 0.85 },
  { source: "KRAS", target: "Pancreatic Cancer", weight: 0.6 },
  { source: "MYC", target: "Breast Cancer", weight: 0.5 },
  { source: "MYC", target: "Lung Cancer", weight: 0.45 },
  { source: "MYC", target: "Colorectal Cancer", weight: 0.4 },
  { source: "PTEN", target: "Breast Cancer", weight: 0.55 },
  { source: "PTEN", target: "Melanoma", weight: 0.5 },
  { source: "PTEN", target: "Renal Cell Carcinoma", weight: 0.3 },
  { source: "APC", target: "Colorectal Cancer", weight: 0.95 },
  { source: "VHL", target: "Renal Cell Carcinoma", weight: 0.9 },
  { source: "RB1", target: "Retinoblastoma", weight: 0.95 },
  { source: "RB1", target: "Lung Cancer", weight: 0.3 },
  { source: "ATM", target: "Breast Cancer", weight: 0.45 },
  { source: "CDKN2A", target: "Melanoma", weight: 0.85 },
  { source: "CDKN2A", target: "Lung Cancer", weight: 0.3 },
  { source: "MLH1", target: "Lynch Syndrome", weight: 0.95 },
  { source: "MLH1", target: "Colorectal Cancer", weight: 0.7 },
  { source: "APOE", target: "Alzheimer's Disease", weight: 0.9 },
];

// Degree = number of edges touching a node, drives node radius.
const degree = new Map([...genes, ...diseases].map((name) => [name, 0]));
for (const l of links) {
  degree.set(l.source, degree.get(l.source) + 1);
  degree.set(l.target, degree.get(l.target) + 1);
}

// --- Layout ------------------------------------------------------------------
const margin = { top: 150, right: 360, bottom: 60, left: 200 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;
const leftX = 0;
const rightX = iw;

function columnPositions(names) {
  const step = ih / (names.length + 1);
  return new Map(names.map((name, i) => [name, (i + 1) * step]));
}
const genesY = columnPositions(genes);
const diseasesY = columnPositions(diseases);

const maxDegree = d3.max([...degree.values()]);
const radius = d3.scaleSqrt().domain([1, maxDegree]).range([9, 26]);
const weightExtent = d3.extent(links, (d) => d.weight);
const edgeWidth = d3.scaleLinear().domain(weightExtent).range([1.25, 6]);
const edgeOpacity = d3.scaleLinear().domain(weightExtent).range([0.22, 0.8]);

// --- SVG mount -----------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Edges: gentle S-curves between the two columns -----------------------
const linkPath = (l) => {
  const y1 = genesY.get(l.source);
  const y2 = diseasesY.get(l.target);
  const mx = (leftX + rightX) / 2;
  return `M${leftX},${y1} C${mx},${y1} ${mx},${y2} ${rightX},${y2}`;
};

g.append("g")
  .selectAll("path")
  .data(links)
  .join("path")
  .attr("d", linkPath)
  .attr("fill", "none")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", (d) => edgeWidth(d.weight))
  .attr("stroke-opacity", (d) => edgeOpacity(d.weight));

// --- Nodes: genes (left column) --------------------------------------------
g.append("g")
  .selectAll("circle")
  .data(genes)
  .join("circle")
  .attr("cx", leftX)
  .attr("cy", (d) => genesY.get(d))
  .attr("r", (d) => radius(degree.get(d)))
  .attr("fill", t.palette[0])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

g.append("g")
  .selectAll("text")
  .data(genes)
  .join("text")
  .attr("x", (d) => leftX - radius(degree.get(d)) - 12)
  .attr("y", (d) => genesY.get(d))
  .attr("dy", "0.35em")
  .attr("text-anchor", "end")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text((d) => d);

// --- Nodes: diseases (right column) -----------------------------------------
g.append("g")
  .selectAll("circle")
  .data(diseases)
  .join("circle")
  .attr("cx", rightX)
  .attr("cy", (d) => diseasesY.get(d))
  .attr("r", (d) => radius(degree.get(d)))
  .attr("fill", t.palette[1])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

g.append("g")
  .selectAll("text")
  .data(diseases)
  .join("text")
  .attr("x", (d) => rightX + radius(degree.get(d)) + 12)
  .attr("y", (d) => diseasesY.get(d))
  .attr("dy", "0.35em")
  .attr("text-anchor", "start")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text((d) => d);

// --- Column headers double as the set-membership legend ---------------------
g.append("text")
  .attr("x", leftX)
  .attr("y", -35)
  .attr("text-anchor", "middle")
  .attr("fill", t.palette[0])
  .style("font-size", "18px")
  .style("font-weight", "600")
  .text("Genes");

g.append("text")
  .attr("x", rightX)
  .attr("y", -35)
  .attr("text-anchor", "middle")
  .attr("fill", t.palette[1])
  .style("font-size", "18px")
  .style("font-weight", "600")
  .text("Diseases");

// --- Title + subtitle --------------------------------------------------------
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("network-bipartite · javascript · d3 · anyplot.ai");

svg.append("text")
  .attr("x", width / 2)
  .attr("y", 84)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text("Node size ∝ degree · edge width & opacity ∝ association strength");
