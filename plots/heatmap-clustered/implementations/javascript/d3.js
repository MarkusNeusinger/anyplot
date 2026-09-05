// anyplot.ai
// heatmap-clustered: Clustered Heatmap
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Deterministic PRNG (browser has no seeded RNG) -------------------------
function lcg(seed) {
  let state = seed % 2147483647;
  if (state <= 0) state += 2147483646;
  return function () {
    state = (state * 16807) % 2147483647;
    return (state - 1) / 2147483646;
  };
}
const rng = lcg(42);
function randomNormal() {
  const u1 = rng();
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// --- Data: gene-expression z-scores across dosage groups --------------------
// Rows = genes grouped into 4 co-expression modules, columns = dosage-group
// replicates. Values are already centered on zero, matching the diverging cmap.
const groups = ["Control", "Low-Dose", "High-Dose"];
const replicatesPerGroup = 4;
const columnLabels = [];
groups.forEach((g) => {
  for (let r = 1; r <= replicatesPerGroup; r++) columnLabels.push(`${g}-${r}`);
});

const modules = [
  { size: 5, effect: [1.8, -1.5, 0.2] },
  { size: 5, effect: [-1.6, 1.7, 0.3] },
  { size: 4, effect: [0.1, -1.8, 1.6] },
  { size: 4, effect: [-1.9, -0.2, 1.8] },
];

const rowLabels = [];
const matrix = [];
let geneIndex = 1;
modules.forEach((mod) => {
  for (let i = 0; i < mod.size; i++) {
    rowLabels.push(`Gene-${String(geneIndex).padStart(2, "0")}`);
    geneIndex++;
    const row = [];
    groups.forEach((_, gi) => {
      for (let r = 0; r < replicatesPerGroup; r++) {
        row.push(mod.effect[gi] + randomNormal() * 0.4);
      }
    });
    matrix.push(row);
  }
});

function transpose(m) {
  return m[0].map((_, j) => m.map((row) => row[j]));
}

// --- Hierarchical clustering (UPGMA / average linkage, Euclidean distance) --
function euclideanDistance(a, b) {
  let sum = 0;
  for (let i = 0; i < a.length; i++) sum += (a[i] - b[i]) ** 2;
  return Math.sqrt(sum);
}

function averageLinkageCluster(vectors) {
  let active = vectors.map((v, i) => ({ indices: [i], height: 0, children: null }));
  while (active.length > 1) {
    let bestI = 0;
    let bestJ = 1;
    let bestD = Infinity;
    for (let i = 0; i < active.length; i++) {
      for (let j = i + 1; j < active.length; j++) {
        let total = 0;
        let count = 0;
        for (const ai of active[i].indices) {
          for (const aj of active[j].indices) {
            total += euclideanDistance(vectors[ai], vectors[aj]);
            count++;
          }
        }
        const d = total / count;
        if (d < bestD) {
          bestD = d;
          bestI = i;
          bestJ = j;
        }
      }
    }
    const a = active[bestI];
    const b = active[bestJ];
    const merged = { indices: a.indices.concat(b.indices), height: bestD, children: [a, b] };
    active = active.filter((_, k) => k !== bestI && k !== bestJ);
    active.push(merged);
  }
  return active[0];
}

// Assigns each node a leaf-order position `u` and a merge-height `v`, and
// records the left-to-right leaf visitation order (no branch crossings).
function assignPositions(node, leafOrder) {
  if (!node.children) {
    node.u = leafOrder.length;
    node.v = 0;
    leafOrder.push(node.indices[0]);
    return;
  }
  assignPositions(node.children[0], leafOrder);
  assignPositions(node.children[1], leafOrder);
  node.u = (node.children[0].u + node.children[1].u) / 2;
  node.v = node.height;
}

// Elbow-style dendrogram links in abstract (u = leaf position, v = height) space.
function collectSegments(node, segments) {
  if (!node.children) return;
  const [c0, c1] = node.children;
  segments.push({ u1: c0.u, v1: c0.v, u2: c0.u, v2: node.v });
  segments.push({ u1: c1.u, v1: c1.v, u2: c1.u, v2: node.v });
  segments.push({ u1: c0.u, v1: node.v, u2: c1.u, v2: node.v });
  collectSegments(c0, segments);
  collectSegments(c1, segments);
}

const rowTree = averageLinkageCluster(matrix);
const rowOrder = [];
assignPositions(rowTree, rowOrder);
const rowSegments = [];
collectSegments(rowTree, rowSegments);
const rowMaxHeight = rowTree.v;

const colTree = averageLinkageCluster(transpose(matrix));
const colOrder = [];
assignPositions(colTree, colOrder);
const colSegments = [];
collectSegments(colTree, colSegments);
const colMaxHeight = colTree.v;

const orderedRowLabels = rowOrder.map((i) => rowLabels[i]);
const orderedColLabels = colOrder.map((i) => columnLabels[i]);
const orderedMatrix = rowOrder.map((ri) => colOrder.map((ci) => matrix[ri][ci]));

// --- Layout -------------------------------------------------------------
const marginLeft = 20;
const rowDendroWidth = 130;
const rowLabelWidth = 120;
const gapLeft = 8;
const gapRight = 20;
const colorbarWidth = 34;
const colorbarAxisWidth = 60;
const marginRight = 26;

const marginTop = 74;
const colDendroHeight = 130;
const gapTop = 6;
const colLabelHeight = 110;
const marginBottom = 26;

const heatmapX = marginLeft + rowDendroWidth + rowLabelWidth + gapLeft;
const heatmapWidth =
  width - heatmapX - gapRight - colorbarWidth - colorbarAxisWidth - marginRight;
const heatmapY = marginTop + colDendroHeight + gapTop;
const heatmapHeight = height - heatmapY - colLabelHeight - marginBottom;

const xCell = d3.scaleBand().domain(d3.range(colOrder.length)).range([0, heatmapWidth]);
const yCell = d3.scaleBand().domain(d3.range(rowOrder.length)).range([0, heatmapHeight]);

const rowLeafScale = d3
  .scaleLinear()
  .domain([0, rowOrder.length - 1])
  .range([yCell.bandwidth() / 2, heatmapHeight - yCell.bandwidth() / 2]);
const colLeafScale = d3
  .scaleLinear()
  .domain([0, colOrder.length - 1])
  .range([xCell.bandwidth() / 2, heatmapWidth - xCell.bandwidth() / 2]);
const rowHeightScale = d3.scaleLinear().domain([0, rowMaxHeight]).range([rowDendroWidth, 0]);
const colHeightScale = d3.scaleLinear().domain([0, colMaxHeight]).range([colDendroHeight, 0]);

const maxAbs = d3.max(matrix.flat().map(Math.abs));
const colorScale = d3.scaleSequential(d3.interpolateRgbBasis(t.div)).domain([-maxAbs, maxAbs]);

// --- SVG mount ----------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("heatmap-clustered · javascript · d3 · anyplot.ai");

// --- Row dendrogram (left of the heatmap) --------------------------------
const rowDendro = svg
  .append("g")
  .attr("transform", `translate(${marginLeft},${heatmapY})`);
rowDendro
  .selectAll("line")
  .data(rowSegments)
  .join("line")
  .attr("x1", (d) => rowHeightScale(d.v1))
  .attr("y1", (d) => rowLeafScale(d.u1))
  .attr("x2", (d) => rowHeightScale(d.v2))
  .attr("y2", (d) => rowLeafScale(d.u2))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5)
  .attr("fill", "none");

