// anyplot.ai
// circlepacking-basic: Circle Packing Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 88/100 | Updated: 2026-10-24
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";
import { ChartsText } from "@mui/x-charts/ChartsText";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "circlepacking-basic · javascript · muix · anyplot.ai";
const MARGIN = { top: 16, right: 24, bottom: 24, left: 24 };
const HEADER_HEIGHT = 136;
const LEAF_RADIUS_SCALE = 8;
const SIBLING_PADDING_RATIO = 0.06;
const PARENT_PADDING_RATIO = 0.08;
const PACK_ATTRACTION = 0.02;
const PACK_ITERATIONS = 400;
const SEED_SPREAD = 1.4;
const INNER_FILL_OPACITY = 0.14;
const LEAF_FILL_OPACITY = 0.92;

// Columns: set these to your data's column names
const ID = "Node ID"; // role: id
const PARENT = "Parent ID"; // role: parent
const LABEL = "Asset class / holding"; // role: label
const VALUE = "Market value ($K)"; // role: value

// Data: replace this block with your own records
const data = [
  { [ID]: "portfolio", [PARENT]: null, [LABEL]: "Portfolio", [VALUE]: null },
  { [ID]: "equities", [PARENT]: "portfolio", [LABEL]: "Equities", [VALUE]: null },
  { [ID]: "us-large-cap", [PARENT]: "equities", [LABEL]: "US Large Cap", [VALUE]: 420 },
  { [ID]: "us-small-cap", [PARENT]: "equities", [LABEL]: "US Small Cap", [VALUE]: 140 },
  { [ID]: "intl-developed", [PARENT]: "equities", [LABEL]: "Int'l Developed", [VALUE]: 210 },
  { [ID]: "emerging-markets", [PARENT]: "equities", [LABEL]: "Emerging Markets", [VALUE]: 95 },
  { [ID]: "fixed-income", [PARENT]: "portfolio", [LABEL]: "Fixed Income", [VALUE]: null },
  { [ID]: "gov-bonds", [PARENT]: "fixed-income", [LABEL]: "Government Bonds", [VALUE]: 260 },
  { [ID]: "corp-bonds", [PARENT]: "fixed-income", [LABEL]: "Corporate Bonds", [VALUE]: 180 },
  { [ID]: "muni-bonds", [PARENT]: "fixed-income", [LABEL]: "Municipal Bonds", [VALUE]: 90 },
  { [ID]: "real-estate", [PARENT]: "portfolio", [LABEL]: "Real Estate", [VALUE]: null },
  { [ID]: "reits", [PARENT]: "real-estate", [LABEL]: "REITs", [VALUE]: 150 },
  { [ID]: "direct-property", [PARENT]: "real-estate", [LABEL]: "Direct Property", [VALUE]: 110 },
  { [ID]: "alternatives", [PARENT]: "portfolio", [LABEL]: "Alternatives", [VALUE]: null },
  { [ID]: "private-equity", [PARENT]: "alternatives", [LABEL]: "Private Equity", [VALUE]: 130 },
  { [ID]: "commodities", [PARENT]: "alternatives", [LABEL]: "Commodities", [VALUE]: 70 },
  { [ID]: "hedge-funds", [PARENT]: "alternatives", [LABEL]: "Hedge Funds", [VALUE]: 85 },
  { [ID]: "cash", [PARENT]: "portfolio", [LABEL]: "Cash & Equivalents", [VALUE]: null },
  { [ID]: "money-market", [PARENT]: "cash", [LABEL]: "Money Market", [VALUE]: 60 },
  { [ID]: "treasury-bills", [PARENT]: "cash", [LABEL]: "Treasury Bills", [VALUE]: 40 },
];

// Plot: reads only data and the constants above
const VALUE_UNIT = VALUE.match(/\(([^)]+)\)/)?.[1] ?? "";
const unitSuffix = VALUE_UNIT ? ` ${VALUE_UNIT}` : "";

const nodes = data.map((row) => ({
  id: String(row[ID]),
  parent: row[PARENT] == null ? null : String(row[PARENT]),
  label: String(row[LABEL]),
  value: Number(row[VALUE] ?? 0),
  children: [] as any[],
  depth: 0,
  x: 0,
  y: 0,
  r: 0,
  cx: 0,
  cy: 0,
  color: t.palette[0],
  ink: "#1A1A17",
  lines: [String(row[LABEL])],
}));

