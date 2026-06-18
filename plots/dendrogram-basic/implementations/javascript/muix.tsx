// anyplot.ai
// dendrogram-basic: Basic Dendrogram
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 83/100 | Created: 2026-06-18

const t = window.ANYPLOT_TOKENS;

// --- Data: Iris samples (sepal_length, sepal_width, petal_length, petal_width) ---
const samples = [
  // Setosa (5 samples)
  { label: "S-01", features: [5.1, 3.5, 1.4, 0.2], species: 0 },
  { label: "S-02", features: [4.9, 3.0, 1.4, 0.2], species: 0 },
  { label: "S-03", features: [4.7, 3.2, 1.3, 0.2], species: 0 },
  { label: "S-04", features: [5.0, 3.6, 1.4, 0.2], species: 0 },
  { label: "S-05", features: [5.4, 3.9, 1.7, 0.4], species: 0 },
  // Versicolor (5 samples)
  { label: "Ve-01", features: [7.0, 3.2, 4.7, 1.4], species: 1 },
  { label: "Ve-02", features: [6.4, 3.2, 4.5, 1.5], species: 1 },
  { label: "Ve-03", features: [6.9, 3.1, 4.9, 1.5], species: 1 },
  { label: "Ve-04", features: [5.5, 2.3, 4.0, 1.3], species: 1 },
  { label: "Ve-05", features: [6.5, 2.8, 4.6, 1.5], species: 1 },
  // Virginica (5 samples)
  { label: "Vi-01", features: [6.3, 3.3, 6.0, 2.5], species: 2 },
  { label: "Vi-02", features: [5.8, 2.7, 5.1, 1.9], species: 2 },
  { label: "Vi-03", features: [7.1, 3.0, 5.9, 2.1], species: 2 },
  { label: "Vi-04", features: [6.3, 2.9, 5.6, 1.8], species: 2 },
  { label: "Vi-05", features: [6.5, 3.0, 5.8, 2.2], species: 2 },
];

const SPECIES_COLORS = [t.palette[0], t.palette[1], t.palette[2]];
const SPECIES_NAMES = ["Iris setosa", "Iris versicolor", "Iris virginica"];

function euclid(a, b) {
  return Math.sqrt(a.features.reduce((s, v, i) => s + (v - b.features[i]) ** 2, 0));
}

// Agglomerative clustering with complete linkage
function buildTree(pts) {
  let nodes = pts.map((_, i) => ({ height: 0, leaves: [i], children: null, x: 0 }));
  while (nodes.length > 1) {
    let minD = Infinity, mi = 0, mj = 1;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        let d = 0;
        for (const li of nodes[i].leaves)
          for (const lj of nodes[j].leaves)
            d = Math.max(d, euclid(pts[li], pts[lj]));
        if (d < minD) { minD = d; mi = i; mj = j; }
      }
    }
    const merged = {
      height: minD,
      leaves: [...nodes[mi].leaves, ...nodes[mj].leaves],
      children: [nodes[mi], nodes[mj]],
      x: 0,
    };
    nodes.splice(mj, 1);
    nodes.splice(mi, 1);
    nodes.push(merged);
  }
  return nodes[0];
}

function leafOrder(node) {
  if (!node.children) return [node.leaves[0]];
  return [...leafOrder(node.children[0]), ...leafOrder(node.children[1])];
}

function assignX(node, xMap) {
  if (!node.children) { node.x = xMap[node.leaves[0]]; return; }
  assignX(node.children[0], xMap);
  assignX(node.children[1], xMap);
  node.x = (node.children[0].x + node.children[1].x) / 2;
}

function getSegments(node) {
  if (!node.children) return [];
  const [l, r] = node.children;
  return [
    { x1: l.x, y1: node.height, x2: r.x, y2: node.height },
    { x1: l.x, y1: l.height,    x2: l.x, y2: node.height },
    { x1: r.x, y1: r.height,    x2: r.x, y2: node.height },
    ...getSegments(l),
    ...getSegments(r),
  ];
}

