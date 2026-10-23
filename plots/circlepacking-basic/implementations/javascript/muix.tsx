// anyplot.ai
// circlepacking-basic: Circle Packing Chart
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-02
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";
import { ChartsText } from "@mui/x-charts/ChartsText";

const t = window.ANYPLOT_TOKENS;

// Columns
const ID = "Node ID";
const PARENT = "Parent ID";
const LABEL = "Asset Class / Holding";
const VALUE = "Market value ($K)";

// Data
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

// Constants
const TITLE = "circlepacking-basic · javascript · muix · anyplot.ai";
const MARGIN = { top: 168, right: 24, bottom: 24, left: 24 };
const LEAF_RADIUS_SCALE = 8;
const SIBLING_PADDING_RATIO = 0.06;
const PARENT_PADDING_RATIO = 0.08;
const PACK_ATTRACTION = 0.02;
const PACK_ITERATIONS = 400;
const SEED_SPREAD = 1.4;
const VALUE_UNIT = VALUE.match(/\(([^)]+)\)/)?.[1] ?? "";

const nodes = data.map((row) => ({
  id: row[ID],
  parent: row[PARENT],
  label: row[LABEL],
  value: row[VALUE] ?? 0,
  children: [],
  depth: 0,
  x: 0,
  y: 0,
  r: 0,
  cx: 0,
  cy: 0,
  color: t.palette[0],
  fill: t.palette[0],
  ink: "#1A1A17",
  lines: [row[LABEL]],
}));

const byId = new Map(nodes.map((n) => [n.id, n]));
let root = nodes[0];
for (const node of nodes) {
  if (node.parent == null) {
    root = node;
  } else {
    byId.get(node.parent).children.push(node);
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
    node.color = byId.get(node.parent).color;
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

for (const branch of root.children) {
  const maxLeafValue = Math.max(...branch.children.map((c) => c.value));
  const hexNum = parseInt(branch.color.slice(1), 16);
  const baseRgb = [(hexNum >> 16) & 255, (hexNum >> 8) & 255, hexNum & 255];

  for (const leaf of branch.children) {
    const tintFactor = maxLeafValue > 0 ? (1 - leaf.value / maxLeafValue) * 0.58 : 0;
    const rgb = baseRgb.map((c) => Math.round(c + (255 - c) * tintFactor));
    leaf.fill = `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
    const lin = rgb.map((v) => {
      const s = v / 255;
      return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
    });
    const lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
    leaf.ink = lum > 0.45 ? "#1A1A17" : "#FAF8F1";

    const words = leaf.label.split(" ");
    if (words.length <= 1 || leaf.label.length <= 10) {
      leaf.lines = [leaf.label];
    } else {
      let best = [leaf.label];
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
      leaf.lines = best;
    }
  }
}

const SUBTITLE = `${root.label} breakdown across ${root.children.length} categories ($${root.value.toLocaleString()}K total · circle area ∝ ${VALUE.toLowerCase()})`;

function CirclePacking() {
  const { left, top, width, height } = useDrawingArea();
  const availableRadius = Math.min(width, height) / 2 - 4;
  const scale = availableRadius / root.r;
  const originX = left + width / 2;
  const originY = top + height / 2;

  const rootCx = originX + root.cx * scale;
  const rootCy = originY + root.cy * scale;
  const rootR = root.r * scale;

  return (
    <g>
      <circle
        cx={rootCx}
        cy={rootCy}
        r={rootR}
        fill="none"
        stroke={t.inkSoft}
        strokeOpacity={0.35}
        strokeWidth={1.5}
      />
      {root.children.map((branch) => {
        const bCx = originX + branch.cx * scale;
        const bCy = originY + branch.cy * scale;
        const bR = branch.r * scale;
        return (
          <g key={branch.id}>
            <circle
              cx={bCx}
              cy={bCy}
              r={bR}
              fill={branch.color}
              fillOpacity={0.14}
              stroke={branch.color}
              strokeOpacity={0.85}
              strokeWidth={2}
            >
              <title>{`${branch.label}: $${branch.value}K`}</title>
            </circle>
            {branch.children.map((leaf) => {
              const lCx = originX + leaf.cx * scale;
              const lCy = originY + leaf.cy * scale;
              const lR = leaf.r * scale;
              const nameSize = Math.max(14, Math.min(17, Math.round(lR * 0.22)));
              const valueSize = 14;
              const maxLineChars = Math.max(...leaf.lines.map((line) => line.length));
              const reqHalfWidth = (maxLineChars * nameSize * 0.56) / 2;
              const showName = lR >= 32 && reqHalfWidth <= lR * 0.9;
              const showValue = showName && lR >= 46;
              const lineHeightEm = 1.18;
              const nameHalfHeight = (leaf.lines.length * nameSize * lineHeightEm) / 2;
              const valueHalfHeight = (valueSize * lineHeightEm) / 2;
              const gap = nameSize * 0.28;
              const nameCenterY = showValue ? lCy - valueHalfHeight - gap / 2 : lCy;
              const valueCenterY = lCy + nameHalfHeight + gap / 2;
              const formattedVal = VALUE_UNIT === "$K" ? `$${leaf.value}K` : `${leaf.value}`;

              return (
                <g key={leaf.id}>
                  <circle
                    cx={lCx}
                    cy={lCy}
                    r={lR}
                    fill={leaf.fill}
                    stroke={t.pageBg}
                    strokeWidth={2}
                  >
                    <title>{`${branch.label} / ${leaf.label}: ${formattedVal}`}</title>
                  </circle>
                  {showName && (
                    <ChartsText
                      text={leaf.lines.join("\n")}
                      x={lCx}
                      y={nameCenterY}
                      style={{
                        fontSize: nameSize,
                        fontWeight: 600,
                        fill: leaf.ink,
                        textAnchor: "middle",
                        dominantBaseline: "central",
                      }}
                    />
                  )}
                  {showValue && (
                    <ChartsText
                      text={formattedVal}
                      x={lCx}
                      y={valueCenterY}
                      opacity={0.88}
                      style={{
                        fontSize: valueSize,
                        fill: leaf.ink,
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
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const legendWidth = width - MARGIN.left - MARGIN.right;
  const itemWidth = legendWidth / root.children.length;

  return (
    <ChartsContainer width={width} height={height} series={[]} margin={MARGIN} skipAnimation>
      <text x={width / 2} y={44} textAnchor="middle" fontSize={22} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
      <text x={width / 2} y={74} textAnchor="middle" fontSize={15} fill={t.inkSoft}>
        {SUBTITLE}
      </text>
      <g>
        {root.children.map((branch, i) => {
          const itemX = MARGIN.left + itemWidth * i;
          return (
            <g key={branch.id}>
              <circle cx={itemX + 10} cy={116} r={7} fill={branch.color} />
              <text
                x={itemX + 24}
                y={116}
                dominantBaseline="middle"
                fontSize={14}
                fill={t.inkSoft}
              >
                {`${branch.label} ($${branch.value}K)`}
              </text>
            </g>
          );
        })}
      </g>
      <CirclePacking />
    </ChartsContainer>
  );
}
