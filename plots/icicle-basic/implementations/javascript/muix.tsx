// anyplot.ai
// icicle-basic: Basic Icicle Chart
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const ID_COL = "Node Path";
const NAME_COL = "Node Name";
const PARENT_COL = "Parent Path";
const VALUE_COL = "Size (KB)";

const ROOT_FILL = "#6E6A61";
const FIXED_DARK_TEXT = "#1A1A17";
const FIXED_LIGHT_TEXT = "#FAF8F1";
const TINT_STEP = 0.24;
const ROW_GUTTER = 5;
const COL_GUTTER = 2;
const LABEL_FONT_SIZE = [20, 16, 15, 14];
const SUBLABEL_FONT_SIZE = 14;
const CHAR_WIDTH_RATIO = 0.56;

// Data: repository file-system hierarchy in flat scalar records (sizes in KB)
const DATA: Array<{
  [ID_COL]: string;
  [NAME_COL]: string;
  [PARENT_COL]: string;
  [VALUE_COL]: number;
}> = [
  { [ID_COL]: "repo/", [NAME_COL]: "repo/", [PARENT_COL]: "", [VALUE_COL]: 0 },
  // Top-level directories
  { [ID_COL]: "repo/node_modules/", [NAME_COL]: "node_modules/", [PARENT_COL]: "repo/", [VALUE_COL]: 0 },
  { [ID_COL]: "repo/src/", [NAME_COL]: "src/", [PARENT_COL]: "repo/", [VALUE_COL]: 0 },
  { [ID_COL]: "repo/tests/", [NAME_COL]: "tests/", [PARENT_COL]: "repo/", [VALUE_COL]: 0 },
  { [ID_COL]: "repo/docs/", [NAME_COL]: "docs/", [PARENT_COL]: "repo/", [VALUE_COL]: 0 },
  // Subdirectories under node_modules/
  { [ID_COL]: "repo/node_modules/react/", [NAME_COL]: "react/", [PARENT_COL]: "repo/node_modules/", [VALUE_COL]: 0 },
  { [ID_COL]: "repo/node_modules/webpack/", [NAME_COL]: "webpack/", [PARENT_COL]: "repo/node_modules/", [VALUE_COL]: 0 },
  { [ID_COL]: "repo/node_modules/typescript/", [NAME_COL]: "typescript/", [PARENT_COL]: "repo/node_modules/", [VALUE_COL]: 0 },
  { [ID_COL]: "repo/node_modules/eslint/", [NAME_COL]: "eslint/", [PARENT_COL]: "repo/node_modules/", [VALUE_COL]: 0 },
  // Subdirectories under src/
  { [ID_COL]: "repo/src/components/", [NAME_COL]: "components/", [PARENT_COL]: "repo/src/", [VALUE_COL]: 0 },
  { [ID_COL]: "repo/src/utils/", [NAME_COL]: "utils/", [PARENT_COL]: "repo/src/", [VALUE_COL]: 0 },
  { [ID_COL]: "repo/src/styles/", [NAME_COL]: "styles/", [PARENT_COL]: "repo/src/", [VALUE_COL]: 0 },
  // Subdirectories under tests/
  { [ID_COL]: "repo/tests/unit/", [NAME_COL]: "unit/", [PARENT_COL]: "repo/tests/", [VALUE_COL]: 0 },
  { [ID_COL]: "repo/tests/integration/", [NAME_COL]: "integration/", [PARENT_COL]: "repo/tests/", [VALUE_COL]: 0 },
  // Subdirectories under docs/
  { [ID_COL]: "repo/docs/guides/", [NAME_COL]: "guides/", [PARENT_COL]: "repo/docs/", [VALUE_COL]: 0 },
  { [ID_COL]: "repo/docs/reference/", [NAME_COL]: "reference/", [PARENT_COL]: "repo/docs/", [VALUE_COL]: 0 },
  // Files under react/
  { [ID_COL]: "repo/node_modules/react/index.js", [NAME_COL]: "index.js", [PARENT_COL]: "repo/node_modules/react/", [VALUE_COL]: 180 },
  { [ID_COL]: "repo/node_modules/react/package.json", [NAME_COL]: "package.json", [PARENT_COL]: "repo/node_modules/react/", [VALUE_COL]: 60 },
  { [ID_COL]: "repo/node_modules/react/README.md", [NAME_COL]: "README.md", [PARENT_COL]: "repo/node_modules/react/", [VALUE_COL]: 80 },
  // Files under webpack/
  { [ID_COL]: "repo/node_modules/webpack/webpack.js", [NAME_COL]: "webpack.js", [PARENT_COL]: "repo/node_modules/webpack/", [VALUE_COL]: 140 },
  { [ID_COL]: "repo/node_modules/webpack/loader.js", [NAME_COL]: "loader.js", [PARENT_COL]: "repo/node_modules/webpack/", [VALUE_COL]: 90 },
  { [ID_COL]: "repo/node_modules/webpack/config.js", [NAME_COL]: "config.js", [PARENT_COL]: "repo/node_modules/webpack/", [VALUE_COL]: 50 },
  // Files under typescript/
  { [ID_COL]: "repo/node_modules/typescript/tsc.js", [NAME_COL]: "tsc.js", [PARENT_COL]: "repo/node_modules/typescript/", [VALUE_COL]: 120 },
  { [ID_COL]: "repo/node_modules/typescript/lib.d.ts", [NAME_COL]: "lib.d.ts", [PARENT_COL]: "repo/node_modules/typescript/", [VALUE_COL]: 70 },
  { [ID_COL]: "repo/node_modules/typescript/compiler.js", [NAME_COL]: "compiler.js", [PARENT_COL]: "repo/node_modules/typescript/", [VALUE_COL]: 60 },
  // Files under eslint/
  { [ID_COL]: "repo/node_modules/eslint/index.js", [NAME_COL]: "index.js", [PARENT_COL]: "repo/node_modules/eslint/", [VALUE_COL]: 55 },
  { [ID_COL]: "repo/node_modules/eslint/rules.js", [NAME_COL]: "rules.js", [PARENT_COL]: "repo/node_modules/eslint/", [VALUE_COL]: 45 },
  // Files under components/
  { [ID_COL]: "repo/src/components/Button.tsx", [NAME_COL]: "Button.tsx", [PARENT_COL]: "repo/src/components/", [VALUE_COL]: 90 },
  { [ID_COL]: "repo/src/components/Modal.tsx", [NAME_COL]: "Modal.tsx", [PARENT_COL]: "repo/src/components/", [VALUE_COL]: 110 },
  { [ID_COL]: "repo/src/components/Chart.tsx", [NAME_COL]: "Chart.tsx", [PARENT_COL]: "repo/src/components/", [VALUE_COL]: 80 },
  // Files under utils/
  { [ID_COL]: "repo/src/utils/format.ts", [NAME_COL]: "format.ts", [PARENT_COL]: "repo/src/utils/", [VALUE_COL]: 100 },
  { [ID_COL]: "repo/src/utils/api.ts", [NAME_COL]: "api.ts", [PARENT_COL]: "repo/src/utils/", [VALUE_COL]: 90 },
  // Files under styles/
  { [ID_COL]: "repo/src/styles/theme.css", [NAME_COL]: "theme.css", [PARENT_COL]: "repo/src/styles/", [VALUE_COL]: 75 },
  { [ID_COL]: "repo/src/styles/globals.css", [NAME_COL]: "globals.css", [PARENT_COL]: "repo/src/styles/", [VALUE_COL]: 55 },
  // Files under unit/
  { [ID_COL]: "repo/tests/unit/button.test.ts", [NAME_COL]: "button.test.ts", [PARENT_COL]: "repo/tests/unit/", [VALUE_COL]: 100 },
  { [ID_COL]: "repo/tests/unit/utils.test.ts", [NAME_COL]: "utils.test.ts", [PARENT_COL]: "repo/tests/unit/", [VALUE_COL]: 90 },
  // Files under integration/
  { [ID_COL]: "repo/tests/integration/api.test.ts", [NAME_COL]: "api.test.ts", [PARENT_COL]: "repo/tests/integration/", [VALUE_COL]: 85 },
  { [ID_COL]: "repo/tests/integration/flow.test.ts", [NAME_COL]: "flow.test.ts", [PARENT_COL]: "repo/tests/integration/", [VALUE_COL]: 75 },
  // Files under guides/
  { [ID_COL]: "repo/docs/guides/getting-started.md", [NAME_COL]: "getting-started.md", [PARENT_COL]: "repo/docs/guides/", [VALUE_COL]: 70 },
  { [ID_COL]: "repo/docs/guides/deployment.md", [NAME_COL]: "deployment.md", [PARENT_COL]: "repo/docs/guides/", [VALUE_COL]: 60 },
  // Files under reference/
  { [ID_COL]: "repo/docs/reference/api-reference.md", [NAME_COL]: "api-reference.md", [PARENT_COL]: "repo/docs/reference/", [VALUE_COL]: 70 },
];

