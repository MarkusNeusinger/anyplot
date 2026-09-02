// anyplot.ai
// circlepacking-basic: Circle Packing Chart
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data: repository storage breakdown (folders + files, KB) --------------
// Deterministic LCG so file sizes are reproducible without a real RNG.
let seed = 42;
const nextSize = (min, max) => {
  seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
  return min + Math.round((seed / 0x7fffffff) * (max - min));
};

const categories = [
  { id: "src", label: "src/" },
  { id: "assets", label: "assets/" },
  { id: "docs", label: "docs/" },
  { id: "tests", label: "tests/" },
  { id: "config", label: "config/" },
];

const folders = [
  { id: "src-components", parent: "src", label: "components/" },
  { id: "src-hooks", parent: "src", label: "hooks/" },
  { id: "src-utils", parent: "src", label: "utils/" },
  { id: "src-services", parent: "src", label: "services/" },
  { id: "assets-images", parent: "assets", label: "images/" },
  { id: "assets-fonts", parent: "assets", label: "fonts/" },
  { id: "assets-icons", parent: "assets", label: "icons/" },
  { id: "docs-guides", parent: "docs", label: "guides/" },
  { id: "docs-api", parent: "docs", label: "api/" },
  { id: "tests-unit", parent: "tests", label: "unit/" },
  { id: "tests-integration", parent: "tests", label: "integration/" },
];

const filesByParent = {
  "src-components": ["Header.tsx", "Footer.tsx", "Sidebar.tsx", "Chart.tsx", "Modal.tsx", "Button.tsx"],
  "src-hooks": ["useAuth.ts", "useFetch.ts", "useTheme.ts", "useDebounce.ts"],
  "src-utils": ["format.ts", "validate.ts", "parse.ts", "colors.ts", "dates.ts"],
  "src-services": ["api.ts", "storage.ts", "analytics.ts", "sockets.ts"],
  "assets-images": ["hero.png", "logo.png", "banner.png", "avatar.png", "og-image.png"],
  "assets-fonts": ["Inter.woff2", "Mono.woff2", "Serif.woff2"],
  "assets-icons": ["arrow.svg", "check.svg", "close.svg", "search.svg"],
  "docs-guides": ["quickstart.md", "deployment.md", "theming.md", "faq.md"],
  "docs-api": ["reference.md", "changelog.md", "migration.md"],
  "tests-unit": ["format.test.ts", "validate.test.ts", "parse.test.ts", "colors.test.ts", "dates.test.ts", "api.test.ts"],
  "tests-integration": ["auth.spec.ts", "checkout.spec.ts", "search.spec.ts", "onboarding.spec.ts"],
  config: ["tsconfig.json", "eslint.config.js", "vite.config.ts"],
};

const nodes = [{ id: "repo", parent: null, value: null, label: "repo/" }];
for (const c of categories) nodes.push({ id: c.id, parent: "repo", value: null, label: c.label });
for (const f of folders) nodes.push({ id: f.id, parent: f.parent, value: null, label: f.label });
for (const [parent, files] of Object.entries(filesByParent)) {
  const sizeRange = parent === "assets-images" ? [60, 480] : parent.startsWith("assets") ? [10, 90] : [4, 60];
  for (const name of files) {
    nodes.push({ id: `${parent}/${name}`, parent, value: nextSize(...sizeRange), label: name });
  }
}

// --- Hierarchy + pack layout -------------------------------------------------
const margin = { top: 110, right: 50, bottom: 50, left: 50 };
const diameter = Math.min(width - margin.left - margin.right, height - margin.top - margin.bottom);

const root = d3
  .stratify()
  .id((d) => d.id)
  .parentId((d) => d.parent)(nodes)
  .sum((d) => d.value || 0)
  .sort((a, b) => b.value - a.value);

d3.pack().size([diameter, diameter]).padding((d) => (d.depth === 0 ? 12 : d.depth === 1 ? 7 : 3))(root);

// --- Color: hue by top-level category, opacity deepens with nesting --------
const color = d3.scaleOrdinal(
  categories.map((c) => c.id),
  t.palette.slice(0, categories.length)
);
const categoryOf = (d) => d.ancestors().find((a) => a.depth === 1);
const opacityByDepth = { 1: 0.16, 2: 0.4, 3: 0.9 };

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg
  .append("g")
  .attr("transform", `translate(${(width - diameter) / 2},${margin.top + (height - margin.top - margin.bottom - diameter) / 2})`);

// Root boundary — outline only, no fill, encompasses every child circle.
g.append("circle")
  .attr("cx", root.x)
  .attr("cy", root.y)
  .attr("r", root.r)
  .attr("fill", "none")
  .attr("stroke", t.grid)
  .attr("stroke-width", 1.5);

const packNodes = root.descendants().filter((d) => d.depth > 0);

// Circles only — nested children are drawn after (and on top of) their parent,
// matching the pack layout's visual containment.
g.selectAll("circle.node")
  .data(packNodes)
  .join("circle")
  .attr("class", "node")
  .attr("cx", (d) => d.x)
  .attr("cy", (d) => d.y)
  .attr("r", (d) => d.r)
  .attr("fill", (d) => color(categoryOf(d).data.id))
  .attr("fill-opacity", (d) => opacityByDepth[d.depth])
  .attr("stroke", (d) => (!d.children ? t.pageBg : "none"))
  .attr("stroke-width", (d) => (!d.children ? 1.5 : 0));

// Labels are drawn in a later pass so every label paints on top of every
// circle — including a category label that would otherwise sit under its own
// packed children.
const estCharWidth = 0.56;
const fitLabel = (d, fontSize) => {
  const maxChars = Math.max(3, Math.floor((d.r * 1.7) / (fontSize * estCharWidth)));
  return d.data.label.length > maxChars ? `${d.data.label.slice(0, maxChars - 1)}…` : d.data.label;
};

// Category labels sit near the top rim, clear of the packed children below.
g.selectAll("text.category")
  .data(packNodes.filter((d) => d.depth === 1 && d.r > 40))
  .join("text")
  .attr("class", "category")
  .attr("x", (d) => d.x)
  .attr("y", (d) => d.y - d.r + 26)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .style("font-weight", "700")
  .text((d) => fitLabel(d, 17));

// Leaf labels sit centered — leaves have no children to be covered by.
g.selectAll("text.leaf")
  .data(packNodes.filter((d) => !d.children && d.r > 24))
  .join("text")
  .attr("class", "leaf")
  .attr("x", (d) => d.x)
  .attr("y", (d) => d.y)
  .attr("dy", "0.35em")
  .attr("text-anchor", "middle")
  .attr("fill", t.pageBg)
  .style("font-size", (d) => `${Math.min(15, Math.max(10, d.r / 3.4))}px`)
  .text((d) => fitLabel(d, Math.min(15, Math.max(10, d.r / 3.4))));

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "24px")
  .style("font-weight", "600")
  .text("circlepacking-basic · javascript · d3 · anyplot.ai");
