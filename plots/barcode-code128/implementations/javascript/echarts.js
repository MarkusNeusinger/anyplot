// anyplot.ai
// barcode-code128: Code 128 Barcode
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-01

const t = window.ANYPLOT_TOKENS;

// --- Code 128 Subset B pattern table -----------------------------------------
// Standard-compliant bar/space module widths for symbol values 0-102 (each sums
// to 11 modules). Used both for character data (value = ASCII code - 32) and for
// looking up the modulo-103 check symbol. Start-B and Stop are fixed patterns.
const PATTERNS = [
  [2,1,2,2,2,2], [2,2,2,1,2,2], [2,2,2,2,2,1], [1,2,1,2,2,3], [1,2,1,3,2,2],
  [1,3,1,2,2,2], [1,2,2,2,1,3], [1,2,2,3,1,2], [1,3,2,2,1,2], [2,2,1,2,1,3],
  [2,2,1,3,1,2], [2,3,1,2,1,2], [1,1,2,2,3,2], [1,2,2,1,3,2], [1,2,2,2,3,1],
  [1,1,3,2,2,2], [1,2,3,1,2,2], [1,2,3,2,2,1], [2,2,3,2,1,1], [2,2,1,1,3,2],
  [2,2,1,2,3,1], [2,1,3,2,1,2], [2,2,3,1,1,2], [3,1,2,1,3,1], [3,1,1,2,2,2],
  [3,2,1,1,2,2], [3,2,1,2,2,1], [3,1,2,2,1,2], [3,2,2,1,1,2], [3,2,2,2,1,1],
  [2,1,2,1,2,3], [2,1,2,3,2,1], [2,3,2,1,2,1], [1,1,1,3,2,3], [1,3,1,1,2,3],
  [1,3,1,3,2,1], [1,1,2,3,1,3], [1,3,2,1,1,3], [1,3,2,3,1,1], [2,1,1,3,1,3],
  [2,3,1,1,1,3], [2,3,1,3,1,1], [1,1,2,1,3,3], [1,1,2,3,3,1], [1,3,2,1,3,1],
  [1,1,3,1,2,3], [1,1,3,3,2,1], [1,3,3,1,2,1], [3,1,3,1,2,1], [2,1,1,3,3,1],
  [2,3,1,1,3,1], [2,1,3,1,1,3], [2,1,3,3,1,1], [2,1,3,1,3,1], [3,1,1,1,2,3],
  [3,1,1,3,2,1], [3,3,1,1,2,1], [3,1,2,1,1,3], [3,1,2,3,1,1], [3,3,2,1,1,1],
  [3,1,4,1,1,1], [2,2,1,4,1,1], [4,3,1,1,1,1], [1,1,1,2,2,4], [1,1,1,4,2,2],
  [1,2,1,1,2,4], [1,2,1,4,2,1], [1,4,1,1,2,2], [1,4,1,2,2,1], [1,1,2,2,1,4],
  [1,1,2,4,1,2], [1,2,2,1,1,4], [1,2,2,4,1,1], [1,4,2,1,1,2], [1,4,2,2,1,1],
  [2,4,1,2,1,1], [2,2,1,1,1,4], [4,1,3,1,1,1], [2,4,1,1,1,2], [1,3,4,1,1,1],
  [1,1,1,2,4,2], [1,2,1,1,4,2], [1,2,1,2,4,1], [1,1,4,2,1,2], [1,2,4,1,1,2],
  [1,2,4,2,1,1], [4,1,1,2,1,2], [4,2,1,1,1,2], [4,2,1,2,1,1], [2,1,2,1,4,1],
  [2,1,4,1,2,1], [4,1,2,1,2,1], [1,1,1,1,4,3], [1,1,1,3,4,1], [1,3,1,1,4,1],
  [1,1,4,1,1,3], [1,1,4,3,1,1], [4,1,1,1,1,3], [4,1,1,3,1,1], [1,1,3,1,4,1],
  [1,1,4,1,3,1], [3,1,1,1,4,1], [4,1,1,1,3,1],
];
const START_B = [2, 1, 1, 4, 1, 2];
const START_B_VALUE = 104;
const STOP = [2, 3, 3, 1, 1, 1, 2];
const QUIET_MODULES = 10; // >=10x per the Code 128 spec's minimum quiet-zone width

