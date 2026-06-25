// anyplot.ai
// venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-25
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const THEME = window.ANYPLOT_THEME || "light";
const inkMuted = THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data ---
// Three circles defining tech product categories
const CIRCLES = [
  { name: "Overhyped",       cx: 600, cy: 420, r: 270, color: t.palette[0] },
  { name: "Actually Useful", cx: 738, cy: 658, r: 270, color: t.palette[1] },
  { name: "Secretly Loved",  cx: 462, cy: 658, r: 270, color: t.palette[2] },
];

// Centroid of each Venn zone for item placement
const ZONE_CENTROIDS = {
  A:       { x: 600, y: 254 },
  B:       { x: 878, y: 740 },
  C:       { x: 322, y: 740 },
  AB:      { x: 730, y: 506 },
  AC:      { x: 470, y: 506 },
  BC:      { x: 600, y: 780 },
  ABC:     { x: 600, y: 578 },
  outside: { x: 975, y: 300 },
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

// --- SVG ---
const svg = d3.select("#container").append("svg")
  .attr("width", width)
  .attr("height", height);

// --- Circles (semi-transparent fills, colored strokes) ---
CIRCLES.forEach(c => {
  svg.append("circle")
    .attr("cx", c.cx).attr("cy", c.cy).attr("r", c.r)
    .attr("fill", c.color).attr("fill-opacity", 0.12)
    .attr("stroke", c.color).attr("stroke-width", 2.5).attr("stroke-opacity", 0.65);
});

// --- Category labels (outside each circle, editorial serif) ---
const catFont = "Georgia, 'Times New Roman', serif";

// Circle A: above
svg.append("text")
  .attr("x", CIRCLES[0].cx)
  .attr("y", CIRCLES[0].cy - CIRCLES[0].r - 24)
  .attr("text-anchor", "middle")
  .attr("fill", CIRCLES[0].color)
  .style("font-size", "20px").style("font-weight", "700")
  .style("font-family", catFont)
  .text(CIRCLES[0].name);

// Circle B: right side (two lines)
const bx = CIRCLES[1].cx + CIRCLES[1].r + 26;
["Actually", "Useful"].forEach((word, i) => {
  svg.append("text")
    .attr("x", bx).attr("y", CIRCLES[1].cy - 13 + i * 28)
    .attr("text-anchor", "start").attr("fill", CIRCLES[1].color)
    .style("font-size", "20px").style("font-weight", "700")
    .style("font-family", catFont).text(word);
});

// Circle C: left side (two lines)
const cx0 = CIRCLES[2].cx - CIRCLES[2].r - 26;
["Secretly", "Loved"].forEach((word, i) => {
  svg.append("text")
    .attr("x", cx0).attr("y", CIRCLES[2].cy - 13 + i * 28)
    .attr("text-anchor", "end").attr("fill", CIRCLES[2].color)
    .style("font-size", "20px").style("font-weight", "700")
    .style("font-family", catFont).text(word);
});

// --- Items (stacked vertically within each zone) ---
const itemsByZone = d3.group(items, d => d.zone);
const SPACING = 24;

itemsByZone.forEach((zoneItems, zone) => {
  const { x: zx, y: zy } = ZONE_CENTROIDS[zone];
  const n = zoneItems.length;
  const totalH = (n - 1) * SPACING;
  const isOutside = zone === "outside";

  if (isOutside) {
    svg.append("text")
      .attr("x", zx).attr("y", zy - totalH / 2 - 20)
      .attr("text-anchor", "middle").attr("fill", inkMuted)
      .style("font-size", "11px").style("font-style", "italic")
      .text("outside all circles");
  }

  zoneItems.forEach((item, i) => {
    const y = zy - totalH / 2 + i * SPACING;
    svg.append("text")
      .attr("x", zx).attr("y", y)
      .attr("text-anchor", "middle").attr("dominant-baseline", "middle")
      .attr("fill", isOutside ? inkMuted : t.inkSoft)
      .style("font-size", "14px")
      .style("font-style", isOutside ? "italic" : "normal")
      .style("font-family", "system-ui, -apple-system, sans-serif")
      .text(item.label);
  });
});

// --- Title ---
const titleText = "venn-labeled-items · javascript · d3 · anyplot.ai";
svg.append("text")
  .attr("x", width / 2).attr("y", 46)
  .attr("text-anchor", "middle").attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .text(titleText);
