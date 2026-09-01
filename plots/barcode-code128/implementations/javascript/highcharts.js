// anyplot.ai
// barcode-code128: Code 128 Barcode
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 77/100 | Created: 2026-09-01

const t = window.ANYPLOT_TOKENS;

// --- Code 128 encoding (Subset B, modulo-103 check digit) ------------------
// Element-width table: 6 digits (bar,space,bar,space,bar,space) per symbol
// value 0-102, plus Start A/B/C (103/104/105) and Stop (106, 7-digit
// bar-space-bar-space-bar-space-bar). Digits are module counts (1-4 units).
const CODE128_WIDTHS = [
  "212222", "222122", "222221", "121223", "121322", "131222", "122213",
  "122312", "132212", "221213", "221312", "231212", "112232", "122132",
  "122231", "113222", "123122", "123221", "223211", "221132", "221231",
  "213212", "223112", "312131", "311222", "321122", "321221", "312212",
  "322112", "322211", "212123", "212321", "232121", "111323", "131123",
  "131321", "112313", "132113", "132311", "211313", "231113", "231311",
  "112133", "112331", "132131", "113123", "113321", "133121", "313121",
  "211331", "231131", "213113", "213311", "213131", "311123", "311321",
  "331121", "312113", "312311", "332111", "314111", "221411", "431111",
  "111224", "111422", "121124", "121421", "141122", "141221", "112214",
  "112412", "122114", "122411", "142112", "142211", "241211", "221114",
  "413111", "241112", "134111", "111242", "121142", "121241", "114212",
  "124112", "124211", "411212", "421112", "421211", "212141", "214121",
  "412121", "111143", "111341", "131141", "114113", "114311", "411113",
  "411311", "113141", "114131", "311141", "411131", "211412", "211214",
  "211232", "2331112",
];
const START_B = 104;
const STOP = 106;

// The barcode itself is encoded *data*, not chrome: it must stay high-contrast
// black-on-white in both themes for scan reliability, so these are fixed
// literals rather than theme tokens (only the title/label chrome uses t.ink).
const BARCODE_INK = "#1A1A17";
const BARCODE_BG = "#FAF8F1";

const content = "SHIP-2024-ABC123";

// Subset B maps printable ASCII 32-126 to symbol values 0-94.
const values = content.split("").map((c) => c.charCodeAt(0) - 32);
const checkDigit =
  (START_B + values.reduce((sum, v, i) => sum + v * (i + 1), 0)) % 103;
const symbolValues = [START_B, ...values, checkDigit, STOP];

// Expand each symbol's width digits into 1-unit modules (1 = bar, 0 = space).
// Every pattern both starts and ends its digit count so that the alternation
// carries over cleanly into the next symbol's bar.
const modules = [];
symbolValues.forEach((value) => {
  let isBar = true;
  for (const digit of CODE128_WIDTHS[value]) {
    for (let i = 0; i < Number(digit); i++) modules.push(isBar ? 1 : 0);
    isBar = !isBar;
  }
});

// --- Chart -------------------------------------------------------------
const QUIET_ZONE = 10; // blank modules either side — Code 128 requires >=10x
const barData = modules.map((bit, i) => ({
  x: i,
  y: 1,
  color: bit ? BARCODE_INK : "transparent",
}));

Highcharts.chart("container", {
  chart: {
    type: "column",
    backgroundColor: "transparent",
    plotBackgroundColor: BARCODE_BG,
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "barcode-code128 · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    min: -QUIET_ZONE,
    max: modules.length - 1 + QUIET_ZONE,
    lineWidth: 0,
    tickLength: 0,
    labels: { enabled: false },
    title: {
      text: content,
      style: {
        color: t.ink,
        fontSize: "20px",
        fontFamily: "monospace",
        letterSpacing: "4px",
      },
      margin: 30,
    },
  },
  yAxis: {
    min: 0,
    max: 1,
    gridLineWidth: 0,
    lineWidth: 0,
    tickLength: 0,
    labels: { enabled: false },
    title: { text: null },
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: {
    column: {
      pointPadding: 0,
      groupPadding: 0,
      borderWidth: 0,
      borderRadius: 0,
      pointRange: 1,
    },
    series: { animation: false },
  },
  series: [{ name: "Code 128 modules", data: barData }],
});
