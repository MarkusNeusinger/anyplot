// anyplot.ai
// wordcloud-basic: Basic Word Cloud
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: pending | Created: 2026-08-04

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = "Inter, system-ui, -apple-system, sans-serif";
const FONT_MIN = 22; // px, the least frequent term
const FONT_MAX = 118; // px, the most frequent term
const FIT_FACTOR = 0.92; // when a term finds no free spot, every size shrinks by this factor and the layout reruns
const MIN_TEXT = 14; // px, the smallest term never goes below this, the layout drops terms instead
const BOX_PAD = 5; // px of clearance around every word
const ANGLE_STEP = 0.16; // spiral step, radians
const RADIUS_STEP = 1.6; // spiral growth per turn, px
const TITLE = "wordcloud-basic · javascript · muix · anyplot.ai";
const TITLE_H = 80;
const INSET = 26;

// Columns: set these to your data's column names
const TERM = "Term"; // role: word
const MENTIONS = "Mentions"; // role: frequency

// Data: replace this block with your own records, one object per row
// Keyword mentions in the abstracts of a renewable-energy research corpus.
const data = [
  { [TERM]: "solar", [MENTIONS]: 980 },
  { [TERM]: "battery", [MENTIONS]: 860 },
  { [TERM]: "grid", [MENTIONS]: 790 },
  { [TERM]: "storage", [MENTIONS]: 740 },
  { [TERM]: "wind", [MENTIONS]: 705 },
  { [TERM]: "efficiency", [MENTIONS]: 640 },
  { [TERM]: "emissions", [MENTIONS]: 590 },
  { [TERM]: "hydrogen", [MENTIONS]: 540 },
  { [TERM]: "photovoltaic", [MENTIONS]: 505 },
  { [TERM]: "turbine", [MENTIONS]: 470 },
  { [TERM]: "microgrid", [MENTIONS]: 430 },
  { [TERM]: "lithium", [MENTIONS]: 400 },
  { [TERM]: "sustainability", [MENTIONS]: 375 },
  { [TERM]: "carbon", [MENTIONS]: 350 },
  { [TERM]: "capacity", [MENTIONS]: 330 },
  { [TERM]: "infrastructure", [MENTIONS]: 310 },
  { [TERM]: "policy", [MENTIONS]: 290 },
  { [TERM]: "investment", [MENTIONS]: 270 },
  { [TERM]: "resilience", [MENTIONS]: 250 },
  { [TERM]: "biomass", [MENTIONS]: 235 },
  { [TERM]: "geothermal", [MENTIONS]: 220 },
  { [TERM]: "recycling", [MENTIONS]: 205 },
  { [TERM]: "deployment", [MENTIONS]: 190 },
  { [TERM]: "monitoring", [MENTIONS]: 175 },
  { [TERM]: "materials", [MENTIONS]: 165 },
  { [TERM]: "forecast", [MENTIONS]: 150 },
  { [TERM]: "adoption", [MENTIONS]: 140 },
  { [TERM]: "modeling", [MENTIONS]: 130 },
  { [TERM]: "funding", [MENTIONS]: 120 },
  { [TERM]: "transition", [MENTIONS]: 110 },
  { [TERM]: "climate", [MENTIONS]: 100 },
  { [TERM]: "innovation", [MENTIONS]: 92 },
  { [TERM]: "cleantech", [MENTIONS]: 85 },
  { [TERM]: "renewables", [MENTIONS]: 78 },
  { [TERM]: "smartgrid", [MENTIONS]: 70 },
  { [TERM]: "cost", [MENTIONS]: 62 },
  { [TERM]: "scale", [MENTIONS]: 55 },
  { [TERM]: "research", [MENTIONS]: 48 },
  { [TERM]: "market", [MENTIONS]: 40 },
];

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[TERM] != null && d[MENTIONS] != null && d[MENTIONS] > 0);
const counts = rows.map((d) => d[MENTIONS]);
const countMin = Math.min(...counts);
const countMax = Math.max(...counts);
const cloudW = window.ANYPLOT_SIZE.width - 2 * INSET;
const cloudH = window.ANYPLOT_SIZE.height - TITLE_H - 2 * INSET;
const aspect = cloudH / cloudW;

