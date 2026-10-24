// anyplot.ai
// flamegraph-basic: Flame Graph for Performance Profiling
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 82/100 | Updated: 2026-10-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "flamegraph-basic · javascript · muix · anyplot.ai";
const DEPTH_LABEL = "Depth";
const ROOT_ROLE_LABEL = "root";
const LEGEND_LOW_PREFIX = "fewer";
const LEGEND_HIGH_PREFIX = "more";

type RGB = [number, number, number];
const hexToRgb = (hex: string): RGB => [
  parseInt(hex.slice(1, 3), 16),
  parseInt(hex.slice(3, 5), 16),
  parseInt(hex.slice(5, 7), 16),
];
// Warm ramp: amber → ochre → matte red. The root holds every sample, so it takes the hot end.
const WARM_STOPS: RGB[] = [t.amber, t.palette[3], t.palette[4]].map(hexToRgb);
const ROOT_RGB: RGB = WARM_STOPS[WARM_STOPS.length - 1];
const LABEL_INKS = ["#1A1A17", "#FAF8F1"];

const ROW_H_SHARE = 0.92;
const LABEL_FONT_SIZE = 14;
const CHAR_WIDTH_RATIO = 0.58;
const MARGIN = { top: 150, right: 40, bottom: 28, left: 118 };

// Columns: set these to your data's column names
const STACK = "Stack"; // role: stack
const FUNCTION = "Function"; // role: function
const SAMPLES = "Samples"; // role: value

// Data: replace this block with your own records, e.g. folded stacks from a CPU profiler
const foldedStacks: [string, number][] = [
  ["main;parse_request;read_body;socket_recv", 260],
  ["main;parse_request;read_body;buffer_append", 120],
  ["main;parse_request;read_body;inflate_gzip;inflate_block", 180],
  ["main;parse_request;read_body;inflate_gzip;crc32_update", 60],
  ["main;parse_request;json_decode;scan_tokens;utf8_validate", 140],
  ["main;parse_request;json_decode;scan_tokens;next_token", 220],
  ["main;parse_request;json_decode;build_object;alloc_dict", 110],
  ["main;parse_request;json_decode;build_object;intern_string", 90],
  ["main;parse_request;parse_headers;split_lines", 70],
  ["main;parse_request;parse_headers;normalize_header_name", 50],
  ["main;parse_request;parse_query_string;url_decode", 60],
  ["main;parse_request;parse_query_string;split_params", 40],
  ["main;authenticate_user;verify_jwt;base64_decode", 90],
  ["main;authenticate_user;verify_jwt;rsa_verify;bignum_modexp;mont_mul", 280],
  ["main;authenticate_user;verify_jwt;rsa_verify;bignum_modexp;mont_reduce", 60],
  ["main;authenticate_user;verify_jwt;rsa_verify;sha256_digest", 120],
  ["main;authenticate_user;verify_jwt;check_claims", 40],
  ["main;authenticate_user;load_session;redis_get;socket_send", 60],
  ["main;authenticate_user;load_session;redis_get;socket_recv", 140],
  ["main;authenticate_user;load_session;deserialize_session", 80],
  ["main;authenticate_user;check_permissions;load_role_grants", 70],
  ["main;authenticate_user;check_permissions;match_policy", 50],
  ["main;handle_business_logic;fetch_orders;db_query;pg_send_query", 180],
  ["main;handle_business_logic;fetch_orders;db_query;pg_wait_result;poll_socket;epoll_wait", 820],
  ["main;handle_business_logic;fetch_orders;db_query;pg_wait_result;poll_socket;sys_futex", 80],
  ["main;handle_business_logic;fetch_orders;db_query;pg_wait_result;read_packet", 260],
  ["main;handle_business_logic;fetch_orders;db_query;decode_rows;parse_numeric", 310],
  ["main;handle_business_logic;fetch_orders;db_query;decode_rows;parse_timestamp", 240],
  ["main;handle_business_logic;fetch_orders;db_query;decode_rows;alloc_row", 150],
  ["main;handle_business_logic;fetch_orders;orm_hydrate;map_columns", 260],
  ["main;handle_business_logic;fetch_orders;orm_hydrate;build_relations;lazy_load_customer", 220],
  ["main;handle_business_logic;fetch_orders;orm_hydrate;build_relations;lazy_load_items", 380],
  ["main;handle_business_logic;compute_totals;apply_discounts;match_promo_rules", 420],
  ["main;handle_business_logic;compute_totals;apply_discounts;round_currency", 90],
  ["main;handle_business_logic;compute_totals;calculate_tax;lookup_tax_rate;cache_get", 150],
  ["main;handle_business_logic;compute_totals;calculate_tax;lookup_tax_rate;db_query_tax", 210],
  ["main;handle_business_logic;compute_totals;calculate_tax;multiply_decimal", 130],
  ["main;handle_business_logic;compute_totals;sum_line_items", 260],
  ["main;handle_business_logic;enrich_recommendations;load_user_history", 340],
  ["main;handle_business_logic;enrich_recommendations;score_products;dot_product", 760],
  ["main;handle_business_logic;enrich_recommendations;score_products;sort_candidates", 280],
  ["main;handle_business_logic;enrich_recommendations;filter_in_stock", 160],
  ["main;handle_business_logic;validate_order;check_inventory", 230],
  ["main;handle_business_logic;validate_order;validate_address;regex_match", 170],
  ["main;handle_business_logic;validate_order;validate_address;postal_lookup", 110],
  ["main;write_response;render_template;compile_template", 120],
  ["main;write_response;render_template;render_nodes;escape_html", 320],
  ["main;write_response;render_template;render_nodes;format_currency", 140],
  ["main;write_response;render_template;render_nodes;render_partial;concat_strings", 210],
  ["main;write_response;render_template;render_nodes;render_partial;escape_html", 90],
  ["main;write_response;json_encode;serialize_dict", 380],
  ["main;write_response;json_encode;encode_string", 240],
  ["main;write_response;json_encode;float_to_string", 160],
  ["main;write_response;compress_gzip;deflate_block", 460],
  ["main;write_response;compress_gzip;crc32_update", 70],
  ["main;write_response;socket_write;tcp_send", 180],
  ["main;write_response;socket_write;flush_buffer", 60],
  ["main;gc_collect;mark_objects", 220],
  ["main;gc_collect;sweep_heap", 130],
];
const data: Record<string, string | number>[] = foldedStacks.map(([stack, samples]) => ({
  [STACK]: stack,
  [FUNCTION]: stack.split(";").pop()!,
  [SAMPLES]: samples,
}));

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

