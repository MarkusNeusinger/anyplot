// anyplot.ai
// venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
// Library: d3 7.9.0 | JavaScript 22.23.0
// Quality: 87/100 | Created: 2026-06-25
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const THEME = window.ANYPLOT_THEME || "light";
const inkMuted = THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data ---
const circleData = [
  { name: "Overhyped",       cx: 600, cy: 480, r: 270 },
  { name: "Actually Useful", cx: 738, cy: 718, r: 270 },
  { name: "Secretly Loved",  cx: 462, cy: 718, r: 270 },
];

// D3 ordinal scale maps category names to Imprint palette in canonical order
const colorScale = d3.scaleOrdinal()
  .domain(circleData.map(d => d.name))
  .range(t.palette.slice(0, 3));

// Centroid of each Venn zone for label placement
const ZONE_CENTROIDS = {
  A:       { x: 600, y: 314 },
  B:       { x: 878, y: 800 },
  C:       { x: 322, y: 800 },
  AB:      { x: 730, y: 566 },
  AC:      { x: 470, y: 566 },
  BC:      { x: 600, y: 840 },
  ABC:     { x: 600, y: 638 },
  outside: { x: 975, y: 360 },
};

const items = [
  { label: "NFTs",              zone: "A"       },
  { label: "Metaverse",         zone: "A"       },
  { label: "Segway",            zone: "A"       },
  { label: "Google Glass",      zone: "A"       },
  { label: "Wikipedia",         zone: "B"       },
  { label: "GPS Navigation",    zone: "B"       },
  { label: "Cloud Backup",      zone: "B"       },
  { label: "Password Managers", zone: "B"       },
  { label: "Spreadsheets",      zone: "C"       },
  { label: "Fax Machines",      zone: "C"       },
  { label: "Cable TV",          zone: "C"       },
  { label: "ChatGPT",           zone: "AB"      },
  { label: "Electric Scooters", zone: "AB"      },
  { label: "TikTok",            zone: "AC"      },
  { label: "Gamification",      zone: "AC"      },
  { label: "Dark Mode",         zone: "BC"      },
  { label: "RSS Feeds",         zone: "BC"      },
  { label: "Sourdough",         zone: "ABC"     },
  { label: "Zoom",              zone: "ABC"     },
  { label: "Landlines",         zone: "outside" },
];

// Use d3.group to partition items by zone, then compute vertical stacking positions
const SPACING = 24;
const itemsByZone = d3.group(items, d => d.zone);

itemsByZone.forEach((zoneItems, zone) => {
  const { x: zx, y: zy } = ZONE_CENTROIDS[zone];
  const totalH = (zoneItems.length - 1) * SPACING;
  zoneItems.forEach((item, i) => {
    item.x = zx;
    item.y = zy - totalH / 2 + i * SPACING;
  });
});

// --- SVG ---
const svg = d3.select("#container").append("svg")
  .attr("width", width)
  .attr("height", height);

// --- Circles (data join, semi-transparent fills, colored strokes) ---
svg.selectAll("circle.venn-circle").data(circleData).join("circle")
  .attr("class", "venn-circle")
  .attr("cx", d => d.cx).attr("cy", d => d.cy).attr("r", d => d.r)
  .attr("fill", d => colorScale(d.name)).attr("fill-opacity", 0.12)
  .attr("stroke", d => colorScale(d.name))
  .attr("stroke-width", 2.5).attr("stroke-opacity", 0.65);

// --- Category labels (data join per circle, editorial serif) ---
const catFont = "Georgia, 'Times New Roman', serif";

const catLabelDefs = [
  { name: "Overhyped",       lines: ["Overhyped"],          x: circleData[0].cx,                        y: circleData[0].cy - circleData[0].r - 20, anchor: "middle" },
  { name: "Actually Useful", lines: ["Actually", "Useful"], x: circleData[1].cx + circleData[1].r + 26, y: circleData[1].cy - 13,                  anchor: "start"  },
  { name: "Secretly Loved",  lines: ["Secretly", "Loved"],  x: circleData[2].cx - circleData[2].r - 26, y: circleData[2].cy - 13,                  anchor: "end"    },
];

catLabelDefs.forEach(def => {
  const catG = svg.append("g");
  catG.selectAll("text").data(def.lines).join("text")
    .attr("x", def.x)
    .attr("y", (_, i) => def.y + i * 28)
    .attr("text-anchor", def.anchor)
    .attr("fill", colorScale(def.name))
    .style("font-size", "20px").style("font-weight", "700")
    .style("font-family", catFont)
    .text(d => d);
});

// --- "outside all circles" annotation ---
const outsideItems = items.filter(d => d.zone === "outside");
if (outsideItems.length) {
  svg.append("text")
    .attr("x", ZONE_CENTROIDS.outside.x)
    .attr("y", d3.min(outsideItems, d => d.y) - 22)
    .attr("text-anchor", "middle").attr("fill", inkMuted)
    .style("font-size", "14px").style("font-style", "italic")
    .text("outside all circles");
}

// --- Items (data join over all items, positions from d3.group stacking) ---
svg.selectAll("text.venn-item").data(items).join("text")
  .attr("class", "venn-item")
  .attr("x", d => d.x)
  .attr("y", d => d.y)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "middle")
  .attr("fill", d => d.zone === "outside" ? inkMuted : t.inkSoft)
  .style("font-size", "14px")
  .style("font-style", d => d.zone === "outside" ? "italic" : "normal")
  .style("font-family", "system-ui, -apple-system, sans-serif")
  .text(d => d.label);

// --- Title ---
svg.append("text")
  .attr("x", width / 2).attr("y", 46)
  .attr("text-anchor", "middle").attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .text("venn-labeled-items · javascript · d3 · anyplot.ai");