// Archimedean-spiral layout in px: the most frequent term first, each one
// spiralling out from the centre until its measured box is clear of every box
// placed so far. The spiral runs out to the cloud's corners. Font size follows
// the square root of the count, so area tracks it; when any term finds no spot,
// all sizes shrink by one common factor and the whole layout reruns, so the
// size order always matches the counts. Only once the smallest term would drop
// under MIN_TEXT does the last pass leave the terms without a spot out.
const measure = document.createElement("canvas").getContext("2d");
const ordered = [...rows].sort((a, b) => b[MENTIONS] - a[MENTIONS]);
const maxRadius = Math.hypot(cloudW / 2, cloudH / (2 * aspect));
let placed = [];
for (let scale = 1; placed.length < ordered.length && FONT_MIN * scale >= MIN_TEXT; scale *= FIT_FACTOR) {
  placed = [];
  for (const d of ordered) {
    const fontSize = scale * (FONT_MIN + (FONT_MAX - FONT_MIN) * Math.sqrt((d[MENTIONS] - countMin) / (countMax - countMin || 1)));
    measure.font = `600 ${fontSize}px ${FONT}`;
    const boxW = measure.measureText(d[TERM]).width + 2 * BOX_PAD;
    const boxH = fontSize * 1.15 + 2 * BOX_PAD;
    let spot = null;
    for (let angle = 0, radius = 0; radius <= maxRadius && spot == null; angle += ANGLE_STEP) {
      const cx = cloudW / 2 + radius * Math.cos(angle);
      const cy = cloudH / 2 + radius * Math.sin(angle) * aspect;
      const box = { left: cx - boxW / 2, right: cx + boxW / 2, top: cy - boxH / 2, bottom: cy + boxH / 2 };
      const inside = box.left >= 0 && box.right <= cloudW && box.top >= 0 && box.bottom <= cloudH;
      const clear = placed.every(
        (p) => box.right < p.box.left || box.left > p.box.right || box.bottom < p.box.top || box.top > p.box.bottom,
      );
      if (inside && clear) spot = { term: d[TERM], fontSize, x: cx, y: cy, box };
      radius += (RADIUS_STEP * ANGLE_STEP) / (2 * Math.PI);
    }
    if (spot != null) placed.push(spot);
  }
}

// Centre the finished cloud on its own bounding box
const shiftX = cloudW / 2 - (Math.min(...placed.map((p) => p.box.left)) + Math.max(...placed.map((p) => p.box.right))) / 2;
const shiftY = cloudH / 2 - (Math.min(...placed.map((p) => p.box.top)) + Math.max(...placed.map((p) => p.box.bottom))) / 2;
const SUBTITLE = `${placed.length === rows.length ? rows.length : `${placed.length} of ${rows.length}`} terms · font size grows with the square root of ${MENTIONS.toLowerCase()}`;

// The community package has no word cloud: a custom layer sets each term at
// its layout position through the chart's linear scales.
function WordLayer() {
  const xScale = useXScale();
  const yScale = useYScale();

  return (
    <g>
      {placed.map((p) => (
        <text
          key={p.term}
          x={xScale(p.x + shiftX)}
          y={yScale(p.y + shiftY)}
          fontSize={p.fontSize}
          fontFamily={FONT}
          fontWeight={600}
          textAnchor="middle"
          dominantBaseline="central"
          fill={t.palette[0]}
        >
          {p.term}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box", textAlign: "center" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        series={[]}
        skipAnimation
        margin={INSET}
        xAxis={[{ id: "layout-x", min: 0, max: cloudW, position: "none" }]}
        yAxis={[{ id: "layout-y", min: 0, max: cloudH, reverse: true, position: "none" }]}
      >
        <WordLayer />
      </ChartsContainer>
    </div>
  );
}
