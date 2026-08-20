// anyplot.ai
// flamegraph-basic: Flame Graph for Performance Profiling
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-08-20
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

const title = "flamegraph-basic · javascript · muix · anyplot.ai";
const titleFontSize = Math.max(16, Math.round(22 * Math.min(1, 67 / title.length)));

// --- Data: a simulated CPU profile of a web request handler, expressed as a
// call tree (function -> children). Each node's samples equal the sum of its
// children's samples, exactly as a real profiler would report it. ----------
const callTree = {
  name: "main",
  samples: 12000,
  children: [
    {
      name: "parse_request",
      samples: 3000,
      children: [
        { name: "validate_headers", samples: 840 },
        { name: "decode_json_body", samples: 2160 },
      ],
    },
    {
      name: "handle_business_logic",
      samples: 6600,
      children: [
        {
          name: "query_database",
          samples: 4560,
          children: [
            {
              name: "execute_sql",
              samples: 3240,
              children: [
                { name: "parse_sql", samples: 1080 },
                { name: "execute_query", samples: 2160 },
              ],
            },
            { name: "deserialize_rows", samples: 1320 },
          ],
        },
        { name: "compute_response", samples: 2040 },
      ],
    },
    {
      name: "write_response",
      samples: 2400,
      children: [
        { name: "serialize_json", samples: 1560 },
        { name: "flush_socket", samples: 840 },
      ],
    },
  ],
};
const TOTAL_SAMPLES = callTree.samples;

// Flatten the tree into positioned frames: x0/width in sample units (so bar
// width is proportional to samples, per the spec), depth = stack row, branch
// = the depth-1 ancestor this frame belongs to (used for coloring). Siblings
// are laid out contiguously left-to-right with no gaps, standard flame-graph
// (icicle) layout.
function layoutFrames(node, depth, x0, branch, out) {
  out.push({ name: node.name, depth, x0, width: node.samples, samples: node.samples, branch });
  let cursor = x0;
  (node.children ?? []).forEach((child) => {
    layoutFrames(child, depth + 1, cursor, depth === 0 ? child.name : branch, out);
    cursor += child.samples;
  });
  return out;
}
const frames = layoutFrames(callTree, 0, 0, "root", []);
const maxDepth = Math.max(...frames.map((f) => f.depth));

// Imprint palette — first branch encountered is always brand green. The root
// frame uses the theme-adaptive `neutral` anchor (it IS the baseline: 100% of
// samples), so its fill flips with theme like the surrounding chrome.
const BRANCH_COLOR = {
  root: t.ink,
  parse_request: t.palette[0], // #009E73
  handle_business_logic: t.palette[1], // #C475FD
  write_response: t.palette[2], // #4467A3
};
// Fixed (theme-independent) label colors chosen per fill's own luminance —
// the categorical hues don't flip with theme, so their contrasting text
// can't either. `root`'s fill is theme-adaptive, so its label follows suit.
const BRANCH_LABEL_COLOR = {
  root: t.pageBg,
  parse_request: "#FAF8F1",
  handle_business_logic: "#1A1A17",
  write_response: "#FAF8F1",
};

const ROW_H = 0.92; // fraction of each depth row's band actually drawn (rest = gap)
const LABEL_FONT_SIZE = 14;
const CHAR_WIDTH_RATIO = 0.58; // rough average glyph width, in units of font size
const MARGIN = { top: 130, right: 40, bottom: 30, left: 110 };