const relLuminance = (rgb: RGB) => {
  const [r, g, b] = rgb.map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contrast = (a: RGB, b: RGB) => {
  const [hi, lo] = [relLuminance(a), relLuminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

const frames: PositionedFrame[] = rawFrames.map((f) => {
  const isRoot = f.depth === 0;
  const pct = (f.samples / totalSamples) * 100;
  let rgb: RGB = ROOT_RGB;
  if (!isRoot) {
    const u = (pct / 100 - minPct) / (maxPct - minPct);
    const scaled = u * (WARM_STOPS.length - 1);
    const idx = Math.min(WARM_STOPS.length - 2, Math.floor(scaled));
    const frac = scaled - idx;
    rgb = WARM_STOPS[idx].map((c, k) => Math.round(c + (WARM_STOPS[idx + 1][k] - c) * frac)) as RGB;
  }
  // Pick whichever label ink reads better against this fill.
  const labelFill = LABEL_INKS.reduce((best, ink) =>
    contrast(hexToRgb(ink), rgb) > contrast(hexToRgb(best), rgb) ? ink : best,
  );
  return {
    ...f,
    pct,
    fill: `rgb(${rgb.join(",")})`,
    labelFill,
  };
});

function FlameGraphCanvas() {
  const xs = useXScale();
  const ys = useYScale();
  const { width } = window.ANYPLOT_SIZE;

  // Legend: gradient bar with its end labels anchored beneath it, root swatch to the right.
  const legendFs = 14;
  const barW = 360;
  const barH = 14;
  const barY = 92;
  const barX = width / 2 - barW - 40;
  const endLabelY = barY + barH + 18;
  const rootSwatchX = width / 2 + 40;
  const rootName = rootKeys.join(", ");
  const rootLabel = `${rootName} (${ROOT_ROLE_LABEL} · 100% ${SAMPLES})`;
  const leftLabel = `${LEGEND_LOW_PREFIX} ${SAMPLES} (${(minPct * 100).toFixed(1)}%)`;
  const rightLabel = `${LEGEND_HIGH_PREFIX} ${SAMPLES} (${(maxPct * 100).toFixed(1)}%)`;

  return (
    <g>
      <defs>
        <linearGradient id="flamegraphHeatGradient" x1="0%" x2="100%" y1="0%" y2="0%">
          {WARM_STOPS.map((rgb, i) => (
            <stop key={i} offset={`${(i / (WARM_STOPS.length - 1)) * 100}%`} stopColor={`rgb(${rgb.join(",")})`} />
          ))}
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
        <rect x={barX} y={barY} width={barW} height={barH} rx={2} fill="url(#flamegraphHeatGradient)" />
        <text x={barX} y={endLabelY} textAnchor="start">
          {leftLabel}
        </text>
        <text x={barX + barW} y={endLabelY} textAnchor="end">
          {rightLabel}
        </text>
        <rect x={rootSwatchX} y={barY} width={barH} height={barH} rx={2} fill={`rgb(${ROOT_RGB.join(",")})`} />
        <text x={rootSwatchX + barH + 8} y={barY + barH / 2} dominantBaseline="central">
          {rootLabel}
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