const byId = new Map(nodes.map((n) => [n.id, n]));
let root = nodes[0];
for (const node of nodes) {
  if (node.parent == null) {
    root = node;
  } else {
    byId.get(node.parent)?.children.push(node);
  }
}

const order = [root];
for (let i = 0; i < order.length; i++) {
  const curr = order[i];
  for (const child of curr.children) {
    child.depth = curr.depth + 1;
    order.push(child);
  }
}

root.children.forEach((branch, i) => {
  branch.color = t.palette[i];
});
for (const node of order) {
  if (node.depth > 1 && node.parent != null) {
    const parentNode = byId.get(node.parent);
    if (parentNode) node.color = parentNode.color;
  }
  const hexNum = parseInt(node.color.slice(1), 16);
  const rgb = [(hexNum >> 16) & 255, (hexNum >> 8) & 255, hexNum & 255];
  const lin = rgb.map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  const lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
  node.ink = lum > 0.18 ? "#1A1A17" : "#FAF8F1";

  const words = node.label.split(" ");
  if (words.length <= 1 || node.label.length <= 10) {
    node.lines = [node.label];
  } else {
    let best = [node.label];
    let bestDiff = Infinity;
    for (let k = 1; k < words.length; k++) {
      const l1 = words.slice(0, k).join(" ");
      const l2 = words.slice(k).join(" ");
      const diff = Math.abs(l1.length - l2.length);
      if (diff < bestDiff) {
        bestDiff = diff;
        best = [l1, l2];
      }
    }
    node.lines = best;
  }
}