interface IcicleNode {
  id: string;
  name: string;
  parentId: string;
  value: number;
  depth: number;
  childrenIds: string[];
  branchColor: string;
  x0Norm: number;
  x1Norm: number;
  fill: string;
  textFill: string;
  parentValue: number;
}

const nodeById = new Map<string, IcicleNode>();
for (let i = 0; i < DATA.length; i += 1) {
  const row = DATA[i];
  nodeById.set(row[ID_COL], {
    id: row[ID_COL],
    name: row[NAME_COL],
    parentId: row[PARENT_COL],
    value: row[VALUE_COL],
    depth: 0,
    childrenIds: [],
    branchColor: ROOT_FILL,
    x0Norm: 0,
    x1Norm: 1,
    fill: ROOT_FILL,
    textFill: FIXED_LIGHT_TEXT,
    parentValue: 0,
  });
}

let rootId = "";
for (let i = 0; i < DATA.length; i += 1) {
  const row = DATA[i];
  const node = nodeById.get(row[ID_COL])!;
  if (!node.parentId) {
    rootId = node.id;
  } else {
    const parent = nodeById.get(node.parentId);
    if (parent) parent.childrenIds.push(node.id);
  }
}

// Topological BFS order from root
const bfsOrder: IcicleNode[] = [];
const queue: string[] = [rootId];
while (queue.length > 0) {
  const curId = queue.shift()!;
  const cur = nodeById.get(curId)!;
  bfsOrder.push(cur);
  for (let c = 0; c < cur.childrenIds.length; c += 1) {
    const child = nodeById.get(cur.childrenIds[c])!;
    child.depth = cur.depth + 1;
    queue.push(child.id);
  }
}