// --- Column dendrogram (above the heatmap) -------------------------------
const colDendro = svg
  .append("g")
  .attr("transform", `translate(${heatmapX},${marginTop})`);
colDendro
  .selectAll("line")
  .data(colSegments)
  .join("line")
  .attr("x1", (d) => colLeafScale(d.u1))
  .attr("y1", (d) => colHeightScale(d.v1))
  .attr("x2", (d) => colLeafScale(d.u2))
  .attr("y2", (d) => colHeightScale(d.v2))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5)
  .attr("fill", "none");

// --- Row labels -----------------------------------------------------------
const rowLabelG = svg
  .append("g")
  .attr("transform", `translate(${marginLeft + rowDendroWidth},${heatmapY})`);
rowLabelG
  .selectAll("text")
  .data(orderedRowLabels)
  .join("text")
  .attr("x", rowLabelWidth - 10)
  .attr("y", (_, i) => yCell(i) + yCell.bandwidth() / 2)
  .attr("dy", "0.32em")
  .attr("text-anchor", "end")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text((d) => d);

// --- Column labels ----------------------------------------------------------
const colLabelG = svg
  .append("g")
  .attr("transform", `translate(${heatmapX},${heatmapY + heatmapHeight + 10})`);
colLabelG
  .selectAll("text")
  .data(orderedColLabels)
  .join("text")
  .attr(
    "transform",
    (_, j) => `translate(${xCell(j) + xCell.bandwidth() / 2},0) rotate(-40)`
  )
  .attr("text-anchor", "end")
  .attr("dy", "0.32em")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text((d) => d);

