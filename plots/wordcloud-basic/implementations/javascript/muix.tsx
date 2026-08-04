// anyplot.ai
// wordcloud-basic: Basic Word Cloud
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-04

import { ChartContainer } from "@mui/x-charts/ChartContainer";

const t = window.ANYPLOT_TOKENS;
const FONT = "Inter, system-ui, -apple-system, sans-serif";

// --- Data: term frequencies from a renewable-energy research corpus --------
// (word, mention count) — a typical Zipf-shaped tail from abstract keywords.
const WORDS = [
  { word: "solar", frequency: 980 },
  { word: "battery", frequency: 860 },
  { word: "grid", frequency: 790 },
  { word: "storage", frequency: 740 },
  { word: "wind", frequency: 705 },
  { word: "efficiency", frequency: 640 },
  { word: "emissions", frequency: 590 },
  { word: "hydrogen", frequency: 540 },
  { word: "photovoltaic", frequency: 505 },
  { word: "turbine", frequency: 470 },
  { word: "microgrid", frequency: 430 },
  { word: "lithium", frequency: 400 },
  { word: "sustainability", frequency: 375 },
  { word: "carbon", frequency: 350 },
  { word: "capacity", frequency: 330 },
  { word: "infrastructure", frequency: 310 },
  { word: "policy", frequency: 290 },
  { word: "investment", frequency: 270 },
  { word: "resilience", frequency: 250 },
  { word: "biomass", frequency: 235 },
  { word: "geothermal", frequency: 220 },
  { word: "recycling", frequency: 205 },
  { word: "deployment", frequency: 190 },
  { word: "monitoring", frequency: 175 },
  { word: "materials", frequency: 165 },
  { word: "forecast", frequency: 150 },
  { word: "adoption", frequency: 140 },
  { word: "modeling", frequency: 130 },
  { word: "funding", frequency: 120 },
  { word: "transition", frequency: 110 },
  { word: "climate", frequency: 100 },
  { word: "innovation", frequency: 92 },
  { word: "cleantech", frequency: 85 },
  { word: "renewables", frequency: 78 },
  { word: "smartgrid", frequency: 70 },
  { word: "cost", frequency: 62 },
  { word: "scale", frequency: 55 },
  { word: "research", frequency: 48 },
  { word: "market", frequency: 40 },
];

// --- Font-size scale: sqrt so rendered AREA follows frequency, not height ---
const FONT_MIN = 16;
const FONT_MAX = 128;
const FREQUENCIES = WORDS.map((w) => w.frequency);
const MIN_FREQ = Math.min(...FREQUENCIES);
const MAX_FREQ = Math.max(...FREQUENCIES);

function fontSizeFor(frequency) {
  const norm = Math.sqrt((frequency - MIN_FREQ) / (MAX_FREQ - MIN_FREQ));
  return Math.round(FONT_MIN + (FONT_MAX - FONT_MIN) * norm);
}

// Measure each word's rendered glyph width with the real page font metrics so
// the spiral placement below never guesses — and never collides.
const measureCtx = document.createElement("canvas").getContext("2d");

function textWidth(word, fontSize) {
  measureCtx.font = `600 ${fontSize}px ${FONT}`;
  return measureCtx.measureText(word).width;
}

const SIZED_WORDS = WORDS.map((w) => {
  const fontSize = fontSizeFor(w.frequency);
  return {
    ...w,
    fontSize,
    width: textWidth(w.word, fontSize),
    height: fontSize * 1.15,
  };
}).sort((a, b) => b.frequency - a.frequency);

// --- Archimedean-spiral placement -------------------------------------------
// Biggest word first, spiraling outward until a collision-free box is found.
// The spiral's vertical excursion is scaled by the canvas aspect ratio so the
// cloud fills an ellipse matching the mount shape instead of a bare circle.
const PADDING = 7;

function rectsOverlap(a, b) {
  return !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
}

function layoutWordCloud(words, width, height) {
  const centerX = width / 2;
  const centerY = height / 2;
  const aspect = height / width;
  const angleStep = 0.26;
  const radiusStep = 2.4;
  const placed = [];

  words.forEach((word) => {
    const boxW = word.width + PADDING * 2;
    const boxH = word.height + PADDING * 2;
    let angle = 0;
    let radius = 0;

    for (let step = 0; step < 8000; step += 1) {
      const cx = centerX + radius * Math.cos(angle);
      const cy = centerY + radius * Math.sin(angle) * aspect;
      const rect = {
        left: cx - boxW / 2,
        right: cx + boxW / 2,
        top: cy - boxH / 2,
        bottom: cy + boxH / 2,
      };
      const inBounds = rect.left >= 0 && rect.right <= width && rect.top >= 0 && rect.bottom <= height;
      const collides = placed.some((p) => rectsOverlap(rect, p.rect));
      if (inBounds && !collides) {
        placed.push({ ...word, x: cx, y: cy, rect });
        return;
      }
      angle += angleStep;
      radius += radiusStep * (angleStep / (2 * Math.PI));
    }
    // Spiral saturated (shouldn't happen at this word count/canvas size) —
    // drop the word rather than overlap or throw, keeping layout deterministic.
  });

  return placed;
}

const TITLE_H = 64;
const INSET = 26;
const W = window.ANYPLOT_SIZE.width;
const H = window.ANYPLOT_SIZE.height;
const CLOUD_W = W - INSET * 2;
const CLOUD_H = H - TITLE_H - INSET * 2;
const PLACED_WORDS = layoutWordCloud(SIZED_WORDS, CLOUD_W, CLOUD_H);

// --- Custom marks — plain SVG text drawn inside the MUI X surface ----------
function WordCloudMarks() {
  return (
    <g fontFamily={FONT} fontWeight={600} textAnchor="middle" dominantBaseline="middle">
      {PLACED_WORDS.map((word, i) => (
        <text
          key={word.word}
          x={word.x + INSET}
          y={word.y + INSET}
          fontSize={word.fontSize}
          fill={t.palette[i % t.palette.length]}
        >
          {word.word}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <div
      style={{
        width: W,
        height: H,
        background: t.pageBg,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div style={{ height: TITLE_H, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          wordcloud-basic · javascript · muix · anyplot.ai
        </span>
      </div>
      <ChartContainer
        width={W}
        height={H - TITLE_H}
        series={[]}
        margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
        skipAnimation
      >
        <WordCloudMarks />
      </ChartContainer>
    </div>
  );
}
