// anyplot.ai
// circlepacking-basic: Circle Packing Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-02
//# anyplot-orientation: square

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

// --- Budget rollups (for tooltips: every node, not just leaves, gets a $ total) --
const computeTotal = (node) => {
  node.total = node.children.length === 0 ? node.value : node.children.reduce((sum, c) => sum + computeTotal(c), 0);
  return node.total;
};
computeTotal(root);

// --- Solid depth-2 fill: mix the hue with a fixed literal (not the theme
// background) so the composited pixel color is identical in both themes —
// canvas alpha over a theme-dependent backdrop would otherwise drift.
const hexToRgb = (hex) => [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
const mixColor = (hexA, hexB, ratio) => {
  const a = hexToRgb(hexA);
  const b = hexToRgb(hexB);
  return `#${a.map((v, i) => Math.round(v * ratio + b[i] * (1 - ratio)).toString(16).padStart(2, "0")).join("")}`;
};

// --- Flatten with depth-based Imprint coloring ------------------------------
// Divisions (depth 1) take Imprint positions 1-4 in declared order; leaves
// (depth 2) inherit their division's hue, darkened by a fixed literal ratio
// (not theme-dependent alpha) to read as nested.
const flatData = [];
const flatten = (node, depth, color) => {
  flatData.push({
    x: node.absX,
    y: node.absY,
    r: node.r,
    depth,
    label: node.label,
    amount: node.total,
    color,
    parentId: node.parent,
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
      metric: Infinity, // division rims are reserved space, never evicted by a leaf
      text: d.label,
      maxFontSize: DIVISION_FONT,
      minFontSize: DIVISION_FONT,
      bold: true,
      charW: 0.62,
      positions: [{ dx: 0, dy: -d.r * 0.62 }],
    });
  } else {
    if (rPx < 34) return;
    const fontSize = Math.min(LEAF_FONT_MAX, Math.max(LEAF_FONT_MIN, rPx * 0.34));
    labelCandidates.push({
      idx,
      metric: d.r, // real circle size, so bigger-value leaves always get first claim
      text: d.label,
      maxFontSize: fontSize,
      minFontSize: LEAF_FONT_MIN * 0.75,
      bold: false,
      charW: 0.56,
      // Own center first, then a few nudges toward the circle's own rim —
      // enough freedom to dodge a bigger neighbor's box without drifting
      // onto a sibling circle.
      positions: [
        { dx: 0, dy: 0 },
        { dx: 0, dy: -d.r * 0.45 },
        { dx: 0, dy: d.r * 0.45 },
        { dx: -d.r * 0.4, dy: 0 },
        { dx: d.r * 0.4, dy: 0 },
      ],
    });
  }
});
// Larger circles claim label space first.
labelCandidates.sort((a, b) => b.metric - a.metric);

const placedRects = [];
const rectsOverlap = (a, b) => !(a.x2 < b.x1 || a.x1 > b.x2 || a.y2 < b.y1 || a.y1 > b.y2);
const boxFor = (cand, cx, cy, fontSize) => {
  const wUnits = (cand.text.length * fontSize * cand.charW + 8) / pxPerUnit;
  const hUnits = (fontSize * 1.3 + 6) / pxPerUnit;
  return { x1: cx - wUnits / 2, x2: cx + wUnits / 2, y1: cy - hUnits / 2, y2: cy + hUnits / 2 };
};
const acceptLabel = (cand, node, fontSize, rect, pos) => {
  placedRects.push({ ...rect, metric: cand.metric, idx: cand.idx });
  node.showLabel = true;
  node.labelFontSize = fontSize;
  node.labelBold = cand.bold;
  node.labelYOffsetUnits = pos.dy;
  node.labelXOffsetUnits = pos.dx;
  node.labelCharW = cand.charW;
};
// Every position is tried at full size before any position is tried at a
// smaller size (nudging beats shrinking); only the primary (center) position
// at full size may evict an already-placed label, and only if every
// colliding label belongs to a strictly smaller circle — long names are the
// usual reason a big circle's default box collides where a shorter-named
// smaller sibling's box does not.
const tryPlace = (cand, node, allowEvict) => {
  for (let fontSize = cand.maxFontSize; fontSize >= cand.minFontSize; fontSize -= 1) {
    for (let p = 0; p < cand.positions.length; p += 1) {
      const pos = cand.positions[p];
      const cx = node.x + pos.dx;
      const cy = node.y + pos.dy;
      const rect = boxFor(cand, cx, cy, fontSize);
      const collisions = placedRects.filter((r) => rectsOverlap(rect, r));
      if (collisions.length === 0) {
        acceptLabel(cand, node, fontSize, rect, pos);
        return true;
      }
      if (allowEvict && p === 0 && fontSize === cand.maxFontSize && collisions.every((r) => r.metric < cand.metric)) {
        collisions.forEach((r) => placedRects.splice(placedRects.indexOf(r), 1));
        acceptLabel(cand, node, fontSize, rect, pos);
        return true;
      }
    }
  }
  return false;
};

