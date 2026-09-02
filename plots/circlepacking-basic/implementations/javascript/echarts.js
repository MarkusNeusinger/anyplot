// anyplot.ai
// circlepacking-basic: Circle Packing Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-02
//# anyplot-orientation: square
// anyplot.ai
// circlepacking-basic: Circle Packing Chart
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data: R&D budget hierarchy (root -> division -> team), $ millions -----
const records = [
  { id: "root", parent: null, value: null, label: "R&D Portfolio" },
  { id: "cloud", parent: "root", value: null, label: "Cloud Platform" },
  { id: "ai", parent: "root", value: null, label: "AI Research" },
  { id: "hardware", parent: "root", value: null, label: "Hardware Engineering" },
  { id: "mobile", parent: "root", value: null, label: "Mobile Apps" },

  { id: "cloud-compute", parent: "cloud", value: 18, label: "Compute Infra" },
  { id: "cloud-storage", parent: "cloud", value: 12, label: "Storage Systems" },
  { id: "cloud-network", parent: "cloud", value: 9, label: "Networking" },
  { id: "cloud-k8s", parent: "cloud", value: 15, label: "Kubernetes Platform" },
  { id: "cloud-db", parent: "cloud", value: 11, label: "Database Services" },
  { id: "cloud-devops", parent: "cloud", value: 7, label: "DevOps Tooling" },

  { id: "ai-llm", parent: "ai", value: 26, label: "Large Language Models" },
  { id: "ai-vision", parent: "ai", value: 14, label: "Computer Vision" },
  { id: "ai-rl", parent: "ai", value: 8, label: "Reinforcement Learning" },
  { id: "ai-mlops", parent: "ai", value: 10, label: "MLOps" },
  { id: "ai-labeling", parent: "ai", value: 6, label: "Data Labeling" },
  { id: "ai-safety", parent: "ai", value: 9, label: "AI Safety" },

  { id: "hw-chip", parent: "hardware", value: 22, label: "Chip Design" },
  { id: "hw-sensors", parent: "hardware", value: 10, label: "Sensors" },
  { id: "hw-power", parent: "hardware", value: 7, label: "Power Systems" },
  { id: "hw-thermal", parent: "hardware", value: 6, label: "Thermal Engineering" },
  { id: "hw-proto", parent: "hardware", value: 9, label: "Prototyping Lab" },
  { id: "hw-qa", parent: "hardware", value: 5, label: "Quality Testing" },

  { id: "mob-ios", parent: "mobile", value: 13, label: "iOS Development" },
  { id: "mob-android", parent: "mobile", value: 13, label: "Android Development" },
  { id: "mob-sdk", parent: "mobile", value: 8, label: "Cross-platform SDK" },
  { id: "mob-analytics", parent: "mobile", value: 5, label: "App Analytics" },
  { id: "mob-ux", parent: "mobile", value: 6, label: "UX Research" },
  { id: "mob-push", parent: "mobile", value: 4, label: "Push Notifications" },
];

// --- Build the tree ----------------------------------------------------
const byId = {};
records.forEach((rec) => {
  byId[rec.id] = { ...rec, children: [] };
});
records.forEach((rec) => {
  if (rec.parent !== null) byId[rec.parent].children.push(byId[rec.id]);
});
const root = byId.root;

// --- Circle packing: deterministic spiral seed + iterative repulsion -------
// (per spec notes: "pack circles efficiently using force simulation";
// no d3/library layout is used — this is a from-scratch physical relaxation)
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));
const PADDING = 0.15;
const ITERATIONS = 400;

