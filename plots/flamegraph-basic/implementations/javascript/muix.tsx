// anyplot.ai
// flamegraph-basic: Flame Graph for Performance Profiling
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 96/100 | Created: 2026-08-20
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "flamegraph-basic · javascript · muix · anyplot.ai";
const DEPTH_LABEL = "Depth";
const ROOT_ROLE_LABEL = "root";
const LEGEND_LOW_PREFIX = "fewer";
const LEGEND_HIGH_PREFIX = "more";

const WARM_STOPS: [number, number, number][] = [t.amber, t.palette[3], t.palette[4]].map((hex) => [
  parseInt(hex.slice(1, 3), 16),
  parseInt(hex.slice(3, 5), 16),
  parseInt(hex.slice(5, 7), 16),
]);
const ROOT_RGB: [number, number, number] = [
  parseInt(t.inkSoft.slice(1, 3), 16),
  parseInt(t.inkSoft.slice(3, 5), 16),
  parseInt(t.inkSoft.slice(5, 7), 16),
];

const ROW_H_SHARE = 0.92;
const LABEL_FONT_SIZE = 14;
const CHAR_WIDTH_RATIO = 0.58;
const MARGIN = { top: 126, right: 40, bottom: 28, left: 118 };

// Columns: set these to your data's column names
const STACK = "Stack"; // role: stack
const FUNCTION = "Function"; // role: function
const SAMPLES = "Samples"; // role: value

// Data: replace this block with your own records
const VERBS = [
  "parse",
  "validate",
  "compute",
  "fetch",
  "serialize",
  "cache",
  "dispatch",
  "format",
  "aggregate",
  "filter",
  "normalize",
  "encode",
  "decode",
  "resolve",
  "persist",
  "merge",
];
const NOUNS = [
  "headers",
  "payload",
  "record",
  "query",
  "response",
  "token",
  "schema",
  "row",
  "buffer",
  "session",
  "event",
  "job",
  "metric",
  "column",
  "batch",
  "socket",
];

let lcgSeed = 20260820;
const usedFnNames = new Set([
  "main",
  "parse_request",
  "authenticate_user",
  "handle_business_logic",
  "write_response",
]);

type ExpandItem = { stack: string; name: string; samples: number; remainingDepth: number };
const expandStack: ExpandItem[] = [
  { stack: "main;write_response", name: "write_response", samples: 2800, remainingDepth: 4 },
  { stack: "main;handle_business_logic", name: "handle_business_logic", samples: 7700, remainingDepth: 5 },
  { stack: "main;authenticate_user", name: "authenticate_user", samples: 1400, remainingDepth: 4 },
  { stack: "main;parse_request", name: "parse_request", samples: 2100, remainingDepth: 4 },
];

const data: Record<string, string | number>[] = [];

while (expandStack.length > 0) {
  const current = expandStack.pop()!;
  if (current.remainingDepth <= 0 || current.samples < 220) {
    data.push({
      [STACK]: current.stack,
      [FUNCTION]: current.name,
      [SAMPLES]: current.samples,
    });
    continue;
  }
  lcgSeed = (lcgSeed * 48271) % 2147483647;
  const childCount = 2 + Math.floor((lcgSeed / 2147483647) * 2);
  const weights: number[] = [];
  let weightSum = 0;
  for (let i = 0; i < childCount; i++) {
    lcgSeed = (lcgSeed * 48271) % 2147483647;
    const w = 0.5 + lcgSeed / 2147483647;
    weights.push(w);
    weightSum += w;
  }
  let remaining = current.samples;
  const childrenToPush: ExpandItem[] = [];
  for (let i = 0; i < childCount; i++) {
    let fnName = "";
    do {
      lcgSeed = (lcgSeed * 48271) % 2147483647;
      const vIdx = Math.floor((lcgSeed / 2147483647) * VERBS.length);
      lcgSeed = (lcgSeed * 48271) % 2147483647;
      const nIdx = Math.floor((lcgSeed / 2147483647) * NOUNS.length);
      fnName = `${VERBS[vIdx]}_${NOUNS[nIdx]}`;
    } while (usedFnNames.has(fnName));
    usedFnNames.add(fnName);

    const childSamples =
      i === childCount - 1 ? remaining : Math.round((weights[i] / weightSum) * current.samples);
    remaining -= childSamples;
    childrenToPush.push({
      stack: `${current.stack};${fnName}`,
      name: fnName,
      samples: childSamples,
      remainingDepth: current.remainingDepth - 1,
    });
  }
  for (let i = childrenToPush.length - 1; i >= 0; i--) {
    expandStack.push(childrenToPush[i]);
  }
}

// Plot: reads only data and the constants above
type FrameNode = {
  pathKey: string;
  name: string;
  depth: number;
  samples: number;
  childKeys: string[];
};