// Bottom-up sum of leaf sizes
for (let i = bfsOrder.length - 1; i >= 0; i -= 1) {
  const node = bfsOrder[i];
  if (node.childrenIds.length > 0) {
    let sum = 0;
    for (let c = 0; c < node.childrenIds.length; c += 1) {
      sum += nodeById.get(node.childrenIds[c])!.value;
    }
    node.value = sum;
  }
}

// Top-down branch color assignment and normalized [0, 1] partition
const rootNode = nodeById.get(rootId)!;
const topDirs = rootNode.childrenIds.map((id, idx) => {
  const dir = nodeById.get(id)!;
  dir.branchColor = t.palette[idx];
  return dir;
});

for (let i = 0; i < bfsOrder.length; i += 1) {
  const node = bfsOrder[i];
  if (node.depth >= 2) {
    const parent = nodeById.get(node.parentId)!;
    node.branchColor = parent.branchColor;
  }
  if (node.parentId) {
    node.parentValue = nodeById.get(node.parentId)!.value;
  } else {
    node.parentValue = node.value;
  }

  let cx = node.x0Norm;
  const span = node.x1Norm - node.x0Norm;
  for (let c = 0; c < node.childrenIds.length; c += 1) {
    const child = nodeById.get(node.childrenIds[c])!;
    const w = node.value > 0 ? (child.value / node.value) * span : 0;
    child.x0Norm = cx;
    child.x1Norm = cx + w;
    cx += w;
  }

  // Compute tinted RGB fill and relative luminance contrast text
  const hex = node.depth === 0 ? ROOT_FILL : node.branchColor;
  const hexInt = parseInt(hex.slice(1), 16);
  const baseR = (hexInt >> 16) & 255;
  const baseG = (hexInt >> 8) & 255;
  const baseB = hexInt & 255;
  const tintFactor = node.depth === 0 ? 0 : (node.depth - 1) * TINT_STEP;
  const r = Math.round(baseR + (248 - baseR) * tintFactor);
  const g = Math.round(baseG + (246 - baseG) * tintFactor);
  const b = Math.round(baseB + (238 - baseB) * tintFactor);
  node.fill = `rgb(${r}, ${g}, ${b})`;

  const sR =
    r / 255 <= 0.03928
      ? r / 255 / 12.92
      : Math.pow((r / 255 + 0.055) / 1.055, 2.4);
  const sG =
    g / 255 <= 0.03928
      ? g / 255 / 12.92
      : Math.pow((g / 255 + 0.055) / 1.055, 2.4);
  const sB =
    b / 255 <= 0.03928
      ? b / 255 / 12.92
      : Math.pow((b / 255 + 0.055) / 1.055, 2.4);
  const lum = 0.2126 * sR + 0.7152 * sG + 0.0722 * sB;
  node.textFill = lum > 0.32 ? FIXED_DARK_TEXT : FIXED_LIGHT_TEXT;
}

