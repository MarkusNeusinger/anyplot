// anyplot.ai
// circlepacking-basic: Circle Packing Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-02
//# anyplot-orientation: square

// Highcharts' packed-bubble / circle-packing series lives in the
// highcharts-more add-on module, which is not vendored here — only the core
// bundle (with its SVGRenderer) is loaded. So the hierarchy below is packed
// with a small deterministic relaxation algorithm (index-seeded, no RNG) and
// drawn natively with `chart.renderer`: a root ring, one ring per directory,
// and (for one directory) a nested sub-ring for its files, three levels deep.
// The same recursive layout/render pair handles every level. No other
// charting library is used.

const t = window.ANYPLOT_TOKENS;

// --- Data: a small repository's directory sizes (KB), up to 3 levels deep ----
// Most directories hold files directly (2 levels below root); "components/"
// is further split into named files to exercise a 3rd nesting level.
const CATEGORIES = [
  {
    id: "src",
    label: "src/",
    children: [
      {
        id: "src-components",
        label: "components/",
        children: [
          { id: "src-components-table", label: "Table.jsx", value: 150 },
          { id: "src-components-modal", label: "Modal.jsx", value: 130 },
          { id: "src-components-form", label: "Form.jsx", value: 120 },
          { id: "src-components-button", label: "Button.jsx", value: 80 },
        ],
      },
      { id: "src-api", label: "api.js", value: 340 },
      { id: "src-store", label: "store.js", value: 210 },
      { id: "src-utils", label: "utils.js", value: 120 },
      { id: "src-hooks", label: "hooks.js", value: 95 },
      { id: "src-styles", label: "styles.css", value: 70 },
      { id: "src-types", label: "types.d.ts", value: 55 },
    ],
  },
  {
    id: "tests",
    label: "tests/",
    children: [
      { id: "tests-unit", label: "unit/", value: 200 },
      { id: "tests-integration", label: "integration/", value: 150 },
      { id: "tests-e2e", label: "e2e/", value: 90 },
      { id: "tests-fixtures", label: "fixtures/", value: 60 },
      { id: "tests-mocks", label: "mocks/", value: 45 },
    ],
  },
  {
    id: "docs",
    label: "docs/",
    children: [
      { id: "docs-api", label: "api-reference.md", value: 130 },
      { id: "docs-guide", label: "guide.md", value: 85 },
      { id: "docs-changelog", label: "changelog.md", value: 50 },
      { id: "docs-readme", label: "readme.md", value: 45 },
    ],
  },
  {
    id: "assets",
    label: "assets/",
    children: [
      { id: "assets-images", label: "images/", value: 380 },
      { id: "assets-fonts", label: "fonts/", value: 190 },
      { id: "assets-videos", label: "videos/", value: 140 },
      { id: "assets-icons", label: "icons/", value: 95 },
      { id: "assets-logo", label: "logo.svg", value: 40 },
    ],
  },
  {
    id: "build",
    label: "build/",
    children: [
      { id: "build-bundle", label: "bundle.js", value: 600 },
      { id: "build-vendor", label: "vendor.js", value: 420 },
      { id: "build-maps", label: "sourcemaps/", value: 210 },
      { id: "build-manifest", label: "manifest.json", value: 45 },
    ],
  },
];

// Directories are abstract categories, so the Imprint palette is used in
// canonical order — src = brand green (palette[0]).
const categoryColor = (i) => t.palette[i % t.palette.length];

const formatSize = (kb) => (kb >= 1000 ? `${(kb / 1000).toFixed(1)} MB` : `${kb} KB`);

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Pick readable label ink by the fill's own luminance rather than the active
// theme — a leaf circle's colour is the same in light and dark mode, so the
// text riding on top needs the ink value with contrast to THAT colour, not to
// the page. #1A1A17 / #F0EFE8 are exactly the light/dark INK tokens reused
// for this purpose, never a new custom hex.
function contrastInk(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const lin = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  const luminance = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  return luminance > 0.42 ? "#1A1A17" : "#F0EFE8";
}

