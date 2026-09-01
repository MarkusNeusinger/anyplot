// anyplot.ai
// barcode-ean13: EAN-13 Barcode
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-01

const t = window.ANYPLOT_TOKENS;

// A physical barcode's marks must stay dark-on-light regardless of display
// theme to remain machine-scannable — fixed, not theme-adaptive like chrome.
const BARCODE_INK = "#1A1A17";
const BARCODE_CARD = "#FAF8F1";

// --- EAN-13 encoding tables (GS1 standard) ----------------------------------
const L_CODE = [
  "0001101", "0011001", "0010011", "0111101", "0100011",
  "0110001", "0101111", "0111011", "0110111", "0001011",
];
const G_CODE = [
  "0100111", "0110011", "0011011", "0100001", "0011101",
  "0111001", "0000101", "0010001", "0001001", "0010111",
];
const R_CODE = L_CODE.map((pattern) => pattern.replace(/[01]/g, (bit) => (bit === "0" ? "1" : "0")));
const PARITY_TABLE = [
  "LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
  "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL",
];

function checkDigit(twelveDigits) {
  const sum = twelveDigits.reduce((total, digit, i) => total + digit * (i % 2 === 0 ? 1 : 3), 0);
  return (10 - (sum % 10)) % 10;
}

function encodeEAN13(digits) {
  const parity = PARITY_TABLE[digits[0]];
  const leftDigits = digits.slice(1, 7);
  const rightDigits = digits.slice(7, 13);
  const modules = [1, 0, 1]; // start guard
  leftDigits.forEach((digit, i) => {
    const pattern = parity[i] === "L" ? L_CODE[digit] : G_CODE[digit];
    pattern.split("").forEach((bit) => modules.push(Number(bit)));
  });
  modules.push(0, 1, 0, 1, 0); // center guard
  rightDigits.forEach((digit) => {
    R_CODE[digit].split("").forEach((bit) => modules.push(Number(bit)));
  });
  modules.push(1, 0, 1); // end guard
  return modules;
}

// --- Data: a specialty-tea retail product code ------------------------------
const productCode = [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
const digits = [...productCode, checkDigit(productCode)];
const modules = encodeEAN13(digits);

const START_GUARD = new Set([0, 1, 2]);
const CENTER_GUARD = new Set([45, 46, 47, 48, 49]);
const END_GUARD = new Set([92, 93, 94]);
const DIGIT_HEIGHT = 1.0;
const GUARD_HEIGHT = 1.15;
const MAX_HEIGHT = GUARD_HEIGHT;

const barData = modules.map((bit, i) => {
  const isGuard = START_GUARD.has(i) || CENTER_GUARD.has(i) || END_GUARD.has(i);
  const height = isGuard ? GUARD_HEIGHT : DIGIT_HEIGHT;
  return { x: i, y: bit ? height : 0 };
});
const spacerData = modules.map((bit, i) => {
  const isGuard = START_GUARD.has(i) || CENTER_GUARD.has(i) || END_GUARD.has(i);
  const height = isGuard ? GUARD_HEIGHT : DIGIT_HEIGHT;
  return { x: i, y: bit ? MAX_HEIGHT - height : MAX_HEIGHT };
});

// Human-readable digits: leading digit stands alone in the left quiet zone,
// the remaining 12 digits center under their own 7-module encoding block.
const digitLabels = [{ x: -5, text: String(digits[0]) }];
for (let i = 0; i < 6; i += 1) {
  digitLabels.push({ x: 3 + 7 * i + 3.5, text: String(digits[1 + i]) });
}
for (let j = 0; j < 6; j += 1) {
  digitLabels.push({ x: 50 + 7 * j + 3.5, text: String(digits[7 + j]) });
}

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "column",
    backgroundColor: "transparent",
    plotBackgroundColor: BARCODE_CARD,
    plotBorderWidth: 0,
    plotShadow: false,
    animation: false,
    marginBottom: 90,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "barcode-ean13 · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
    margin: 30,
  },
  xAxis: {
    min: -13,
    max: 106,
    visible: false,
  },
  yAxis: {
    min: 0,
    max: MAX_HEIGHT,
    visible: false,
    reversedStacks: false,
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: {
    column: {
      stacking: "normal",
      pointPadding: 0,
      groupPadding: 0,
      borderWidth: 0,
      pointRange: 1,
      animation: false,
    },
    series: { animation: false, enableMouseTracking: false },
  },
  series: [
    {
      name: "Quiet space",
      type: "column",
      data: spacerData,
      color: "transparent",
      dataLabels: { enabled: false },
    },
    {
      name: "Bars",
      type: "column",
      data: barData,
      color: BARCODE_INK,
      dataLabels: { enabled: false },
    },
    {
      name: "Digits",
      type: "scatter",
      data: digitLabels.map((d) => ({ x: d.x, y: 0, name: d.text })),
      marker: { enabled: false },
      dataLabels: {
        enabled: true,
        format: "{point.name}",
        crop: false,
        overflow: "allow",
        verticalAlign: "bottom",
        y: 34,
        align: "center",
        style: {
          color: t.inkSoft,
          fontSize: "20px",
          fontWeight: "500",
          textOutline: "none",
        },
      },
    },
  ],
});