// --- Heatmap cells ----------------------------------------------------------
const heatmapG = svg.append("g").attr("transform", `translate(${heatmapX},${heatmapY})`);
const cells = [];
orderedMatrix.forEach((row, i) => {
  row.forEach((value, j) => cells.push({ i, j, value }));
});
heatmapG
  .selectAll("rect")
  .data(cells)
  .join("rect")
  .attr("x", (d) => xCell(d.j))
  .attr("y", (d) => yCell(d.i))
  .attr("width", xCell.bandwidth())
  .attr("height", yCell.bandwidth())
  .attr("fill", (d) => colorScale(d.value));

heatmapG
  .append("rect")
  .attr("x", 0)
  .attr("y", 0)
  .attr("width", heatmapWidth)
  .attr("height", heatmapHeight)
  .attr("fill", "none")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);

// --- Colorbar legend --------------------------------------------------------
const colorbarX = heatmapX + heatmapWidth + gapRight;
const colorbarSteps = d3.range(0, 1.001, 0.1);
svg
  .append("linearGradient")
  .attr("id", "imprint-div-gradient")
  .attr("x1", "0")
  .attr("x2", "0")
  .attr("y1", "1")
  .attr("y2", "0")
  .selectAll("stop")
  .data(colorbarSteps)
  .join("stop")
  .attr("offset", (d) => `${d * 100}%`)
  .attr("stop-color", (d) => colorScale(-maxAbs + d * 2 * maxAbs));

svg
  .append("rect")
  .attr("x", colorbarX)
  .attr("y", heatmapY)
  .attr("width", colorbarWidth)
  .attr("height", heatmapHeight)
  .attr("fill", "url(#imprint-div-gradient)")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);

const colorbarScale = d3.scaleLinear().domain([-maxAbs, maxAbs]).range([heatmapHeight, 0]);
const colorbarAxis = svg
  .append("g")
  .attr("transform", `translate(${colorbarX + colorbarWidth},${heatmapY})`)
  .call(d3.axisRight(colorbarScale).ticks(5).tickSize(6));
colorbarAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "13px");
colorbarAxis.selectAll("line").attr("stroke", t.grid);
colorbarAxis.select(".domain").attr("stroke", t.inkSoft);

svg
  .append("text")
  .attr(
    "transform",
    `translate(${colorbarX + colorbarWidth + colorbarAxisWidth - 6},${heatmapY + heatmapHeight / 2}) rotate(90)`
  )
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Expression (z-score)");
