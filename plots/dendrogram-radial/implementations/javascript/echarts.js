// anyplot.ai
// dendrogram-radial: Radial Dendrogram
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-04

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// --- Data: synthetic tissue samples, 4 groups, 2D expression-like features --
function lcg(seed) {
  let s = seed >>> 0;
  return function () {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}
const rand = lcg(42);

const CLUSTER_NAMES = ["Liver", "Heart", "Brain", "Kidney"];
const CLUSTER_CENTERS = [
  [-3, -2],
  [3, -2],
  [-3, 3],
  [3, 3],
];
const LEAVES_PER_CLUSTER = 8;

const leaves = [];
CLUSTER_NAMES.forEach((name, clusterId) => {
  const [cx0, cy0] = CLUSTER_CENTERS[clusterId];
  for (let k = 1; k <= LEAVES_PER_CLUSTER; k++) {
    leaves.push({
      id: leaves.length,
      label: `${name}-${String(k).padStart(2, "0")}`,
      cluster: clusterId,
      x: cx0 + (rand() - 0.5) * 3,
      y: cy0 + (rand() - 0.5) * 3,
    });
  }
});
const leafCount = leaves.length;

// --- Hierarchical clustering (UPGMA / average linkage) -----------------------
function euclidean(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}
const distKey = (a, b) => (a < b ? `${a}_${b}` : `${b}_${a}`);
const distances = new Map();
for (let i = 0; i < leafCount; i++) {
  for (let j = i + 1; j < leafCount; j++) {
    distances.set(distKey(i, j), euclidean(leaves[i], leaves[j]));
  }
}

const nodes = new Map();
leaves.forEach((leaf) => {
  nodes.set(leaf.id, { id: leaf.id, isLeaf: true, label: leaf.label, cluster: leaf.cluster, size: 1, height: 0 });
});

let active = leaves.map((leaf) => leaf.id);
let nextId = leafCount;
const merges = [];

while (active.length > 1) {
  let bestA = -1;
  let bestB = -1;
  let bestDist = Infinity;
  for (let i = 0; i < active.length; i++) {
    for (let j = i + 1; j < active.length; j++) {
      const d = distances.get(distKey(active[i], active[j]));
      if (d < bestDist) {
        bestDist = d;
        bestA = active[i];
        bestB = active[j];
      }
    }
  }
  const nodeA = nodes.get(bestA);
  const nodeB = nodes.get(bestB);
  const merged = {
    id: nextId,
    isLeaf: false,
    left: bestA,
    right: bestB,
    size: nodeA.size + nodeB.size,
    height: bestDist,
    cluster: nodeA.cluster === nodeB.cluster ? nodeA.cluster : null,
  };
  nodes.set(nextId, merged);

  active
    .filter((c) => c !== bestA && c !== bestB)
    .forEach((c) => {
      const dAC = distances.get(distKey(bestA, c));
      const dBC = distances.get(distKey(bestB, c));
      distances.set(distKey(nextId, c), (nodeA.size * dAC + nodeB.size * dBC) / merged.size);
    });

  active = active.filter((c) => c !== bestA && c !== bestB).concat(nextId);
  merges.push(merged);
  nextId++;
}

const root = merges[merges.length - 1];
const maxHeight = root.height;

// --- Radial layout: leaves at equal angles, radius ~ merge distance --------
const angleStep = (2 * Math.PI) / leafCount;
let leafCursor = 0;
function assignAngle(id) {
  const node = nodes.get(id);
  if (node.isLeaf) {
    node.angle = -Math.PI / 2 + leafCursor * angleStep;
    leafCursor++;
    return node.angle;
  }
  const leftAngle = assignAngle(node.left);
  const rightAngle = assignAngle(node.right);
  node.angle = (leftAngle + rightAngle) / 2;
  return node.angle;
}
assignAngle(root.id);

const cx = size.width / 2;
const cy = size.height / 2 + 22;
const rMax = Math.min(size.width, size.height) / 2 - 190;
const rRing = rMax + 18;
const rLabel = rMax + 34;

function radiusOf(node) {
  return rMax * (1 - node.height / maxHeight);
}
function toPoint(angle, r) {
  return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
}

const clusterColors = t.palette.slice(0, CLUSTER_NAMES.length);
function branchColor(node) {
  return node.cluster !== null && node.cluster !== undefined ? clusterColors[node.cluster] : t.inkSoft;
}

// --- Graphic elements: elbow-connected radial branches ----------------------
const elements = [];

function addBranch(parent, childId) {
  const child = nodes.get(childId);
  const rParent = radiusOf(parent);
  const rChild = radiusOf(child);
  const color = branchColor(child);
  const a1 = Math.min(parent.angle, child.angle);
  const a2 = Math.max(parent.angle, child.angle);

  elements.push({
    type: "arc",
    shape: { cx, cy, r: rParent, startAngle: a1, endAngle: a2 },
    style: { stroke: color, fill: "none", lineWidth: 2.4 },
    silent: true,
  });
  const [sx, sy] = toPoint(child.angle, rParent);
  const [ex, ey] = toPoint(child.angle, rChild);
  elements.push({
    type: "line",
    shape: { x1: sx, y1: sy, x2: ex, y2: ey },
    style: { stroke: color, lineWidth: 2.4 },
    silent: true,
  });
}
merges.forEach((merge) => {
  addBranch(merge, merge.left);
  addBranch(merge, merge.right);
});

elements.push({ type: "circle", shape: { cx, cy, r: 5 }, style: { fill: t.ink }, silent: true });

// --- Outer metadata ring + leaf labels ---------------------------------------
leaves.forEach((leaf) => {
  const node = nodes.get(leaf.id);
  const ringHalf = angleStep * 0.36;
  elements.push({
    type: "arc",
    shape: { cx, cy, r: rRing, startAngle: node.angle - ringHalf, endAngle: node.angle + ringHalf },
    style: { stroke: clusterColors[leaf.cluster], lineWidth: 6, opacity: 0.85 },
    silent: true,
  });

  const [lx, ly] = toPoint(node.angle, rLabel);
  const onLeft = Math.cos(node.angle) < -0.001;
  elements.push({
    type: "text",
    x: lx,
    y: ly,
    rotation: onLeft ? node.angle + Math.PI : node.angle,
    style: {
      text: leaf.label,
      fill: t.inkSoft,
      fontSize: 13,
      align: onLeft ? "right" : "left",
      verticalAlign: "middle",
    },
    silent: true,
  });
});

// --- Legend (top-left, outside the circle's footprint) ----------------------
CLUSTER_NAMES.forEach((name, i) => {
  const y = 78 + i * 30;
  elements.push({ type: "rect", shape: { x: 30, y, width: 18, height: 18 }, style: { fill: clusterColors[i] }, silent: true });
  elements.push({
    type: "text",
    x: 56,
    y: y + 9,
    style: { text: name, fill: t.inkSoft, fontSize: 15, align: "left", verticalAlign: "middle" },
    silent: true,
  });
});

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "dendrogram-radial · javascript · echarts · anyplot.ai",
    left: "center",
    top: 16,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  graphic: { elements },
});