// Each stack frame as a rect, sized/positioned from the layout above. The
// function name is drawn inside the bar only when it actually fits — no
// rotated or truncated text, per the spec's "wide enough to fit" rule. A
// native <title> gives every frame a real (non-fake) hover tooltip.
function FlameFrames() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g>
      {frames.map((f) => {
        const xLeft = xs(f.x0);
        const xRight = xs(f.x0 + f.width);
        const yTop = ys(f.depth + ROW_H);
        const yBottom = ys(f.depth);
        const w = xRight - xLeft;
        const h = yBottom - yTop;
        const pct = (f.samples / TOTAL_SAMPLES) * 100;
        const fits = w - 14 >= f.name.length * LABEL_FONT_SIZE * CHAR_WIDTH_RATIO;
        return (
          <g key={`${f.branch}-${f.name}`}>
            <rect x={xLeft} y={yTop} width={w} height={h} fill={BRANCH_COLOR[f.branch]} stroke={t.pageBg} strokeWidth={1.5}>
              <title>{`${f.name}: ${f.samples.toLocaleString()} samples (${pct.toFixed(1)}%)`}</title>
            </rect>
            {fits && (
              <text
                x={xLeft + w / 2}
                y={yTop + h / 2}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={LABEL_FONT_SIZE}
                fontWeight={600}
                fill={BRANCH_LABEL_COLOR[f.branch]}
                pointerEvents="none"
              >
                {f.name}
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
}

// Row labels on the left — the chart has no numeric x-axis (bar width is a
// proportion, not a metric to read off a scale; x-position is layout-only,
// not temporal — see spec), so depth is the only axis worth labeling.
function DepthLabels() {
  const ys = useYScale();
  return (
    <g fontSize={13} fill={t.inkSoft} textAnchor="end">
      {Array.from({ length: maxDepth + 1 }, (_, d) => (
        <text key={d} x={MARGIN.left - 14} y={ys(d + ROW_H / 2)} dominantBaseline="central">
          {d === 0 ? "Depth 0 · root" : `Depth ${d}`}
        </text>
      ))}
    </g>
  );
}

// Color key for the three top-level call branches (root's neutral fill is
// self-explanatory from its "main" label and full-width row).
const LEGEND_ITEMS = [
  { label: "parse_request", color: BRANCH_COLOR.parse_request },
  { label: "handle_business_logic", color: BRANCH_COLOR.handle_business_logic },
  { label: "write_response", color: BRANCH_COLOR.write_response },
];

function BranchLegend() {
  const FS = 13;
  const CHAR_W = FS * 0.58;
  const SWATCH = 14;
  const GAP = 30;
  const widths = LEGEND_ITEMS.map((item) => SWATCH + 8 + item.label.length * CHAR_W);
  const totalWidth = widths.reduce((sum, w) => sum + w, 0) + GAP * (LEGEND_ITEMS.length - 1);
  const { width } = window.ANYPLOT_SIZE;
  const y = 104;
  let cursor = width / 2 - totalWidth / 2;
  return (
    <g fontSize={FS} fill={t.inkSoft}>
      {LEGEND_ITEMS.map((item, i) => {
        const x = cursor;
        cursor += widths[i] + GAP;
        return (
          <g key={item.label}>
            <rect x={x} y={y - SWATCH + 2} width={SWATCH} height={SWATCH} rx={2} fill={item.color} />
            <text x={x + SWATCH + 8} y={y}>
              {item.label}
            </text>
          </g>
        );
      })}
    </g>
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const subtitle = `Simulated web-request CPU profile · ${TOTAL_SAMPLES.toLocaleString()} samples across ${frames.length} stack frames`;

  return (
    <ChartContainer
      width={width}
      height={height}
      series={[]}
      margin={MARGIN}
      xAxis={[{ scaleType: "linear", min: 0, max: TOTAL_SAMPLES, disableLine: true, disableTicks: true, valueFormatter: () => "" }]}
      yAxis={[{ scaleType: "linear", min: 0, max: maxDepth + 1, disableLine: true, disableTicks: true, valueFormatter: () => "" }]}
      skipAnimation
    >
      <FlameFrames />
      <DepthLabels />
      <BranchLegend />
      <text x={width / 2} y={48} textAnchor="middle" fontSize={titleFontSize} fontWeight={600} fill={t.ink}>
        {title}
      </text>
      <text x={width / 2} y={76} textAnchor="middle" fontSize={15} fill={t.inkSoft}>
        {subtitle}
      </text>
    </ChartContainer>
  );
}