const nodeMap = new Map<string, FrameNode>();
const rootKeys: string[] = [];

for (const row of data) {
  const stackStr = String(row[STACK]);
  const leafFn = String(row[FUNCTION]);
  const samples = Number(row[SAMPLES]);
  const parts = stackStr.split(";");
  if (parts.length > 0 && parts[parts.length - 1] !== leafFn) {
    parts[parts.length - 1] = leafFn;
  }
  let prefix = "";
  for (let d = 0; d < parts.length; d++) {
    const fn = parts[d];
    const nextPrefix = d === 0 ? fn : `${prefix};${fn}`;
    if (d === 0 && !rootKeys.includes(nextPrefix)) {
      rootKeys.push(nextPrefix);
    }
    let node = nodeMap.get(nextPrefix);
    if (!node) {
      node = { pathKey: nextPrefix, name: fn, depth: d, samples: 0, childKeys: [] };
      nodeMap.set(nextPrefix, node);
      if (d > 0) {
        const parentNode = nodeMap.get(prefix)!;
        parentNode.childKeys.push(nextPrefix);
      }
    }
    node.samples += samples;
    prefix = nextPrefix;
  }
}

type PositionedFrame = {
  pathKey: string;
  name: string;
  depth: number;
  x0: number;
  width: number;
  samples: number;
  pct: number;
  fill: string;
  labelFill: string;
};

const rawFrames: { pathKey: string; name: string; depth: number; x0: number; width: number; samples: number }[] = [];
const layoutQueue: { key: string; x0: number }[] = [];
let rootCursor = 0;
const rootEntries: { key: string; x0: number }[] = [];
for (const rKey of rootKeys) {
  rootEntries.push({ key: rKey, x0: rootCursor });
  rootCursor += nodeMap.get(rKey)!.samples;
}
for (let i = rootEntries.length - 1; i >= 0; i--) {
  layoutQueue.push(rootEntries[i]);
}

while (layoutQueue.length > 0) {
  const { key, x0 } = layoutQueue.pop()!;
  const node = nodeMap.get(key)!;
  rawFrames.push({
    pathKey: node.pathKey,
    name: node.name,
    depth: node.depth,
    x0,
    width: node.samples,
    samples: node.samples,
  });
  let cursor = x0;
  const childEntries: { key: string; x0: number }[] = [];
  for (const cKey of node.childKeys) {
    const child = nodeMap.get(cKey)!;
    childEntries.push({ key: cKey, x0: cursor });
    cursor += child.samples;
  }
  for (let i = childEntries.length - 1; i >= 0; i--) {
    layoutQueue.push(childEntries[i]);
  }
}

const totalSamples = rootCursor;
const maxDepth = Math.max(...rawFrames.map((f) => f.depth));
const nonRootPcts = rawFrames.filter((f) => f.depth > 0).map((f) => f.samples / totalSamples);
const minPct = Math.min(...nonRootPcts);
const maxPct = Math.max(...nonRootPcts);

const frames: PositionedFrame[] = rawFrames.map((f) => {
  const isRoot = f.depth === 0;
  const pct = (f.samples / totalSamples) * 100;
  let rgb: [number, number, number] = ROOT_RGB;
  if (!isRoot) {
    const u = (pct / 100 - minPct) / (maxPct - minPct);
    const scaled = u * (WARM_STOPS.length - 1);
    const idx = Math.min(WARM_STOPS.length - 2, Math.floor(scaled));
    const frac = scaled - idx;
    rgb = [
      Math.round(WARM_STOPS[idx][0] + (WARM_STOPS[idx + 1][0] - WARM_STOPS[idx][0]) * frac),
      Math.round(WARM_STOPS[idx][1] + (WARM_STOPS[idx + 1][1] - WARM_STOPS[idx][1]) * frac),
      Math.round(WARM_STOPS[idx][2] + (WARM_STOPS[idx + 1][2] - WARM_STOPS[idx][2]) * frac),
    ];
  }
  const srgb = rgb.map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  const lum = 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2];
  return {
    ...f,
    pct,
    fill: `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`,
    labelFill: lum > 0.45 ? "#1A1A17" : "#FAF8F1",
  };
});

