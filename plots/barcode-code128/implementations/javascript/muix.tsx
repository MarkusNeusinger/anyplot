// anyplot.ai
// barcode-code128: Code 128 Barcode
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-01
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;

// Constants
// Code 128 symbol patterns (ISO/IEC 15417): PATTERNS[v] is the 11-module bar (1) /
// space (0) pattern of symbol value v; 103-105 are Start A/B/C, 106 is the 13-module Stop.
const PATTERNS = [
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
const CHECK_MODULUS = 103;
const SUBSET_B_OFFSET = 32; // a Subset B symbol value is the ASCII code minus 32
const QUIET_ZONE_MODULES = 10; // ISO/IEC 15417 minimum quiet zone on each side
// A barcode keeps dark bars on a light ground in both themes so it still scans
const LABEL_BG = "#FAF8F1";
const BAR_INK = "#1A1A17";
const MAX_SYMBOL_SHARE = 0.86; // widest share of the canvas the symbol may take
const BAR_HEIGHT_SHARE = 0.5; // bar height as a share of the canvas height

// Data: replace this block with your own parameters
const CONTENT = "SHIP-2024-ABC123"; // role: content

// Plot: reads only the parameters and the constants above
const dataValues = Array.from(CONTENT, (ch) => ch.charCodeAt(0) - SUBSET_B_OFFSET);
const checkValue = dataValues.reduce((sum, v, i) => sum + v * (i + 1), START_B) % CHECK_MODULUS;
const symbolValues = [START_B, ...dataValues, checkValue, STOP];
const quietZone = "0".repeat(QUIET_ZONE_MODULES);
const bits = quietZone + symbolValues.map((v) => String(PATTERNS[v])).join("") + quietZone;
const totalModules = bits.length;

// Run-length segments: each bar or space becomes one stacked series, so every
// width is a whole number of modules exactly as the encoding gives it
const segments: { modules: number; isBar: boolean }[] = [];
for (let i = 0; i < bits.length; ) {
  let j = i;
  while (j < bits.length && bits[j] === bits[i]) j += 1;
  segments.push({ modules: j - i, isBar: bits[i] === "1" });
  i = j;
}

const { width, height } = window.ANYPLOT_SIZE;
// Whole pixels per module keep every bar edge sharp
const modulePx = Math.floor((width * MAX_SYMBOL_SHARE) / totalModules);
const symbolWidth = modulePx * totalModules;
const barHeight = Math.round(height * BAR_HEIGHT_SHARE);

const TITLE = "barcode-code128 · javascript · muix · anyplot.ai";
const caption = `Code 128 Subset B · ${CONTENT.length} data characters · check value ${checkValue} · ${totalModules} modules incl. ${QUIET_ZONE_MODULES}-module quiet zones`;

export default function Chart() {
  return (
    <div
      style={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 28,
        background: t.pageBg,
      }}
    >
      <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
      <div
        style={{
          background: LABEL_BG,
          border: `1px solid ${t.grid}`,
          borderRadius: 6,
          padding: "40px 0 28px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <BarChart
          width={symbolWidth}
          height={barHeight}
          layout="horizontal"
          skipAnimation
          hideLegend
          margin={{ top: 0, bottom: 0, left: 0, right: 0 }}
          xAxis={[{ scaleType: "linear", min: 0, max: totalModules, position: "none" }]}
          yAxis={[{ scaleType: "band", data: [CONTENT], categoryGapRatio: 0, position: "none" }]}
          series={segments.map((seg, i) => ({
            id: `segment-${i}`,
            data: [seg.modules],
            stack: "symbol",
            color: seg.isBar ? BAR_INK : "transparent",
          }))}
          slotProps={{ tooltip: { trigger: "none" } }}
        />
        <div
          style={{
            marginTop: 22,
            fontFamily: "'JetBrains Mono', 'Courier New', monospace",
            fontSize: 30,
            letterSpacing: "0.35em",
            paddingLeft: "0.35em", // balances the spacing after the last character
            color: BAR_INK,
          }}
        >
          {CONTENT}
        </div>
      </div>
      <div style={{ fontSize: 16, color: t.inkSoft }}>{caption}</div>
    </div>
  );
}
