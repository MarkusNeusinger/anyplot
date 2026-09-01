// anyplot.ai
// barcode-ean13: EAN-13 Barcode
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-01

const t = window.ANYPLOT_TOKENS;
const W = window.ANYPLOT_SIZE.width;
const H = window.ANYPLOT_SIZE.height;

// --- EAN-13 encoding tables --------------------------------------------------
const L_CODE = [
  "0001101", "0011001", "0010011", "0111101", "0100011",
  "0110001", "0101111", "0111011", "0110111", "0001011",
];
const G_CODE = [
  "0100111", "0110011", "0011011", "0100001", "0011101",
  "0111001", "0000101", "0010001", "0001001", "0010111",
];
const R_CODE = L_CODE.map((code) => code.replace(/./g, (b) => (b === "0" ? "1" : "0")));
const FIRST_DIGIT_PARITY = [
  "LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
  "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL",
];

// digits[0..11] = manufacturer-side base digits; the 13th (check) digit is derived
function checkDigit(digits) {
  const sum = digits.reduce((acc, d, i) => acc + d * (i % 2 === 0 ? 1 : 3), 0);
  return (10 - (sum % 10)) % 10;
}

function encodeEan13(baseDigits) {
  const digits = baseDigits.concat(checkDigit(baseDigits));
  const first = digits[0];
  const left = digits.slice(1, 7);
  const right = digits.slice(7, 13);
  const parity = FIRST_DIGIT_PARITY[first];
  const leftBits = left.map((d, i) => (parity[i] === "L" ? L_CODE[d] : G_CODE[d])).join("");
  const rightBits = right.map((d) => R_CODE[d]).join("");
  const bits = "101" + leftBits + "01010" + rightBits + "101";
  return { digits, bits };
}

// --- Data (in-memory, deterministic) -----------------------------------------
// 5901234123457 — Polish specialty-coffee product code (12 base digits + computed check digit)
const { digits, bits } = encodeEan13([5, 9, 0, 1, 2, 3, 4, 1, 2, 3, 4, 5]);
const firstDigit = digits[0];
const leftDigits = digits.slice(1, 7);
const rightDigits = digits.slice(7, 13);

// --- Layout -------------------------------------------------------------------
const QUIET = 9; // quiet-zone modules on each side (spec minimum)
const MODULE_W = 12;
const DIGIT_BAR_H = 380;
const GUARD_BAR_H = DIGIT_BAR_H + 50;
const PAD = 50;
const TEXT_GAP = 20;
const TEXT_H = 56;

const cardW = PAD * 2 + (QUIET * 2 + bits.length) * MODULE_W;
const cardH = PAD * 2 + GUARD_BAR_H + TEXT_GAP + TEXT_H;
const titleArea = 130;
const cardX = (W - cardW) / 2;
const cardY = titleArea + (H - titleArea - cardH) / 2;
const barsTop = cardY + PAD;
const barsLeft = cardX + PAD;
const textY = barsTop + GUARD_BAR_H + TEXT_GAP;

// Real barcodes stay black-on-white regardless of site theme — a scanner reads
// contrast, not brand chrome — so the label card and its bars use fixed paper
// colors while the surrounding page and title stay theme-adaptive.
const LABEL_BG = "#FDFCF5";
const LABEL_BORDER = t.inkSoft;
const BAR_COLOR = "#1A1A17";

// Guard-bar module ranges (start, center, end) render taller than digit bars
function isGuardModule(idx) {
  return idx < 3 || (idx >= 45 && idx < 50) || idx >= 92;
}

// Collapse the module bit-string into contiguous black bars (runs of "1")
function buildBars(bitString) {
  const bars = [];
  let runStart = -1;
  for (let idx = 0; idx <= bitString.length; idx += 1) {
    const on = bitString[idx] === "1";
    if (on && runStart === -1) runStart = idx;
    if (!on && runStart !== -1) {
      bars.push({ start: runStart, width: idx - runStart, tall: isGuardModule(runStart) });
      runStart = -1;
    }
  }
  return bars;
}

const barRects = buildBars(bits).map((bar) => ({
  type: "rect",
  shape: {
    x: barsLeft + (QUIET + bar.start) * MODULE_W,
    y: barsTop,
    width: bar.width * MODULE_W,
    height: bar.tall ? GUARD_BAR_H : DIGIT_BAR_H,
  },
  style: { fill: BAR_COLOR },
}));

function digitText(x, text) {
  return {
    type: "text",
    x,
    y: textY,
    style: {
      text,
      fill: BAR_COLOR,
      fontSize: 32,
      fontFamily: "Menlo, Consolas, monospace",
      textAlign: "center",
      textVerticalAlign: "top",
    },
  };
}

const digitTexts = [
  digitText(barsLeft + (QUIET / 2) * MODULE_W, String(firstDigit)),
  ...leftDigits.map((d, i) =>
    digitText(barsLeft + (QUIET + 3 + i * 7 + 3.5) * MODULE_W, String(d))
  ),
  ...rightDigits.map((d, i) =>
    digitText(barsLeft + (QUIET + 50 + i * 7 + 3.5) * MODULE_W, String(d))
  ),
];

// --- Init -----------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
const title = "Specialty Coffee Beans 250g · barcode-ean13 · javascript · echarts · anyplot.ai";
const titleFontSize = Math.max(15, Math.round(22 * Math.min(1, 67 / title.length)));

const gtin = digits.join("");

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  tooltip: {},
  title: {
    text: title,
    left: "center",
    top: 40,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  graphic: {
    elements: [
      {
        type: "rect",
        shape: { x: cardX, y: cardY, width: cardW, height: cardH, r: 6 },
        style: { fill: LABEL_BG, stroke: LABEL_BORDER, lineWidth: 1.5, shadowBlur: 18, shadowColor: "rgba(0,0,0,0.18)", shadowOffsetY: 6 },
        // Graphic elements can carry their own tooltip config (ECharts-specific,
        // not a generic canvas capability); hover over the card to reveal the
        // GTIN this barcode encodes — purely an interactive-HTML affordance,
        // invisible to the static screenshot.
        tooltip: { show: true, formatter: `GTIN: ${gtin}` },
      },
      ...barRects,
      ...digitTexts,
    ],
  },
});
