// anyplot.ai
// barcode-ean13: EAN-13 Barcode
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-01
import { BarChart } from "@mui/x-charts/BarChart";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// --- EAN-13 encoding tables --------------------------------------------------
// L-code is canonical; the right-hand R-code is its bitwise complement, and the
// even-parity G-code is the reverse of R (standard EAN-13/UPC-A relationships).
const L_CODE = [
  "0001101", "0011001", "0010011", "0111101", "0100011",
  "0110001", "0101111", "0111011", "0110111", "0001011",
];
const PARITY = [
  "LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
  "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL",
];
const complement = (bits) => bits.split("").map((b) => (b === "1" ? "0" : "1")).join("");
const reverse = (bits) => bits.split("").reverse().join("");
const R_CODE = L_CODE.map(complement);
const G_CODE = R_CODE.map(reverse);

const checkDigit = (twelveDigits) => {
  const sum = twelveDigits.reduce((acc, d, i) => acc + d * (i % 2 === 0 ? 1 : 3), 0);
  return (10 - (sum % 10)) % 10;
};

// --- Data: a 12-digit product code (Polish EAN prefix); check digit computed ---
const twelveDigits = "590123412345".split("").map(Number);
const digits = [...twelveDigits, checkDigit(twelveDigits)];

// --- Encode modules: 9 quiet + 3 start + 42 left + 5 center + 42 right + 3 end + 9 quiet = 113 ---
const QUIET_ZONE = 9;
const START_GUARD = "101";
const CENTER_GUARD = "01010";
const END_GUARD = "101";

const parity = PARITY[digits[0]];
const leftBits = digits
  .slice(1, 7)
  .map((d, i) => (parity[i] === "L" ? L_CODE[d] : G_CODE[d]))
  .join("");
const rightBits = digits
  .slice(7, 13)
  .map((d) => R_CODE[d])
  .join("");

const bars =
  "0".repeat(QUIET_ZONE) + START_GUARD + leftBits + CENTER_GUARD + rightBits + END_GUARD + "0".repeat(QUIET_ZONE);
const modules = bars.split("").map(Number);
const moduleIndex = modules.map((_, i) => i);

// --- Digit label placement: centered under each digit's 7-module block; the ---
// --- first digit has no bars of its own and sits centered in the left quiet zone. ---
const leftStart = QUIET_ZONE + START_GUARD.length;
const rightStart = leftStart + 6 * 7 + CENTER_GUARD.length;
const digitCenters = [
  Math.floor(QUIET_ZONE / 2),
  ...Array.from({ length: 6 }, (_, i) => leftStart + i * 7 + 3),
  ...Array.from({ length: 6 }, (_, i) => rightStart + i * 7 + 3),
];
const digitAtCenter = new Map(digitCenters.map((moduleIdx, i) => [moduleIdx, String(digits[i])]));

const TITLE = "barcode-ean13 · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 90;

// Bars render in the theme's ink color rather than the Imprint brand green — a
// scannable barcode reads as dark-on-light / light-on-dark bars, the same
// real-world-fidelity exception the style guide grants grass=green or blood=red.
export default function Chart() {
  return (
    <Box sx={{ width: SIZE.width, height: SIZE.height, display: "flex", flexDirection: "column" }}>
      <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 500, textAlign: "center", pt: 2, height: TITLE_HEIGHT }}>
        {TITLE}
      </Typography>
      <BarChart
        width={SIZE.width}
        height={SIZE.height - TITLE_HEIGHT}
        series={[{ data: modules, color: t.ink }]}
        xAxis={[
          {
            scaleType: "band",
            data: moduleIndex,
            categoryGapRatio: 0,
            barGapRatio: 0,
            disableLine: true,
            disableTicks: true,
            tickLabelInterval: (value) => digitAtCenter.has(value),
            valueFormatter: (value) => digitAtCenter.get(value) ?? "",
            tickLabelStyle: { fontSize: 22, fontFamily: "monospace", fontWeight: 700 },
          },
        ]}
        leftAxis={null}
        margin={{ top: 16, right: 24, bottom: 56, left: 24 }}
        slotProps={{ legend: { hidden: true } }}
        skipAnimation
      />
    </Box>
  );
}