// --- Circle packing: a small deterministic relaxation, applied per level -----
// Seed circles on a ring (index-based angle, no RNG), then repeatedly resolve
// overlaps and pull toward the centroid until the group settles into a tight,
// non-overlapping cluster. The same routine packs siblings at every depth —
// files within a directory, a directory alongside files within its parent,
// and top-level directories within the repository.
function packCircles(items, gap) {
  if (items.length === 0) return { placed: [], boundingRadius: 0 };
  if (items.length === 1) {
    return { placed: [{ id: items[0].id, x: 0, y: 0, r: items[0].r }], boundingRadius: items[0].r };
  }
  const n = items.length;
  const nodes = items.map((it, i) => {
    const theta = (i / n) * Math.PI * 2;
    const seedR = it.r * 1.6 + i * 4;
    return { id: it.id, r: it.r, x: seedR * Math.cos(theta), y: seedR * Math.sin(theta) };
  });
  for (let iter = 0; iter < 260; iter += 1) {
    nodes.forEach((a) => {
      a.x -= a.x * 0.02;
      a.y -= a.y * 0.02;
    });
    for (let i = 0; i < n; i += 1) {
      for (let j = i + 1; j < n; j += 1) {
        const a = nodes[i];
        const b = nodes[j];
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let dist = Math.sqrt(dx * dx + dy * dy);
        const minDist = a.r + b.r + gap;
        if (dist < 1e-6) {
          dx = 0.01 * (i + 1);
          dy = 0.01 * (j + 1);
          dist = Math.sqrt(dx * dx + dy * dy);
        }
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
  const minX = Math.min(...nodes.map((nd) => nd.x - nd.r));
  const maxX = Math.max(...nodes.map((nd) => nd.x + nd.r));
  const minY = Math.min(...nodes.map((nd) => nd.y - nd.r));
  const maxY = Math.max(...nodes.map((nd) => nd.y + nd.r));
  const ox = (minX + maxX) / 2;
  const oy = (minY + maxY) / 2;
  nodes.forEach((nd) => {
    nd.x -= ox;
    nd.y -= oy;
  });
  let boundingRadius = 0;
  nodes.forEach((nd) => {
    const d = Math.sqrt(nd.x * nd.x + nd.y * nd.y) + nd.r;
    if (d > boundingRadius) boundingRadius = d;
  });
  return { placed: nodes, boundingRadius };
}

// --- Layout: a recursive pack, depth 0 = root, 1 = category, 2+ = nested ----
// Circle area, not radius, encodes size: radius = sqrt(value) in abstract
// units; everything is rescaled to pixels once the final plot area is known.
// Every node below the root inherits its top-level category's colour index,
// so a nested sub-directory (e.g. "components/") reads as part of "src/".
const LEAF_GAP = 1.4;
const RING_PADDING = 6.5;
const CATEGORY_GAP = 7;
const ROOT_PADDING = 7;

const leafRadius = (value) => Math.sqrt(value);

function layoutNode(node, depth, categoryIndex) {
  if (!node.children) {
    return { id: node.id, label: node.label, value: node.value, r: leafRadius(node.value), depth, categoryIndex, leaf: true };
  }
  const childLayouts = node.children.map((child, i) => layoutNode(child, depth + 1, depth === 0 ? i : categoryIndex));
  const gap = depth === 0 ? CATEGORY_GAP : LEAF_GAP;
  const { placed, boundingRadius } = packCircles(
    childLayouts.map((cl) => ({ id: cl.id, r: cl.r })),
    gap,
  );
  const totalValue = childLayouts.reduce((s, cl) => s + cl.value, 0);
  const children = childLayouts.map((cl) => {
    const p = placed.find((pp) => pp.id === cl.id);
    return { ...cl, x: p.x, y: p.y };
  });
  // Padding shrinks with depth so nested rings hug their contents a little
  // tighter than the outer category rings do.
  const padding = depth === 0 ? ROOT_PADDING : depth === 1 ? RING_PADDING : RING_PADDING * 0.7;
  return {
    id: node.id,
    label: node.label,
    value: totalValue,
    r: boundingRadius + padding,
    depth,
    categoryIndex,
    leaf: false,
    children,
  };
}

const tree = layoutNode({ id: "root", label: "repository", children: CATEGORIES }, 0, null);

// --- Chart shell (no series — every circle is drawn with the renderer) -------
const chart = Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    marginTop: 100,
    marginBottom: 40,
    marginLeft: 40,
    marginRight: 40,
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "circlepacking-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Repository directory sizes — circle area = file/folder size (KB), colour = directory",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: { visible: false },
  yAxis: { visible: false },
  legend: { enabled: false },
  plotOptions: { series: { animation: false } },
  series: [],
});

const cx = chart.plotLeft + chart.plotWidth / 2;
const cy = chart.plotTop + chart.plotHeight / 2;
const radiusMax = Math.min(chart.plotWidth, chart.plotHeight) / 2;
const finalScale = (radiusMax - 12) / tree.r;
const px = (x) => cx + x * finalScale;
const py = (y) => cy + y * finalScale;
const pr = (r) => r * finalScale;

function addTitle(el, text) {
  const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
  title.textContent = text;
  el.element.appendChild(title);
}

const g = chart.renderer.g("circle-packing").add();

// --- Render: recursive, depth drives stroke weight / fill alpha / labels ----
// depth 0 = root outline, depth 1 = category ring, depth 2+ = nested rings
// (subtly thinner stroke, higher fill alpha) or solid leaf circles.
function renderNode(node, parentX, parentY, pathPrefix) {
  const x = px(parentX + (node.x ?? 0));
  const y = py(parentY + (node.y ?? 0));
  const r = pr(node.r);

  if (node.leaf) {
    const color = categoryColor(node.categoryIndex);
    const leaf = chart.renderer
      .circle(x, y, r)
      .attr({ fill: color, stroke: t.pageBg, "stroke-width": 1.5 })
      .add(g);
    addTitle(leaf, `${pathPrefix}${node.label} — ${formatSize(node.value)}`);

    if (r >= 28) {
      const fontSize = Math.max(10, Math.min(13, Math.round(r * 0.26)));
      const maxChars = Math.max(3, Math.floor((r * 1.7) / (fontSize * 0.58)));
      const text = node.label.length > maxChars ? `${node.label.slice(0, maxChars - 1)}…` : node.label;
      chart.renderer
        .text(text, x, y + fontSize * 0.35)
        .attr({ align: "center" })
        .css({ color: contrastInk(color), fontSize: `${fontSize}px`, fontWeight: "500" })
        .add(g);
    }
    return;
  }

  if (node.depth === 0) {
    const root = chart.renderer
      .circle(x, y, r)
      .attr({ fill: "transparent", stroke: t.grid, "stroke-width": 1.5 })
      .add(g);
    addTitle(root, `repository — ${formatSize(node.value)} total`);
  } else {
    const isCategory = node.depth === 1;
    const color = categoryColor(node.categoryIndex);
    const ring = chart.renderer
      .circle(x, y, r)
      .attr({
        fill: hexToRgba(color, isCategory ? 0.1 : 0.17),
        stroke: color,
        "stroke-width": isCategory ? 2.5 : 1.8,
      })
      .add(g);
    addTitle(ring, `${pathPrefix}${node.label} — ${formatSize(node.value)} total`);

    const labelThreshold = isCategory ? 55 : 40;
    if (r >= labelThreshold) {
      const fontSize = isCategory ? Math.max(12, Math.min(16, Math.round(r * 0.1))) : Math.max(11, Math.min(13, Math.round(r * 0.12)));
      chart.renderer
        .text(`${node.label} · ${formatSize(node.value)}`, x, y - r + fontSize + 6)
        .attr({ align: "center" })
        .css({ color: t.ink, fontSize: `${fontSize}px`, fontWeight: "600" })
        .add(g);
    }
  }

  const childPathPrefix = node.depth === 0 ? "" : `${pathPrefix}${node.label}`;
  const originX = parentX + (node.x ?? 0);
  const originY = parentY + (node.y ?? 0);
  node.children.forEach((child) => renderNode(child, originX, originY, childPathPrefix));
}

renderNode(tree, 0, 0, "");

// Static-frame timing signal for the harness.
window.__anyplotReady = true;