const candByIdx = {};
labelCandidates.forEach((cand) => {
  candByIdx[cand.idx] = cand;
  tryPlace(cand, flatData[cand.idx], true);
});

// Local-monotonicity repair: a bigger leaf can still lose its label slot to
// an even-bigger sibling's box, while a smaller sibling elsewhere happens to
// sit in open space and keeps its label — within one parent cluster, evict
// that smaller sibling's label and retry the bigger circle in the freed space
// so a reader never sees "smaller labeled, bigger not" inside the same circle.
const leafByParent = {};
flatData.forEach((d, idx) => {
  if (d.depth === 2) (leafByParent[d.parentId] ||= []).push(idx);
});
Object.values(leafByParent).forEach((siblingIdxs) => {
  const bySizeDesc = siblingIdxs.slice().sort((a, b) => flatData[b].r - flatData[a].r);
  bySizeDesc.forEach((idx) => {
    const node = flatData[idx];
    if (node.showLabel) return;
    const cand = candByIdx[idx];
    if (!cand) return;
    const victimIdx = siblingIdxs.find((j) => flatData[j].showLabel && flatData[j].r < node.r);
    if (victimIdx === undefined) return;
    const rectPos = placedRects.findIndex((r) => r.idx === victimIdx);
    if (rectPos === -1) return;
    const savedRect = placedRects[rectPos];
    placedRects.splice(rectPos, 1);
    if (tryPlace(cand, node, false)) {
      flatData[victimIdx].showLabel = false;
    } else {
      placedRects.push(savedRect);
    }
  });
});

const seriesData = flatData.map((d) => {
  if (d.depth === 0) {
    return {
      value: [d.x, d.y, d.r],
      itemStyle: { color: "transparent", borderColor: t.inkSoft, borderWidth: 1.5, opacity: 0.4 },
      label: d.label,
      amount: d.amount,
    };
  }
  if (d.depth === 1) {
    return {
      value: [d.x, d.y, d.r],
      itemStyle: { color: d.color, opacity: 0.85, borderColor: t.pageBg, borderWidth: 2.5 },
      label: d.label,
      amount: d.amount,
    };
  }
  // Solid literal-mixed fill (not canvas alpha over the theme background) so
  // the composited leaf color is pixel-identical between light and dark.
  return {
    value: [d.x, d.y, d.r],
    itemStyle: { color: mixColor(d.color, "#000000", 0.82), opacity: 1, borderColor: t.pageBg, borderWidth: 1.2 },
    label: d.label,
    amount: d.amount,
  };
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
  const labelCenter = api.coord([api.value(0) + raw.labelXOffsetUnits, api.value(1) + raw.labelYOffsetUnits]);
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
  // Recovers labels dropped by the static collision-avoidance layout: any
  // circle (labeled or not) shows its name + budget on hover.
  tooltip: {
    trigger: "item",
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink, fontSize: 14 },
    formatter: (params) => (params.data && params.data.amount != null ? `<strong>${params.data.label}</strong><br/>$${params.data.amount}M` : ""),
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
      tooltip: { show: false },
      clip: false,
    },
  ],
});