const packCircles = (nodes) => {
  const n = nodes.length;
  if (n === 0) return 0;
  if (n === 1) {
    nodes[0].x = 0;
    nodes[0].y = 0;
    return nodes[0].r;
  }
  const sorted = nodes.slice().sort((a, b) => b.r - a.r);
  sorted.forEach((node, i) => {
    const spiralR = 2.2 * Math.sqrt(i) * (sorted[0].r + 0.4);
    node.x = spiralR * Math.cos(i * GOLDEN_ANGLE);
    node.y = spiralR * Math.sin(i * GOLDEN_ANGLE);
  });
  for (let iter = 0; iter < ITERATIONS; iter += 1) {
    for (let i = 0; i < n; i += 1) {
      const a = sorted[i];
      for (let j = i + 1; j < n; j += 1) {
        const b = sorted[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 0.0001;
        const minDist = a.r + b.r + PADDING;
        if (dist < minDist) {
          const overlap = (minDist - dist) / 2;
          const nx = dx / dist;
          const ny = dy / dist;
          a.x -= nx * overlap;
          a.y -= ny * overlap;
          b.x += nx * overlap;
          b.y += ny * overlap;
        }
      }
    }
    for (let i = 0; i < n; i += 1) {
      sorted[i].x *= 0.993;
      sorted[i].y *= 0.993;
    }
  }
  let enclosing = 0;
  for (let i = 0; i < n; i += 1) {
    const d = Math.sqrt(sorted[i].x * sorted[i].x + sorted[i].y * sorted[i].y) + sorted[i].r;
    if (d > enclosing) enclosing = d;
  }
  return enclosing + PADDING * 2;
};

// Leaf radius scales with sqrt(value) so area (not radius) encodes value.
// Internal-node radius is the enclosing circle of its packed children.
const layoutNode = (node) => {
  if (node.children.length === 0) {
    node.r = Math.sqrt(node.value);
    return;
  }
  node.children.forEach(layoutNode);
  node.r = packCircles(node.children);
};
layoutNode(root);

const placeAbsolute = (node, ox, oy) => {
  node.absX = ox;
  node.absY = oy;
  node.children.forEach((child) => placeAbsolute(child, ox + child.x, oy + child.y));
};
placeAbsolute(root, 0, 0);

// --- Flatten with depth-based Imprint coloring ------------------------------
// Divisions (depth 1) take Imprint positions 1-4 in declared order; leaves
// (depth 2) inherit their division's hue at lower opacity to read as nested.
const flatData = [];
const flatten = (node, depth, color) => {
  flatData.push({
    x: node.absX,
    y: node.absY,
    r: node.r,
    depth,
    label: node.label,
    color,
  });
  node.children.forEach((child, idx) => {
    const childColor = depth === 0 ? t.palette[idx % t.palette.length] : color;
    flatten(child, depth + 1, childColor);
  });
};
flatten(root, 0, t.muted);

// --- Label layout: precompute placement + collision avoidance --------------
// The packing algorithm seeds each group's largest circle at the local
// origin, which coincides with the parent's own center — so a naive
// centered label would collide with its biggest child every time. Instead:
// division labels sit near the rim (the packed children leave that area
// empty by construction, since PADDING pads the enclosing radius), leaf
// labels sit on their own circle, and every candidate is rejected if its
// estimated box collides with an already-accepted one (bigger leaves win).
const domain = root.r * 1.06;
const mountSize = window.ANYPLOT_SIZE;
const GRID_LR = 0.09;
const GRID_TOP = 0.12;
const GRID_BOTTOM = 0.06;
const gridPx = Math.min(mountSize.width * (1 - GRID_LR * 2), mountSize.height * (1 - GRID_TOP - GRID_BOTTOM));
const pxPerUnit = gridPx / (2 * domain);

const DIVISION_FONT = 22;
const LEAF_FONT_MIN = 12;
const LEAF_FONT_MAX = 17;

const labelCandidates = [];
flatData.forEach((d, idx) => {
  if (d.depth === 0) return;
  const rPx = d.r * pxPerUnit;
  if (d.depth === 1) {
    if (rPx < 60) return;
    labelCandidates.push({
      idx,
      priority: 0,
      text: d.label,
      fontSize: DIVISION_FONT,
      bold: true,
      yOffsetUnits: -d.r * 0.62,
      charW: 0.62,
    });
  } else {
    if (rPx < 34) return;
    const fontSize = Math.min(LEAF_FONT_MAX, Math.max(LEAF_FONT_MIN, rPx * 0.34));
    labelCandidates.push({
      idx,
      priority: 1 / rPx,
      text: d.label,
      fontSize,
      bold: false,
      yOffsetUnits: 0,
      charW: 0.56,
    });
  }
});
labelCandidates.sort((a, b) => a.priority - b.priority);

const placedRects = [];
const rectsOverlap = (a, b) => !(a.x2 < b.x1 || a.x1 > b.x2 || a.y2 < b.y1 || a.y1 > b.y2);
labelCandidates.forEach((cand) => {
  const node = flatData[cand.idx];
  const cx = node.x;
  const cy = node.y + cand.yOffsetUnits;
  const wUnits = (cand.text.length * cand.fontSize * cand.charW + 8) / pxPerUnit;
  const hUnits = (cand.fontSize * 1.3 + 6) / pxPerUnit;
  const rect = { x1: cx - wUnits / 2, x2: cx + wUnits / 2, y1: cy - hUnits / 2, y2: cy + hUnits / 2 };
  if (placedRects.some((r) => rectsOverlap(rect, r))) return;
  placedRects.push(rect);
  node.showLabel = true;
  node.labelFontSize = cand.fontSize;
  node.labelBold = cand.bold;
  node.labelYOffsetUnits = cand.yOffsetUnits;
  node.labelCharW = cand.charW;
});

const seriesData = flatData.map((d) => {
  if (d.depth === 0) {
    return { value: [d.x, d.y, d.r], itemStyle: { color: "transparent", borderColor: t.inkSoft, borderWidth: 1.5, opacity: 0.4 } };
  }
  if (d.depth === 1) {
    return { value: [d.x, d.y, d.r], itemStyle: { color: d.color, opacity: 0.85, borderColor: t.pageBg, borderWidth: 2.5 } };
  }
  return { value: [d.x, d.y, d.r], itemStyle: { color: d.color, opacity: 0.5, borderColor: t.pageBg, borderWidth: 1.2 } };
});

// --- Custom-series renderers -----------------------------------------------
// Circles and labels are two separate series (circles drawn first, labels
// second) so every label chip paints on top of ALL circles — a label must
// never be covered by a sibling/child circle drawn later in tree order.
const renderCircle = (params, api) => {
  const center = api.coord([api.value(0), api.value(1)]);
  const rPixel = api.size([api.value(2), 0])[0];
  return { type: "circle", shape: { cx: center[0], cy: center[1], r: rPixel }, style: api.style() };
};

const labeledNodes = flatData.filter((d) => d.showLabel);
const labelSeriesData = labeledNodes.map((d) => ({ value: [d.x, d.y] }));

const renderLabel = (params, api) => {
  const raw = labeledNodes[params.dataIndex];
  const labelCenter = api.coord([api.value(0), api.value(1) + raw.labelYOffsetUnits]);
  const w = raw.label.length * raw.labelFontSize * raw.labelCharW + 8;
  const h = raw.labelFontSize * 1.3 + 6;
  return {
    type: "group",
    children: [
      {
        type: "rect",
        shape: { x: labelCenter[0] - w / 2, y: labelCenter[1] - h / 2, width: w, height: h, r: 3 },
        style: { fill: t.elevatedBg },
      },
      {
        type: "text",
        style: {
          text: raw.label,
          x: labelCenter[0],
          y: labelCenter[1],
          fill: t.ink,
          fontSize: raw.labelFontSize,
          fontWeight: raw.labelBold ? 600 : 500,
          textAlign: "center",
          textVerticalAlign: "middle",
        },
      },
    ],
  };
};

// --- Chart -------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "circlepacking-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  grid: { left: "9%", right: "9%", top: "12%", bottom: "6%" },
  xAxis: { type: "value", min: -domain, max: domain, show: false, splitLine: { show: false } },
  yAxis: { type: "value", min: -domain, max: domain, show: false, splitLine: { show: false } },
  series: [
    {
      type: "custom",
      coordinateSystem: "cartesian2d",
      renderItem: renderCircle,
      data: seriesData,
      clip: false,
    },
    {
      type: "custom",
      coordinateSystem: "cartesian2d",
      renderItem: renderLabel,
      data: labelSeriesData,
      clip: false,
    },
  ],
});
