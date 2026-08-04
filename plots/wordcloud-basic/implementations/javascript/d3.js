// anyplot.ai
// wordcloud-basic: Basic Word Cloud
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-04

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const muted = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data: term frequencies from a product-review survey, tagged by sentiment
const words = [
  { word: "reliable", frequency: 142, sentiment: "positive" },
  { word: "expensive", frequency: 118, sentiment: "negative" },
  { word: "intuitive", frequency: 104, sentiment: "positive" },
  { word: "support", frequency: 96, sentiment: "neutral" },
  { word: "battery", frequency: 90, sentiment: "neutral" },
  { word: "sluggish", frequency: 84, sentiment: "negative" },
  { word: "durable", frequency: 79, sentiment: "positive" },
  { word: "shipping", frequency: 74, sentiment: "negative" },
  { word: "design", frequency: 70, sentiment: "positive" },
  { word: "setup", frequency: 66, sentiment: "neutral" },
  { word: "value", frequency: 62, sentiment: "positive" },
  { word: "noisy", frequency: 58, sentiment: "negative" },
  { word: "warranty", frequency: 55, sentiment: "neutral" },
  { word: "lightweight", frequency: 52, sentiment: "positive" },
  { word: "confusing", frequency: 49, sentiment: "negative" },
  { word: "responsive", frequency: 47, sentiment: "positive" },
  { word: "packaging", frequency: 45, sentiment: "neutral" },
  { word: "overpriced", frequency: 43, sentiment: "negative" },
  { word: "sturdy", frequency: 41, sentiment: "positive" },
  { word: "manual", frequency: 39, sentiment: "neutral" },
  { word: "glitchy", frequency: 37, sentiment: "negative" },
  { word: "comfortable", frequency: 35, sentiment: "positive" },
  { word: "delayed", frequency: 33, sentiment: "negative" },
  { word: "helpful", frequency: 32, sentiment: "positive" },
  { word: "compact", frequency: 30, sentiment: "positive" },
  { word: "pricey", frequency: 29, sentiment: "negative" },
  { word: "smooth", frequency: 28, sentiment: "positive" },
  { word: "outdated", frequency: 27, sentiment: "negative" },
  { word: "friendly", frequency: 26, sentiment: "positive" },
  { word: "return", frequency: 25, sentiment: "neutral" },
  { word: "accurate", frequency: 24, sentiment: "positive" },
  { word: "clunky", frequency: 23, sentiment: "negative" },
  { word: "premium", frequency: 22, sentiment: "positive" },
  { word: "delivery", frequency: 21, sentiment: "neutral" },
  { word: "stylish", frequency: 20, sentiment: "positive" },
  { word: "refund", frequency: 19, sentiment: "negative" },
  { word: "efficient", frequency: 18, sentiment: "positive" },
  { word: "instructions", frequency: 17, sentiment: "neutral" },
  { word: "quiet", frequency: 16, sentiment: "positive" },
  { word: "fragile", frequency: 15, sentiment: "negative" },
];

const sentimentColor = (s) => (s === "positive" ? t.palette[0] : s === "negative" ? t.palette[4] : muted);

const fontSize = d3
  .scaleSqrt()
  .domain(d3.extent(words, (d) => d.frequency))
  .range([16, 80]);

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Cloud placement (Vogel/Fermat sunflower spiral + rectangle collision) --
const bounds = { xMin: 30, xMax: width - 30, yMin: 96, yMax: height - 76 };
const cx = (bounds.xMin + bounds.xMax) / 2;
const cy = (bounds.yMin + bounds.yMax) / 2;
const halfW = cx - bounds.xMin;
const halfH = cy - bounds.yMin;
const squash = halfH / halfW; // keep the elliptical search inside the rectangular bounds
const pad = 4;
const placedRects = [];

const overlaps = (r) =>
  placedRects.some((p) => !(r.x + r.w < p.x || r.x > p.x + p.w || r.y + r.h < p.y || r.y > p.y + p.h));

const GOLDEN_ANGLE = 2.399963;
const SPIRAL_STEP = 5;

const findSpot = (bw, bh) => {
  const maxRadius = Math.hypot(halfW, halfH) + Math.max(bw, bh);
  const maxSteps = Math.ceil((maxRadius / SPIRAL_STEP) ** 2);
  for (let step = 0; step < maxSteps; step++) {
    const angle = step * GOLDEN_ANGLE;
    const radius = SPIRAL_STEP * Math.sqrt(step);
    const x = cx + radius * Math.cos(angle);
    const y = cy + radius * Math.sin(angle) * squash;
    const rect = { x: x - bw / 2 - pad, y: y - bh / 2 - pad, w: bw + 2 * pad, h: bh + 2 * pad };
    if (rect.x < bounds.xMin || rect.x + rect.w > bounds.xMax) continue;
    if (rect.y < bounds.yMin || rect.y + rect.h > bounds.yMax) continue;
    if (!overlaps(rect)) return { x, y, rect };
  }
  return null;
};

// Largest (most frequent) terms placed first, near the center.
const ranked = [...words].sort((a, b) => b.frequency - a.frequency);

const cloud = svg.append("g");
for (const d of ranked) {
  const label = cloud
    .append("text")
    .attr("font-size", `${fontSize(d.frequency)}px`)
    .attr("font-weight", d.frequency >= fontSize.domain()[1] * 0.55 ? 700 : 500)
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "central")
    .attr("fill", sentimentColor(d.sentiment))
    .text(d.word);

  const box = label.node().getBBox();
  const spot = findSpot(box.width, box.height);
  if (!spot) {
    label.remove();
    continue;
  }
  label.attr("x", spot.x).attr("y", spot.y);
  placedRects.push(spot.rect);
}

// --- Title ---------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("wordcloud-basic · javascript · d3 · anyplot.ai");

// --- Legend: sentiment color key ------------------------------------------
const legendItems = [
  { label: "Positive", color: t.palette[0] },
  { label: "Negative", color: t.palette[4] },
  { label: "Neutral", color: muted },
];
const legend = svg
  .append("g")
  .attr("transform", `translate(${width / 2 - 170}, ${height - 34})`);
legendItems.forEach((item, i) => {
  const g = legend.append("g").attr("transform", `translate(${i * 130}, 0)`);
  g.append("rect").attr("width", 14).attr("height", 14).attr("rx", 3).attr("fill", item.color);
  g.append("text")
    .attr("x", 22)
    .attr("y", 11)
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(item.label);
});
