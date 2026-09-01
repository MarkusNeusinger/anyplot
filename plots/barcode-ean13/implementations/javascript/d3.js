// anyplot.ai
// barcode-ean13: EAN-13 Barcode
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-01

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- EAN-13 encoding tables --------------------------------------------------
// Left-hand digit patterns: "L" (odd parity) and "G" (even parity), 7 modules each.
const L_CODE = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"];
const G_CODE = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"];
const R_CODE = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"];
// Parity pattern (L/G) for the 6 left digits, selected by the leading digit.
const PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"];

// --- Data: a 12-digit product code, check digit auto-calculated -------------
const productCode = "590123412345";
const digits = productCode.split("").map(Number);
const checksum = (10 - digits.reduce((sum, d, i) => sum + d * (i % 2 === 0 ? 1 : 3), 0) % 10) % 10;
const code = digits.concat(checksum);

const leftDigits = code.slice(1, 7);
const rightDigits = code.slice(7, 13);
const parity = PARITY[code[0]];
const leftBits = leftDigits.map((d, i) => (parity[i] === "L" ? L_CODE[d] : G_CODE[d])).join("");
const rightBits = rightDigits.map((d) => R_CODE[d]).join("");

const QUIET = 9;
const bits = "0".repeat(QUIET) + "101" + leftBits + "01010" + rightBits + "101" + "0".repeat(QUIET);
const START_GUARD = [QUIET, QUIET + 2];
const CENTER_GUARD = [QUIET + 45, QUIET + 49];
const END_GUARD = [QUIET + 92, QUIET + 94];
const inGuard = (i) => (i >= START_GUARD[0] && i <= START_GUARD[1]) || (i >= CENTER_GUARD[0] && i <= CENTER_GUARD[1]) || (i >= END_GUARD[0] && i <= END_GUARD[1]);

// A physical barcode must stay dark-ink-on-light-background to remain
// scannable regardless of the page's light/dark theme — only the
// surrounding chrome (title) is allowed to flip with ANYPLOT_THEME.
const BARCODE_BG = "#FAF8F1";
const BARCODE_BORDER = "#D9D4C3";
const BARCODE_INK = "#1A1A17";

// --- Layout -------------------------------------------------------------------
const moduleWidth = 11;
const barcodeWidth = bits.length * moduleWidth;
const startX = (width - barcodeWidth) / 2;
const digitBarHeight = 420;
const guardBarHeight = digitBarHeight + 40;
const barsTopY = 260;

const cardPad = 60;
const cardTop = barsTopY - 50;
const textY = barsTopY + guardBarHeight + 50;
const cardBottom = textY + 40;

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// Label card — barcodes read as printed labels, so an elevated card grounds
// it; the card stays fixed light regardless of theme (see BARCODE_* above).
svg.append("rect")
  .attr("x", startX - cardPad).attr("y", cardTop)
  .attr("width", barcodeWidth + cardPad * 2).attr("height", cardBottom - cardTop)
  .attr("rx", 24)
  .attr("fill", BARCODE_BG)
  .attr("stroke", BARCODE_BORDER)
  .attr("stroke-width", 1.5);

// Bars — one rect per "1" module, bound via a data-join with a linear scale
// mapping module index to pixel offset; guard bars extend further down as
// sync marks.
const moduleX = d3.scaleLinear().domain([0, bits.length]).range([0, barcodeWidth]);
const moduleW = moduleX(1) - moduleX(0);
const barData = [...bits]
  .map((bit, i) => ({ bit, i, guard: inGuard(i) }))
  .filter((d) => d.bit === "1");

svg.append("g")
  .selectAll("rect")
  .data(barData)
  .join("rect")
  .attr("x", (d) => startX + moduleX(d.i))
  .attr("y", barsTopY)
  .attr("width", moduleW)
  .attr("height", (d) => (d.guard ? guardBarHeight : digitBarHeight))
  .attr("fill", BARCODE_INK);

// Human-readable digits — leading digit sits left of the start guard; the two
// six-digit groups center under their own encoded region.
const digitFont = { fontFamily: "ui-monospace, 'SFMono-Regular', Menlo, monospace", fontSize: "30px", fill: BARCODE_INK };

svg.append("text")
  .attr("x", startX + (START_GUARD[0] - 1) * moduleWidth).attr("y", textY)
  .attr("text-anchor", "end")
  .style("font-family", digitFont.fontFamily).style("font-size", digitFont.fontSize).attr("fill", digitFont.fill)
  .text(code[0]);

svg.append("text")
  .attr("x", startX + (START_GUARD[1] + 1 + CENTER_GUARD[0] - 1) / 2 * moduleWidth).attr("y", textY)
  .attr("text-anchor", "middle")
  .style("font-family", digitFont.fontFamily).style("font-size", digitFont.fontSize).attr("fill", digitFont.fill)
  .style("letter-spacing", "6px")
  .text(leftDigits.join(""));

svg.append("text")
  .attr("x", startX + (CENTER_GUARD[1] + 1 + END_GUARD[0] - 1) / 2 * moduleWidth).attr("y", textY)
  .attr("text-anchor", "middle")
  .style("font-family", digitFont.fontFamily).style("font-size", digitFont.fontSize).attr("fill", digitFont.fill)
  .style("letter-spacing", "6px")
  .text(rightDigits.join(""));

// Title
svg.append("text").attr("x", width / 2).attr("y", 64).attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "26px").style("font-weight", "600")
  .text("barcode-ean13 · javascript · d3 · anyplot.ai");
