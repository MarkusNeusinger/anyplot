// anyplot.ai
// icicle-basic: Basic Icicle Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = '"Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, sans-serif';
const MONO = '"JetBrains Mono", "SFMono-Regular", Menlo, monospace';
const ROOT_FILL = "#6E6A61";
const FIXED_DARK_TEXT = "#1A1A17";
const FIXED_LIGHT_TEXT = "#FAF8F1";
const TINT_STEP = 0.24;
const ROW_GUTTER = 5;
const COL_GUTTER = 2;
const LABEL_FONT_SIZE = [20, 16, 15, 14];
const SUBLABEL_FONT_SIZE = 14;
const CHAR_WIDTH_RATIO = 0.56;

// Columns: set these to your data's column names
const ID = "Node path"; // role: id
const NAME = "Node name"; // role: name
const PARENT = "Parent path"; // role: parent
const VALUE = "Size (KB)"; // role: value

// Data: replace this block with your own records
const data: Array<{
  [ID]: string;
  [NAME]: string;
  [PARENT]: string;
  [VALUE]: number;
}> = [
  { [ID]: "repo/", [NAME]: "repo/", [PARENT]: "", [VALUE]: 0 },
  // Top-level directories
  { [ID]: "repo/node_modules/", [NAME]: "node_modules/", [PARENT]: "repo/", [VALUE]: 0 },
  { [ID]: "repo/src/", [NAME]: "src/", [PARENT]: "repo/", [VALUE]: 0 },
  { [ID]: "repo/tests/", [NAME]: "tests/", [PARENT]: "repo/", [VALUE]: 0 },
  { [ID]: "repo/docs/", [NAME]: "docs/", [PARENT]: "repo/", [VALUE]: 0 },
  // Subdirectories under node_modules/
  { [ID]: "repo/node_modules/react/", [NAME]: "react/", [PARENT]: "repo/node_modules/", [VALUE]: 0 },
  { [ID]: "repo/node_modules/webpack/", [NAME]: "webpack/", [PARENT]: "repo/node_modules/", [VALUE]: 0 },
  { [ID]: "repo/node_modules/typescript/", [NAME]: "typescript/", [PARENT]: "repo/node_modules/", [VALUE]: 0 },
  { [ID]: "repo/node_modules/eslint/", [NAME]: "eslint/", [PARENT]: "repo/node_modules/", [VALUE]: 0 },
  // Subdirectories under src/
  { [ID]: "repo/src/components/", [NAME]: "components/", [PARENT]: "repo/src/", [VALUE]: 0 },
  { [ID]: "repo/src/utils/", [NAME]: "utils/", [PARENT]: "repo/src/", [VALUE]: 0 },
  { [ID]: "repo/src/styles/", [NAME]: "styles/", [PARENT]: "repo/src/", [VALUE]: 0 },
  // Subdirectories under tests/
  { [ID]: "repo/tests/unit/", [NAME]: "unit/", [PARENT]: "repo/tests/", [VALUE]: 0 },
  { [ID]: "repo/tests/integration/", [NAME]: "integration/", [PARENT]: "repo/tests/", [VALUE]: 0 },
  // Subdirectories under docs/
  { [ID]: "repo/docs/guides/", [NAME]: "guides/", [PARENT]: "repo/docs/", [VALUE]: 0 },
  { [ID]: "repo/docs/reference/", [NAME]: "reference/", [PARENT]: "repo/docs/", [VALUE]: 0 },
  // Files under react/
  { [ID]: "repo/node_modules/react/index.js", [NAME]: "index.js", [PARENT]: "repo/node_modules/react/", [VALUE]: 180 },
  { [ID]: "repo/node_modules/react/package.json", [NAME]: "package.json", [PARENT]: "repo/node_modules/react/", [VALUE]: 60 },
  { [ID]: "repo/node_modules/react/README.md", [NAME]: "README.md", [PARENT]: "repo/node_modules/react/", [VALUE]: 80 },
  // Files under webpack/
  { [ID]: "repo/node_modules/webpack/webpack.js", [NAME]: "webpack.js", [PARENT]: "repo/node_modules/webpack/", [VALUE]: 140 },
  { [ID]: "repo/node_modules/webpack/loader.js", [NAME]: "loader.js", [PARENT]: "repo/node_modules/webpack/", [VALUE]: 90 },
  { [ID]: "repo/node_modules/webpack/config.js", [NAME]: "config.js", [PARENT]: "repo/node_modules/webpack/", [VALUE]: 50 },
  // Files under typescript/
  { [ID]: "repo/node_modules/typescript/tsc.js", [NAME]: "tsc.js", [PARENT]: "repo/node_modules/typescript/", [VALUE]: 120 },
  { [ID]: "repo/node_modules/typescript/lib.d.ts", [NAME]: "lib.d.ts", [PARENT]: "repo/node_modules/typescript/", [VALUE]: 70 },
  { [ID]: "repo/node_modules/typescript/compiler.js", [NAME]: "compiler.js", [PARENT]: "repo/node_modules/typescript/", [VALUE]: 60 },
  // Files under eslint/
  { [ID]: "repo/node_modules/eslint/index.js", [NAME]: "index.js", [PARENT]: "repo/node_modules/eslint/", [VALUE]: 55 },
  { [ID]: "repo/node_modules/eslint/rules.js", [NAME]: "rules.js", [PARENT]: "repo/node_modules/eslint/", [VALUE]: 45 },
  // Files under components/
  { [ID]: "repo/src/components/Button.tsx", [NAME]: "Button.tsx", [PARENT]: "repo/src/components/", [VALUE]: 90 },
  { [ID]: "repo/src/components/Modal.tsx", [NAME]: "Modal.tsx", [PARENT]: "repo/src/components/", [VALUE]: 110 },
  { [ID]: "repo/src/components/Chart.tsx", [NAME]: "Chart.tsx", [PARENT]: "repo/src/components/", [VALUE]: 80 },
  // Files under utils/
  { [ID]: "repo/src/utils/format.ts", [NAME]: "format.ts", [PARENT]: "repo/src/utils/", [VALUE]: 100 },
  { [ID]: "repo/src/utils/api.ts", [NAME]: "api.ts", [PARENT]: "repo/src/utils/", [VALUE]: 90 },
  // Files under styles/
  { [ID]: "repo/src/styles/theme.css", [NAME]: "theme.css", [PARENT]: "repo/src/styles/", [VALUE]: 75 },
  { [ID]: "repo/src/styles/globals.css", [NAME]: "globals.css", [PARENT]: "repo/src/styles/", [VALUE]: 55 },
  // Files under unit/
  { [ID]: "repo/tests/unit/button.test.ts", [NAME]: "button.test.ts", [PARENT]: "repo/tests/unit/", [VALUE]: 100 },
  { [ID]: "repo/tests/unit/utils.test.ts", [NAME]: "utils.test.ts", [PARENT]: "repo/tests/unit/", [VALUE]: 90 },
  // Files under integration/
  { [ID]: "repo/tests/integration/api.test.ts", [NAME]: "api.test.ts", [PARENT]: "repo/tests/integration/", [VALUE]: 85 },
  { [ID]: "repo/tests/integration/flow.test.ts", [NAME]: "flow.test.ts", [PARENT]: "repo/tests/integration/", [VALUE]: 75 },
  // Files under guides/
  { [ID]: "repo/docs/guides/getting-started.md", [NAME]: "getting-started.md", [PARENT]: "repo/docs/guides/", [VALUE]: 70 },
  { [ID]: "repo/docs/guides/deployment.md", [NAME]: "deployment.md", [PARENT]: "repo/docs/guides/", [VALUE]: 60 },
  // Files under reference/
  { [ID]: "repo/docs/reference/api-reference.md", [NAME]: "api-reference.md", [PARENT]: "repo/docs/reference/", [VALUE]: 70 },
];

