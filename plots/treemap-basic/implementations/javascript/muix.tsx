// anyplot.ai
// treemap-basic: Basic Treemap
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-08-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "treemap-basic · javascript · muix · anyplot.ai";
const TITLE_H = 80;
const MARGIN = { top: 8, right: 32, bottom: 24, left: 32 };
const GUTTER = 3; // px between main categories
const HEADER_H = 30; // px band that names a main category above its tiles
const MIN_NESTED_H = 40; // px a category needs below its header to show its subcategories
const TILE_TINT = 0.3; // share mixed toward white for the subcategory level
const LABEL_FONT = 15;
const CHAR_W = 0.56; // average glyph width as a share of the font size

// Columns: set these to your data's column names
const CATEGORY = "Department"; // role: category
const SUBCATEGORY = "Cost center"; // role: subcategory
const VALUE = "Budget (USD thousand)"; // role: value

// Data: replace this block with your own records, one object per row
// Company expense breakdown: six departments, 20 cost centers.
const data = [
  { [CATEGORY]: "Engineering", [SUBCATEGORY]: "Platform Infra", [VALUE]: 820 },
  { [CATEGORY]: "Engineering", [SUBCATEGORY]: "Mobile Apps", [VALUE]: 540 },
  { [CATEGORY]: "Engineering", [SUBCATEGORY]: "DevOps", [VALUE]: 310 },
  { [CATEGORY]: "Engineering", [SUBCATEGORY]: "QA & Testing", [VALUE]: 210 },
  { [CATEGORY]: "Sales", [SUBCATEGORY]: "Enterprise", [VALUE]: 610 },
  { [CATEGORY]: "Sales", [SUBCATEGORY]: "SMB", [VALUE]: 380 },
  { [CATEGORY]: "Sales", [SUBCATEGORY]: "Partnerships", [VALUE]: 190 },
  { [CATEGORY]: "Marketing", [SUBCATEGORY]: "Digital Ads", [VALUE]: 430 },
  { [CATEGORY]: "Marketing", [SUBCATEGORY]: "Content", [VALUE]: 260 },
  { [CATEGORY]: "Marketing", [SUBCATEGORY]: "Events", [VALUE]: 150 },
  { [CATEGORY]: "Marketing", [SUBCATEGORY]: "Brand", [VALUE]: 120 },
  { [CATEGORY]: "R&D", [SUBCATEGORY]: "Applied Research", [VALUE]: 480 },
  { [CATEGORY]: "R&D", [SUBCATEGORY]: "Prototyping", [VALUE]: 260 },
  { [CATEGORY]: "R&D", [SUBCATEGORY]: "Patents & Compliance", [VALUE]: 140 },
  { [CATEGORY]: "Operations", [SUBCATEGORY]: "Facilities", [VALUE]: 340 },
  { [CATEGORY]: "Operations", [SUBCATEGORY]: "IT Support", [VALUE]: 220 },
  { [CATEGORY]: "Operations", [SUBCATEGORY]: "Logistics", [VALUE]: 180 },
  { [CATEGORY]: "Customer Success", [SUBCATEGORY]: "Support", [VALUE]: 300 },
  { [CATEGORY]: "Customer Success", [SUBCATEGORY]: "Onboarding", [VALUE]: 180 },
  { [CATEGORY]: "Customer Success", [SUBCATEGORY]: "Training", [VALUE]: 110 },
];

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[VALUE] != null && d[VALUE] > 0);
const categories = [...new Set(rows.map((d) => d[CATEGORY]))];
const categoryTotals = categories.map((c) => ({
  name: c,
  value: rows.filter((d) => d[CATEGORY] === c).reduce((sum, d) => sum + d[VALUE], 0),
}));
const grandTotal = categoryTotals.reduce((sum, c) => sum + c.value, 0);