// --- Data: a logistics package-tracking label --------------------------------
const content = "PKG-48213-RX";

// --- Encode: Start B + data symbols + check symbol (mod 103) + Stop ----------
const symbolPatterns = [START_B];
let checksum = START_B_VALUE;
for (let i = 0; i < content.length; i++) {
  const value = content.charCodeAt(i) - 32;
  symbolPatterns.push(PATTERNS[value]);
  checksum += value * (i + 1);
}
const checkValue = checksum % 103;
symbolPatterns.push(PATTERNS[checkValue]);
symbolPatterns.push(STOP);

// --- Flatten to a module-width sequence, keep only the drawn bar segments ----
const widths = symbolPatterns.flat();
const bars = [];
let isBar = true;
let pos = QUIET_MODULES;
for (const width of widths) {
  if (isBar) bars.push([pos, width]);
  pos += width;
  isBar = !isBar;
}
const totalModules = pos + QUIET_MODULES;

// --- Layout (1600x900 CSS mount -> 3200x1800 px) ------------------------------
const AREA_LEFT = 220;
const AREA_RIGHT = 220;
const BAR_TOP = 220;
const BAR_BOTTOM_GAP = 280; // grid "bottom" = distance from mount bottom to bar baseline
const barBaselineY = 900 - BAR_BOTTOM_GAP;
const pxPerModule = (1600 - AREA_LEFT - AREA_RIGHT) / totalModules;
const toPx = (moduleValue) => AREA_LEFT + moduleValue * pxPerModule;

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "barcode-code128 · javascript · echarts · anyplot.ai",
    subtext: `Code 128, Subset B  ·  check digit ${checkValue} (mod 103)  ·  ${content.length} data characters`,
    left: "center",
    top: 34,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
    subtextStyle: { color: t.inkSoft, fontSize: 14 },
  },
  grid: {
    left: AREA_LEFT,
    right: AREA_RIGHT,
    top: BAR_TOP,
    bottom: BAR_BOTTOM_GAP,
  },
  xAxis: { type: "value", min: 0, max: totalModules, show: false },
  yAxis: { type: "value", min: 0, max: 1, show: false },
  graphic: [
    {
      type: "text",
      bounding: "raw",
      x: toPx(QUIET_MODULES / 2),
      y: BAR_TOP - 22,
      style: { text: "quiet zone", fill: t.inkSoft, fontSize: 11, fontStyle: "italic", textAlign: "center" },
      z: 40,
    },
    {
      type: "text",
      bounding: "raw",
      x: toPx(totalModules - QUIET_MODULES / 2),
      y: BAR_TOP - 22,
      style: { text: "quiet zone", fill: t.inkSoft, fontSize: 11, fontStyle: "italic", textAlign: "center" },
      z: 40,
    },
    {
      type: "text",
      bounding: "raw",
      x: 800,
      y: barBaselineY + 40,
      style: {
        text: content.split("").join(" "),
        fill: t.ink,
        fontSize: 30,
        fontWeight: "bold",
        fontFamily: "monospace",
        textAlign: "center",
      },
      z: 40,
    },
    {
      type: "text",
      bounding: "raw",
      x: 800,
      y: barBaselineY + 86,
      style: {
        text: "Start B  ·  data  ·  check symbol  ·  Stop",
        fill: t.inkSoft,
        fontSize: 13,
        textAlign: "center",
      },
      z: 40,
    },
  ],
  series: [
    {
      type: "custom",
      clip: true,
      renderItem: (params, api) => {
        const start = api.value(0);
        const width = api.value(1);
        const topLeft = api.coord([start, 1]);
        const bottomRight = api.coord([start + width, 0]);
        return {
          type: "rect",
          shape: {
            x: topLeft[0],
            y: topLeft[1],
            width: bottomRight[0] - topLeft[0],
            height: bottomRight[1] - topLeft[1],
          },
          style: { fill: t.ink },
        };
      },
      data: bars,
    },
  ],
});
