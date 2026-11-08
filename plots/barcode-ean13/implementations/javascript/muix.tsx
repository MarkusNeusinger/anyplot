// anyplot.ai
// barcode-ean13: EAN-13 Barcode
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-01
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// EAN-13 digit patterns: the L-code is canonical, the R-code is its bitwise
// complement and the even-parity G-code is the R-code reversed
const L_CODE = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"];
const R_CODE = L_CODE.map((bits) => Array.from(bits, (b) => (b === "1" ? "0" : "1")).join(""));
const G_CODE = R_CODE.map((bits) => Array.from(bits).reverse().join(""));
// The leading digit is not drawn as bars: it sets the L/G parity of the left group
const PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"];
const START_GUARD = "101";
const CENTER_GUARD = "01010";
const END_GUARD = "101";
const DIGITS_PER_HALF = 6;
const QUIET_ZONE_MODULES = 9; // minimum quiet zone on each side
// A barcode keeps dark bars on a light ground in both themes so it still scans
const LABEL_BG = "#FAF8F1";
const BAR_INK = "#1A1A17";
const DIGIT_BAR_SHARE = 0.9; // digit bars end here; guard bars run on to 1, between the digit groups
const MAX_SYMBOL_SHARE = 0.6; // widest share of the canvas the symbol may take
const BAR_HEIGHT_SHARE = 0.6; // guard bar length as a share of the canvas height
const DIGIT_FONT = 32;

// Data: replace this block with your own parameters
const CODE = "590123412345"; // role: code

// Plot: reads only the parameters and the constants above
// The check digit is computed from the first 12 digits (weights 1, 3, 1, 3, ...)
const payload = Array.from(CODE.slice(0, 2 * DIGITS_PER_HALF), Number);
const weightedSum = payload.reduce((sum, d, i) => sum + d * (i % 2 === 0 ? 1 : 3), 0);
const checkDigit = (10 - (weightedSum % 10)) % 10;
const digits = [...payload, checkDigit];
const parity = PARITY[digits[0]];
const leftDigits = digits.slice(1, 1 + DIGITS_PER_HALF);
const rightDigits = digits.slice(1 + DIGITS_PER_HALF);
const leftBits = leftDigits.map((d, i) => (parity[i] === "L" ? L_CODE[d] : G_CODE[d])).join("");
const rightBits = rightDigits.map((d) => R_CODE[d]).join("");

const quietZone = "0".repeat(QUIET_ZONE_MODULES);
const parts = [
  { bits: quietZone, guard: false },
  { bits: START_GUARD, guard: true },
  { bits: leftBits, guard: false },
  { bits: CENTER_GUARD, guard: true },
  { bits: rightBits, guard: false },
  { bits: END_GUARD, guard: true },
  { bits: quietZone, guard: false },
];
const modules = parts.flatMap((p) => Array.from(p.bits, (b) => ({ bar: b === "1", guard: p.guard })));
const moduleIndex = modules.map((_, i) => i);
const totalModules = modules.length;

// Human-readable digits in module units: the leading digit centred in the left
// quiet zone, every other digit centred under its own 7-module pattern
const digitWidth = L_CODE[0].length;
const leftStart = QUIET_ZONE_MODULES + START_GUARD.length;
const rightStart = leftStart + leftBits.length + CENTER_GUARD.length;
const digitSlots = [
  { digit: digits[0], center: QUIET_ZONE_MODULES / 2 },
  ...leftDigits.map((digit, i) => ({ digit, center: leftStart + (i + 0.5) * digitWidth })),
  ...rightDigits.map((digit, i) => ({ digit, center: rightStart + (i + 0.5) * digitWidth })),
];

const { width, height } = window.ANYPLOT_SIZE;
// Whole pixels per module keep every bar edge sharp
const modulePx = Math.floor((width * MAX_SYMBOL_SHARE) / totalModules);
const symbolWidth = modulePx * totalModules;
const barHeight = Math.round(height * BAR_HEIGHT_SHARE);

const TITLE = "barcode-ean13 · javascript · muix · anyplot.ai";
const caption = `EAN-13 ${digits.join("")} · check digit ${checkDigit} · left-half parity ${parity} set by leading digit ${digits[0]} · ${totalModules} modules incl. ${QUIET_ZONE_MODULES}-module quiet zones`;

function DigitLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  const x0 = xScale(moduleIndex[0]);
  const band = xScale.bandwidth();
  return (
    <g>
      {digitSlots.map((slot, i) => (
        <text
          key={i}
          x={x0 + slot.center * band}
          y={yScale(1)}
          textAnchor="middle"
          fontSize={DIGIT_FONT}
          fontFamily="'JetBrains Mono', 'Courier New', monospace"
          fill={BAR_INK}
        >
          {slot.digit}
        </text>
      ))}
    </g>
  );
}

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
          padding: "40px 0 30px",
        }}
      >
        <ChartsContainer
          width={symbolWidth}
          height={barHeight}
          skipAnimation
          margin={{ top: 0, bottom: 0, left: 0, right: 0 }}
          xAxis={[{ scaleType: "band", data: moduleIndex, categoryGapRatio: 0, position: "none" }]}
          yAxis={[{ min: 0, max: 1, reverse: true, position: "none" }]}
          series={[
            {
              type: "bar",
              id: "digit-bars",
              stack: "symbol",
              color: BAR_INK,
              data: modules.map((m) => (m.bar && !m.guard ? DIGIT_BAR_SHARE : 0)),
            },
            {
              type: "bar",
              id: "guard-bars",
              stack: "symbol",
              color: BAR_INK,
              data: modules.map((m) => (m.bar && m.guard ? 1 : 0)),
            },
          ]}
        >
          <BarPlot skipAnimation />
          <DigitLabels />
        </ChartsContainer>
      </div>
      <div style={{ fontSize: 16, color: t.inkSoft }}>{caption}</div>
    </div>
  );
}
