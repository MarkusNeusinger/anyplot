// anyplot.ai
// barcode-code128: Code 128 Barcode
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-01
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// --- Code 128 Subset B encoder (real ISO/IEC 15417 tables, not a mockup) ----
// BARS[v] is the real 11-module (13 for STOP) bar/space pattern for symbol
// value v, encoded as a string of 1s (bar) and 0s (space) — the canonical
// Code 128 symbol table. Index 103/104/105 are Start A/B/C, 106 is Stop.
const BARS = [
  11011001100, 11001101100, 11001100110, 10010011000, 10010001100, 10001001100, 10011001000, 10011000100,
  10001100100, 11001001000, 11001000100, 11000100100, 10110011100, 10011011100, 10011001110, 10111001100,
  10011101100, 10011100110, 11001110010, 11001011100, 11001001110, 11011100100, 11001110100, 11101101110,
  11101001100, 11100101100, 11100100110, 11101100100, 11100110100, 11100110010, 11011011000, 11011000110,
  11000110110, 10100011000, 10001011000, 10001000110, 10110001000, 10001101000, 10001100010, 11010001000,
  11000101000, 11000100010, 10110111000, 10110001110, 10001101110, 10111011000, 10111000110, 10001110110,
  11101110110, 11010001110, 11000101110, 11011101000, 11011100010, 11011101110, 11101011000, 11101000110,
  11100010110, 11101101000, 11101100010, 11100011010, 11101111010, 11001000010, 11110001010, 10100110000,
  10100001100, 10010110000, 10010000110, 10000101100, 10000100110, 10110010000, 10110000100, 10011010000,
  10011000010, 10000110100, 10000110010, 11000010010, 11001010000, 11110111010, 11000010100, 10001111010,
  10100111100, 10010111100, 10010011110, 10111100100, 10011110100, 10011110010, 11110100100, 11110010100,
  11110010010, 11011011110, 11011110110, 11110110110, 10101111000, 10100011110, 10001011110, 10111101000,
  10111100010, 11110101000, 11110100010, 10111011110, 10111101110, 11101011110, 11110101110, 11010000100,
  11010010000, 11010011100, 1100011101011,
];
const START_B = 104;
const STOP = 106;
const QUIET_ZONE_MODULES = 10; // ANSI/ISO minimum quiet zone: 10x module width

// Shipping-label content (Subset B: full ASCII 32-126, no subset switching needed).
const CONTENT = "SHIP-2024-ABC123";

const dataValues = Array.from(CONTENT, (ch) => ch.charCodeAt(0) - 32);
const checksum = dataValues.reduce((sum, v, i) => sum + v * (i + 1), START_B) % 103;
const symbolValues = [START_B, ...dataValues, checksum, STOP];

const moduleBits = symbolValues.map((v) => String(BARS[v])).join("");
const fullBits = "0".repeat(QUIET_ZONE_MODULES) + moduleBits + "0".repeat(QUIET_ZONE_MODULES);
const TOTAL_MODULES = fullBits.length;

// Run-length encode into bar/space segments — each becomes one stacked series
// so the chart draws the exact variable-width pattern, not an approximation.
const segments = [];
for (let i = 0; i < fullBits.length; ) {
  let j = i;
  while (j < fullBits.length && fullBits[j] === fullBits[i]) j++;
  segments.push({ width: j - i, isBar: fullBits[i] === "1" });
  i = j;
}

// --- Title chrome ------------------------------------------------------------
const TITLE = "barcode-code128 · javascript · muix · anyplot.ai";
const TITLE_FONT_DEFAULT = 22;
const titleFontSize =
  TITLE.length > 67 ? Math.round(TITLE_FONT_DEFAULT * (67 / TITLE.length)) : TITLE_FONT_DEFAULT;

// --- Layout constants (CSS px within the mount's coordinate space) ---------
const PADDING = 60;
const TITLE_H = 50;
const LABEL_H = 56;
const CAPTION_H = 28;
const GAP = 24;

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const chartHeight = SIZE.height - PADDING * 2 - TITLE_H - LABEL_H - CAPTION_H - GAP;
  const chartWidth = SIZE.width - PADDING * 2;

  return (
    <div
      style={{
        width: SIZE.width,
        height: SIZE.height,
        padding: PADDING,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div style={{ height: TITLE_H, fontSize: titleFontSize, fontWeight: 500, color: t.ink }}>{TITLE}</div>
      <div style={{ height: GAP }} />
      <BarChart
        width={chartWidth}
        height={chartHeight}
        layout="horizontal"
        series={segments.map((seg) => ({
          data: [seg.width],
          stack: "barcode",
          // Bars behave like structural ink (a rendered glyph), not a
          // categorical series, so they take the theme-adaptive ink token
          // rather than the brand-green Imprint position — the module
          // widths themselves stay geometrically exact to real Code 128,
          // so the pattern would still scan if printed true black-on-white.
          color: seg.isBar ? t.ink : "transparent",
        }))}
        xAxis={[{ scaleType: "linear", min: 0, max: TOTAL_MODULES }]}
        yAxis={[{ scaleType: "band", data: ["code128"], categoryGapRatio: 0 }]}
        margin={{ top: 0, bottom: 0, left: 0, right: 0 }}
        bottomAxis={null}
        leftAxis={null}
        slotProps={{ legend: { hidden: true } }}
        tooltip={{ trigger: "none" }}
        skipAnimation
      />
      <div style={{ height: GAP }} />
      <div
        style={{
          height: LABEL_H,
          textAlign: "center",
          fontFamily: "'Courier New', monospace",
          fontSize: 26,
          letterSpacing: "0.35em",
          color: t.ink,
        }}
      >
        {CONTENT}
      </div>
      <div style={{ height: CAPTION_H, textAlign: "center", fontSize: 14, color: t.inkSoft }}>
        Code 128 · Subset B (full ASCII, ANSI/ISO quiet zones)
      </div>
    </div>
  );
}