// --- Pre-compute tree (deterministic, module-level) ---
const root = buildTree(samples);
const n = samples.length;
const order = leafOrder(root);
const xMap = {};
order.forEach((li, pos) => { xMap[li] = pos; });
assignX(root, xMap);
const maxH = root.height;
const segs = getSegments(root);

// --- Chart component ---
export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  const mg = { top: 70, right: 185, bottom: 148, left: 88 };
  const pw = W - mg.left - mg.right;
  const ph = H - mg.top - mg.bottom;

  const xScale = (pos) => mg.left + (pos / (n - 1)) * pw;
  const yScale = (h) => mg.top + ph * (1 - h / maxH);

  const leafY = yScale(0);
  const nTicks = 5;
  const yTicks = Array.from({ length: nTicks + 1 }, (_, i) => (maxH * i) / nTicks);

  return (
    <svg
      width={W}
      height={H}
      style={{ fontFamily: "system-ui, -apple-system, sans-serif", display: "block" }}
    >
      {/* Background */}
      <rect width={W} height={H} fill={t.pageBg} />

      {/* Title */}
      <text
        x={W / 2} y={44}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        dendrogram-basic · javascript · muix · anyplot.ai
      </text>

      {/* Horizontal grid lines at distance ticks */}
      {yTicks.map((h, i) => (
        <line
          key={i}
          x1={mg.left} y1={yScale(h)}
          x2={mg.left + pw} y2={yScale(h)}
          stroke={t.grid} strokeWidth={1}
        />
      ))}

      {/* Dendrogram branches */}
      {segs.map((s, i) => (
        <line
          key={i}
          x1={xScale(s.x1)} y1={yScale(s.y1)}
          x2={xScale(s.x2)} y2={yScale(s.y2)}
          stroke={t.ink}
          strokeWidth={2}
          strokeLinecap="round"
        />
      ))}

      {/* Leaf dots colored by species */}
      {order.map((li, pos) => (
        <circle
          key={pos}
          cx={xScale(pos)}
          cy={leafY}
          r={6}
          fill={SPECIES_COLORS[samples[li].species]}
        />
      ))}

      {/* Leaf labels rotated -45° */}
      {order.map((li, pos) => (
        <text
          key={pos}
          x={0}
          y={0}
          textAnchor="end"
          fontSize={13}
          fill={SPECIES_COLORS[samples[li].species]}
          transform={`translate(${xScale(pos)}, ${leafY + 14}) rotate(-45)`}
        >
          {samples[li].label}
        </text>
      ))}

      {/* Y-axis spine */}
      <line
        x1={mg.left} y1={mg.top}
        x2={mg.left} y2={mg.top + ph}
        stroke={t.inkSoft} strokeWidth={1.5}
      />

      {/* Y-axis ticks and labels */}
      {yTicks.map((h, i) => (
        <g key={i}>
          <line
            x1={mg.left - 6} y1={yScale(h)}
            x2={mg.left} y2={yScale(h)}
            stroke={t.inkSoft} strokeWidth={1.5}
          />
          <text
            x={mg.left - 10}
            y={yScale(h) + 5}
            textAnchor="end"
            fontSize={13}
            fill={t.inkSoft}
          >
            {h.toFixed(2)}
          </text>
        </g>
      ))}

      {/* Y-axis label */}
      <text
        textAnchor="middle"
        fontSize={15}
        fill={t.ink}
        transform={`translate(${22}, ${mg.top + ph / 2}) rotate(-90)`}
      >
        Distance (Complete Linkage)
      </text>

      {/* Legend */}
      {SPECIES_NAMES.map((name, i) => (
        <g key={i} transform={`translate(${W - mg.right + 22}, ${mg.top + 24 + i * 30})`}>
          <circle cx={8} cy={0} r={7} fill={SPECIES_COLORS[i]} />
          <text x={22} y={5} fontSize={14} fill={t.ink}>{name}</text>
        </g>
      ))}
    </svg>
  );
}