let lcgState = 42;
for (let idx = order.length - 1; idx >= 0; idx--) {
  const node = order[idx];
  if (node.children.length === 0) {
    node.r = LEAF_RADIUS_SCALE * Math.sqrt(node.value);
    continue;
  }
  node.value = node.children.reduce((sum, c) => sum + c.value, 0);
  const children = node.children;
  const sorted = [...children].sort((a, b) => b.r - a.r);
  const meanChildR = children.reduce((sum, c) => sum + c.r, 0) / children.length;
  const siblingPad = meanChildR * SIBLING_PADDING_RATIO;
  const seedRadius = sorted[0].r * SEED_SPREAD;

  sorted.forEach((c, i) => {
    const angle = (2 * Math.PI * i) / sorted.length;
    lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
    const jx = (lcgState / 4294967296 - 0.5) * 4;
    lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
    const jy = (lcgState / 4294967296 - 0.5) * 4;
    c.x = Math.cos(angle) * seedRadius + jx;
    c.y = Math.sin(angle) * seedRadius + jy;
  });

  for (let iter = 0; iter < PACK_ITERATIONS; iter++) {
    for (const c of children) {
      c.x -= c.x * PACK_ATTRACTION;
      c.y -= c.y * PACK_ATTRACTION;
    }
    for (let i = 0; i < children.length; i++) {
      for (let j = i + 1; j < children.length; j++) {
        const a = children[i];
        const b = children[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.hypot(dx, dy) || 0.01;
        const minDist = a.r + b.r + siblingPad;
        if (dist < minDist) {
          const overlap = (minDist - dist) / 2;
          const ux = dx / dist;
          const uy = dy / dist;
          a.x -= ux * overlap;
          a.y -= uy * overlap;
          b.x += ux * overlap;
          b.y += uy * overlap;
        }
      }
    }
  }

  const minX = Math.min(...children.map((c) => c.x - c.r));
  const maxX = Math.max(...children.map((c) => c.x + c.r));
  const minY = Math.min(...children.map((c) => c.y - c.r));
  const maxY = Math.max(...children.map((c) => c.y + c.r));
  const shiftX = (minX + maxX) / 2;
  const shiftY = (minY + maxY) / 2;
  for (const c of children) {
    c.x -= shiftX;
    c.y -= shiftY;
  }

  let enclosing = 0;
  for (const c of children) {
    enclosing = Math.max(enclosing, Math.hypot(c.x, c.y) + c.r);
  }
  node.r = enclosing * (1 + PARENT_PADDING_RATIO);
}

for (const node of order) {
  for (const child of node.children) {
    child.cx = node.cx + child.x;
    child.cy = node.cy + child.y;
  }
}

const SUBTITLE = `${root.label} · ${root.children.length} groups · total ${root.value.toLocaleString()}${unitSuffix} · circle area ∝ ${VALUE}`;

function CirclePacking() {
  const { left, top, width, height } = useDrawingArea();
  const availableRadius = Math.min(width, height) / 2 - 4;
  const scale = availableRadius / root.r;
  const originX = left + width / 2;
  const originY = top + height / 2;

  return (
    <g>
      {order.map((node) => {
        const nCx = originX + node.cx * scale;
        const nCy = originY + node.cy * scale;
        const nR = node.r * scale;
        const formattedVal = `${node.value.toLocaleString()}${unitSuffix}`;

        if (node.depth === 0) {
          return (
            <circle
              key={node.id}
              cx={nCx}
              cy={nCy}
              r={nR}
              fill="none"
              stroke={t.inkSoft}
              strokeOpacity={0.35}
              strokeWidth={1.5}
            />
          );
        }

        if (node.children.length > 0) {
          return (
            <circle
              key={node.id}
              cx={nCx}
              cy={nCy}
              r={nR}
              fill={node.color}
              fillOpacity={INNER_FILL_OPACITY}
              stroke={node.color}
              strokeOpacity={0.85}
              strokeWidth={2}
            >
              <title>{`${node.label}: ${formattedVal}`}</title>
            </circle>
          );
        }

        const nameSize = Math.max(14, Math.min(17, Math.round(nR * 0.22)));
        const valueSize = 14;
        const maxLineChars = Math.max(...node.lines.map((line: string) => line.length));
        const reqHalfWidth = (maxLineChars * nameSize * 0.56) / 2;
        const showName = nR >= 32 && reqHalfWidth <= nR * 0.9;
        const showValue = showName && nR >= 46;
        const lineHeightEm = 1.18;
        const nameHalfHeight = (node.lines.length * nameSize * lineHeightEm) / 2;
        const valueHalfHeight = (valueSize * lineHeightEm) / 2;
        const gap = nameSize * 0.28;
        const nameCenterY = showValue ? nCy - valueHalfHeight - gap / 2 : nCy;
        const valueCenterY = nCy + nameHalfHeight + gap / 2;

        return (
          <g key={node.id}>
            <circle
              cx={nCx}
              cy={nCy}
              r={nR}
              fill={node.color}
              fillOpacity={LEAF_FILL_OPACITY}
              stroke={t.pageBg}
              strokeWidth={2}
            >
              <title>{`${node.label}: ${formattedVal}`}</title>
            </circle>
            {showName && (
              <ChartsText
                text={node.lines.join("\n")}
                x={nCx}
                y={nameCenterY}
                style={{
                  fontSize: nameSize,
                  fontWeight: 600,
                  fill: node.ink,
                  textAnchor: "middle",
                  dominantBaseline: "central",
                }}
              />
            )}
            {showValue && (
              <ChartsText
                text={formattedVal}
                x={nCx}
                y={valueCenterY}
                opacity={0.92}
                style={{
                  fontSize: valueSize,
                  fill: node.ink,
                  textAnchor: "middle",
                  dominantBaseline: "central",
                }}
              />
            )}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - HEADER_HEIGHT;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          height: HEADER_HEIGHT,
          padding: "18px 28px 0 28px",
          boxSizing: "border-box",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 4, lineHeight: 1.3 }}>
          {SUBTITLE}
        </div>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "8px 22px",
            marginTop: 12,
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          {root.children.map((branch) => (
            <div key={branch.id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  backgroundColor: branch.color,
                  opacity: LEAF_FILL_OPACITY,
                  display: "inline-block",
                }}
              />
              <span>{`${branch.label} (${branch.value.toLocaleString()}${unitSuffix})`}</span>
            </div>
          ))}
        </div>
      </div>
      <ChartsContainer
        width={width}
        height={chartHeight}
        series={[]}
        xAxis={[{ position: "none" }]}
        yAxis={[{ position: "none" }]}
        margin={MARGIN}
        skipAnimation
      >
        <CirclePacking />
      </ChartsContainer>
    </div>
  );
}