// Plot: reads only data and the constants above
const unitMatch = VALUE.match(/\(([^)]+)\)/);
const valueUnit = unitMatch ? unitMatch[1] : "";
const unitSuffix = valueUnit ? ` ${valueUnit}` : "";

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
for (let i = 0; i < data.length; i += 1) {
  const row = data[i];
  nodeById.set(row[ID], {
    id: row[ID],
    name: row[NAME],
    parentId: row[PARENT],
    value: row[VALUE],
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
for (let i = 0; i < data.length; i += 1) {
  const row = data[i];
  const node = nodeById.get(row[ID])!;
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
  node.textFill = lum > 0.18 ? FIXED_DARK_TEXT : FIXED_LIGHT_TEXT;
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
            ? `${node.name} · ${node.value.toLocaleString()}${unitSuffix} total`
            : node.name;
        const subText =
          node.depth === 0 ? "" : `${node.value.toLocaleString()}${unitSuffix}`;
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
                {node.id}: {node.value.toLocaleString()}
                {unitSuffix} ({pct}% of parent)
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
                fontFamily={MONO}
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
        fontFamily: FONT,
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
              fontFamily: MONO,
            }}
          >
            {DEPTH_COUNT} levels · {leafCount} leaves ·{" "}
            {rootNode.value.toLocaleString()}
            {unitSuffix} total · width ∝ {VALUE}
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
                <span style={{ color: t.inkSoft, fontFamily: MONO }}>
                  ({dir.value.toLocaleString()}
                  {unitSuffix})
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