function FlameGraphCanvas() {
  const xs = useXScale();
  const ys = useYScale();
  const { width } = window.ANYPLOT_SIZE;

  const legendFs = 14;
  const legendCharW = legendFs * 0.58;
  const legendY = 104;
  const barW = 220;
  const barH = 14;
  const rootName = rootKeys.join(", ");
  const rootLabel = `${rootName} (${ROOT_ROLE_LABEL} · 100% ${SAMPLES})`;
  const leftLabel = `${LEGEND_LOW_PREFIX} ${SAMPLES} (${(minPct * 100).toFixed(1)}%)`;
  const rightLabel = `${LEGEND_HIGH_PREFIX} ${SAMPLES} (${(maxPct * 100).toFixed(1)}%)`;
  const rootSwatchW = 14;
  const rootBlockW = rootSwatchW + 8 + rootLabel.length * legendCharW;
  const leftLabelW = leftLabel.length * legendCharW;
  const rightLabelW = rightLabel.length * legendCharW;
  const legendPad = 14;
  const sectionGap = 36;
  const barBlockW = leftLabelW + legendPad + barW + legendPad + rightLabelW;
  const totalLegendW = rootBlockW + sectionGap + barBlockW;

  let lx = width / 2 - totalLegendW / 2;
  const rootSwatchX = lx;
  const rootLabelX = rootSwatchX + rootSwatchW + 8;
  lx += rootBlockW + sectionGap;
  const leftLabelX = lx;
  lx += leftLabelW + legendPad;
  const barX = lx;
  lx += barW + legendPad;
  const rightLabelX = lx;

  return (
    <g>
      <defs>
        <linearGradient id="flamegraphHeatGradient" x1="0%" x2="100%" y1="0%" y2="0%">
          <stop offset="0%" stopColor={`rgb(${WARM_STOPS[0].join(",")})`} />
          <stop offset="50%" stopColor={`rgb(${WARM_STOPS[1].join(",")})`} />
          <stop offset="100%" stopColor={`rgb(${WARM_STOPS[2].join(",")})`} />
        </linearGradient>
      </defs>

      {/* Flame frames */}
      {frames.map((f) => {
        const xLeft = xs(f.x0);
        const xRight = xs(f.x0 + f.width);
        const yTop = ys(f.depth + ROW_H_SHARE);
        const yBottom = ys(f.depth);
        const w = xRight - xLeft;
        const h = yBottom - yTop;
        const fits = w - 14 >= f.name.length * LABEL_FONT_SIZE * CHAR_WIDTH_RATIO;
        return (
          <g key={f.pathKey}>
            <rect
              x={xLeft}
              y={yTop}
              width={w}
              height={h}
              fill={f.fill}
              stroke={t.pageBg}
              strokeWidth={1.5}
            >
              <title>{`${f.name}: ${f.samples.toLocaleString()} ${SAMPLES} (${f.pct.toFixed(1)}%)`}</title>
            </rect>
            {fits && (
              <text
                x={xLeft + w / 2}
                y={yTop + h / 2}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={LABEL_FONT_SIZE}
                fontWeight={600}
                fill={f.labelFill}
                pointerEvents="none"
              >
                {f.name}
              </text>
            )}
          </g>
        );
      })}

      {/* Depth row labels */}
      <g fontSize={14} fill={t.inkSoft} textAnchor="end">
        {Array.from({ length: maxDepth + 1 }, (_, d) => (
          <text key={d} x={MARGIN.left - 14} y={ys(d + ROW_H_SHARE / 2)} dominantBaseline="central">
            {d === 0 ? `${DEPTH_LABEL} 0 · ${ROOT_ROLE_LABEL}` : `${DEPTH_LABEL} ${d}`}
          </text>
        ))}
      </g>

      {/* Heat scale legend */}
      <g fontSize={legendFs} fill={t.inkSoft}>
        <rect
          x={rootSwatchX}
          y={legendY - rootSwatchW + 2}
          width={rootSwatchW}
          height={rootSwatchW}
          rx={2}
          fill={`rgb(${ROOT_RGB.join(",")})`}
        />
        <text x={rootLabelX} y={legendY}>
          {rootLabel}
        </text>
        <text x={leftLabelX} y={legendY}>
          {leftLabel}
        </text>
        <rect
          x={barX}
          y={legendY - barH + 2}
          width={barW}
          height={barH}
          rx={2}
          fill="url(#flamegraphHeatGradient)"
        />
        <text x={rightLabelX} y={legendY}>
          {rightLabel}
        </text>
      </g>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const subtitle = `${totalSamples.toLocaleString()} ${SAMPLES} across ${frames.length} stack frames (${data.length} leaf traces)`;

  return (
    <ChartsContainer
      width={width}
      height={height}
      series={[]}
      margin={MARGIN}
      xAxis={[{ scaleType: "linear", min: 0, max: totalSamples, position: "none" }]}
      yAxis={[{ scaleType: "linear", min: 0, max: maxDepth + 1, position: "none" }]}
      skipAnimation
    >
      <FlameGraphCanvas />
      <text x={width / 2} y={44} textAnchor="middle" fontSize={22} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
      <text x={width / 2} y={70} textAnchor="middle" fontSize={15} fill={t.inkSoft}>
        {subtitle}
      </text>
    </ChartsContainer>
  );
}