const maxDepth = Math.max(...bfsOrder.map((n) => n.depth));
const DEPTH_COUNT = maxDepth + 1;
const leafCount = bfsOrder.filter((n) => n.childrenIds.length === 0).length;

function IcicleLayer() {
  const { left, top, width, height } = useDrawingArea();
  const rowH = height / DEPTH_COUNT;

  return (
    <g>
      {bfsOrder.map((node) => {
        const x = left + node.x0Norm * width + COL_GUTTER / 2;
        const w = Math.max(0, (node.x1Norm - node.x0Norm) * width - COL_GUTTER);
        const y = top + node.depth * rowH + ROW_GUTTER / 2;
        const h = rowH - ROW_GUTTER;
        const fontSize =
          LABEL_FONT_SIZE[
            Math.min(node.depth, LABEL_FONT_SIZE.length - 1)
          ];

        const labelText =
          node.depth === 0
            ? `${node.name} · ${node.value.toLocaleString()} KB total`
            : node.name;
        const subText =
          node.depth === 0 ? "" : `${node.value.toLocaleString()} KB`;
        const pct =
          node.parentValue > 0
            ? ((node.value / node.parentValue) * 100).toFixed(0)
            : "100";

        const showLabel =
          w - 12 >= labelText.length * fontSize * CHAR_WIDTH_RATIO &&
          h >= fontSize + 6;
        const showSub =
          showLabel &&
          subText.length > 0 &&
          h >= fontSize + SUBLABEL_FONT_SIZE + 12 &&
          w - 12 >= subText.length * SUBLABEL_FONT_SIZE * CHAR_WIDTH_RATIO;

        return (
          <g key={node.id}>
            <rect
              x={x}
              y={y}
              width={w}
              height={h}
              fill={node.fill}
              stroke={t.pageBg}
              strokeWidth={1.5}
              rx={2}
            >
              <title>
                {node.id}: {node.value.toLocaleString()} KB ({pct}% of parent)
              </title>
            </rect>
            {showLabel && (
              <text
                x={x + 8}
                y={y + fontSize + 5}
                fontSize={fontSize}
                fontWeight={showSub || node.depth <= 1 ? 600 : 500}
                fill={node.textFill}
                pointerEvents="none"
              >
                {labelText}
              </text>
            )}
            {showSub && (
              <text
                x={x + 8}
                y={y + fontSize + SUBLABEL_FONT_SIZE + 9}
                fontSize={SUBLABEL_FONT_SIZE}
                fontFamily={t.mono}
                fill={node.textFill}
                opacity={0.88}
                pointerEvents="none"
              >
                {subText}
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const headerHeight = 84;
  const chartHeight = height - headerHeight;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        color: t.ink,
        fontFamily: t.sans,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          height: headerHeight,
          padding: "14px 28px 4px 28px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxSizing: "border-box",
        }}
      >
        <div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: t.ink,
              lineHeight: 1.2,
            }}
          >
            icicle-basic · javascript · muix · anyplot.ai
          </div>
          <div
            style={{
              fontSize: 14,
              color: t.inkSoft,
              marginTop: 4,
              fontFamily: t.mono,
            }}
          >
            Repository file sizes across {DEPTH_COUNT} hierarchy levels (
            {leafCount} files, {rootNode.value.toLocaleString()} KB total) ·
            width ∝ {VALUE_COL}
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            fontSize: 14,
            color: t.ink,
          }}
        >
          {topDirs.map((dir) => (
            <div
              key={dir.id}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 3,
                  background: dir.branchColor,
                  display: "inline-block",
                }}
              />
              <span>
                <strong style={{ fontWeight: 600 }}>{dir.name}</strong>{" "}
                <span style={{ color: t.inkSoft, fontFamily: t.mono }}>
                  ({dir.value.toLocaleString()} KB)
                </span>
              </span>
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
        margin={{ top: 8, right: 24, bottom: 20, left: 24 }}
        skipAnimation
      >
        <IcicleLayer />
      </ChartsContainer>
    </div>
  );
}