// Colors: one Imprint hue per main category in order of appearance; the
// subcategory tiles take a lighter shade of it, so shading tells the levels
// apart. Text ink follows each fill's luminance, not the theme.
const shades = new Map(
  categories.map((c, i) => {
    const base = [16, 8, 0].map((s) => (parseInt(t.palette[i].slice(1), 16) >> s) & 255);
    const tile = base.map((v) => Math.round(v + (255 - v) * TILE_TINT));
    const [headInk, tileInk] = [base, tile].map((rgb) => {
      const [r, g, b] = rgb.map((v) => v / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
      return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.2 ? "#1A1A17" : "#FAF8F1";
    });
    return [c, { head: t.palette[i], tile: `rgb(${tile.join(",")})`, headInk, tileInk }];
  }),
);

// Squarified layout (Bruls, Huizing & van Wijk) in px of the drawing area, one
// task per container: the main categories over the whole area first, then the
// subcategories of each category inside its rectangle below the header band.
const PLOT_W = window.ANYPLOT_SIZE.width - MARGIN.left - MARGIN.right;
const PLOT_H = window.ANYPLOT_SIZE.height - TITLE_H - MARGIN.top - MARGIN.bottom;
const tiles = [];
const tasks = [{ level: 0, category: null, items: categoryTotals, rect: { x: 0, y: 0, w: PLOT_W, h: PLOT_H } }];
while (tasks.length > 0) {
  const { level, category, items, rect } = tasks.shift();
  const total = items.reduce((sum, d) => sum + d.value, 0);
  const rest = items
    .map((d) => ({ ...d, area: (d.value / total) * rect.w * rect.h }))
    .sort((a, b) => b.area - a.area);
  let free = { ...rect };
  let row = [];
  while (rest.length > 0 || row.length > 0) {
    // Grow the current strip while that keeps its worst aspect ratio from rising
    const side = Math.min(free.w, free.h);
    let grow = rest.length > 0 && row.length === 0;
    if (rest.length > 0 && row.length > 0) {
      const [current, next] = [row, [...row, rest[0]]].map((r) => {
        const s = r.reduce((sum, d) => sum + d.area, 0);
        const areas = r.map((d) => d.area);
        return Math.max((side * side * Math.max(...areas)) / (s * s), (s * s) / (side * side * Math.min(...areas)));
      });
      grow = next <= current;
    }
    if (grow) {
      row.push(rest.shift());
      continue;
    }
    // Lay the strip along the shorter side of the free space
    const stripArea = row.reduce((sum, d) => sum + d.area, 0);
    const vertical = free.w >= free.h;
    const thickness = stripArea / (vertical ? free.h : free.w);
    let offset = vertical ? free.y : free.x;
    row.forEach((d) => {
      const span = d.area / thickness;
      const box = vertical
        ? { x: free.x, y: offset, w: thickness, h: span }
        : { x: offset, y: free.y, w: span, h: thickness };
      offset += span;
      if (level === 0) {
        const outer = { x: box.x + GUTTER, y: box.y + GUTTER, w: Math.max(0, box.w - 2 * GUTTER), h: Math.max(0, box.h - 2 * GUTTER) };
        const nested = outer.h >= HEADER_H + MIN_NESTED_H;
        tiles.push({ level, category: d.name, name: d.name, value: d.value, ...outer, nested });
        if (nested) {
          tasks.push({
            level: 1,
            category: d.name,
            items: rows.filter((r) => r[CATEGORY] === d.name).map((r) => ({ name: r[SUBCATEGORY], value: r[VALUE] })),
            rect: { x: outer.x, y: outer.y + HEADER_H, w: outer.w, h: outer.h - HEADER_H },
          });
        }
      } else {
        tiles.push({ level, category, name: d.name, value: d.value, ...box });
      }
    });
    free = vertical
      ? { x: free.x + thickness, y: free.y, w: free.w - thickness, h: free.h }
      : { x: free.x, y: free.y + thickness, w: free.w, h: free.h - thickness };
    row = [];
  }
}

const fmt = new Intl.NumberFormat("en-US");
const SUBTITLE = `${rows.length} ${SUBCATEGORY.toLowerCase()} tiles in ${categories.length} ${CATEGORY.toLowerCase()} blocks · area ∝ ${VALUE}, ${fmt.format(grandTotal)} in total`;

// The community package has no treemap: a custom layer draws the tiles through
// the container's px-unit scales, labels only where the text fits its tile.
function Treemap() {
  const xScale = useXScale();
  const yScale = useYScale();

  return (
    <g>
      {tiles.map((tile) => {
        const shade = shades.get(tile.category);
        const x = xScale(tile.x);
        const y = yScale(tile.y);
        const w = xScale(tile.x + tile.w) - x;
        const h = yScale(tile.y + tile.h) - y;
        const pct = ((tile.value / grandTotal) * 100).toFixed(1);

        if (tile.level === 0) {
          const header = `${tile.name} · ${fmt.format(tile.value)}`;
          const headerFits = w - 16 >= header.length * LABEL_FONT * CHAR_W;
          const nameFits = w - 16 >= tile.name.length * LABEL_FONT * CHAR_W && h >= LABEL_FONT + 10;
          return (
            <g key={`cat-${tile.name}`}>
              <rect x={x} y={y} width={w} height={tile.nested ? HEADER_H : h} fill={shade.head}>
                <title>{`${tile.name}: ${fmt.format(tile.value)} (${pct}%)`}</title>
              </rect>
              {(tile.nested ? headerFits : nameFits) && (
                <text x={x + 8} y={y + HEADER_H / 2 + 5} fontSize={LABEL_FONT} fontWeight={700} fill={shade.headInk}>
                  {tile.nested ? header : tile.name}
                </text>
              )}
              <rect x={x} y={y} width={w} height={h} fill="none" stroke={t.pageBg} strokeWidth={GUTTER} />
            </g>
          );
        }

        const nameFits = w - 16 >= tile.name.length * LABEL_FONT * CHAR_W && h >= LABEL_FONT + 12;
        const valueFits = nameFits && h >= LABEL_FONT * 2 + 18;
        return (
          <g key={`sub-${tile.category}-${tile.name}`}>
            <rect x={x} y={y} width={w} height={h} fill={shade.tile} stroke={t.pageBg} strokeWidth={2}>
              <title>{`${tile.category} / ${tile.name}: ${fmt.format(tile.value)} (${pct}%)`}</title>
            </rect>
            {nameFits && (
              <text x={x + 8} y={y + LABEL_FONT + 7} fontSize={LABEL_FONT} fontWeight={500} fill={shade.tileInk}>
                {tile.name}
              </text>
            )}
            {valueFits && (
              <text x={x + 8} y={y + LABEL_FONT * 2 + 12} fontSize={LABEL_FONT - 1} fill={shade.tileInk}>
                {fmt.format(tile.value)}
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

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        series={[]}
        skipAnimation
        margin={MARGIN}
        xAxis={[{ id: "px-x", scaleType: "linear", min: 0, max: PLOT_W, position: "none" }]}
        yAxis={[{ id: "px-y", scaleType: "linear", min: 0, max: PLOT_H, reverse: true, position: "none" }]}
      >
        <Treemap />
      </ChartsContainer>
    </div>
  );
}
