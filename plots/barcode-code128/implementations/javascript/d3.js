// anyplot.ai
// barcode-code128: Code 128 Barcode
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-01

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Code 128 Subset B symbol table -----------------------------------------
// Module-width patterns (bar,space,bar,space,bar,space) for symbol values
// 0-102, plus Start A/B/C (103/104/105) and Stop (106). Subset B maps ASCII
// 32-127 to values 0-95 via value = charCode - 32.
const CODE128_B = [
  "212222", "222122", "222221", "121223", "121322",
  "131222", "122213", "122312", "132212", "221213",
  "221312", "231212", "112232", "122132", "122231",
  "113222", "123122", "123221", "223211", "221132",
  "221231", "213212", "223112", "312131", "311222",
  "321122", "321221", "312212", "322112", "322211",
  "212123", "212321", "232121", "111323", "131123",
  "131321", "112313", "132113", "132311", "211313",
  "231113", "231311", "112133", "112331", "132131",
  "113123", "113321", "133121", "313121", "211331",
  "231131", "213113", "213311", "213131", "311123",
  "311321", "331121", "312113", "312311", "332111",
  "314111", "221411", "431111", "111224", "111422",
  "121124", "121421", "141122", "141221", "112214",
  "112412", "122114", "122411", "142112", "142211",
  "241211", "221114", "413111", "241112", "134111",
  "111242", "121142", "121241", "114212", "124112",
  "124211", "411212", "421112", "421211", "212141",
  "214121", "412121", "111143", "111341", "131141",
  "114113", "114311", "411113", "411311", "113141",
  "114131", "311141", "411131", "211412", "211214",
  "211232", "2331112",
].map((pattern) => pattern.split("").map(Number));

const START_B = 104;
const STOP = 106;

// --- Data: encode a shipping-label style payload with Code Set B -----------
const content = "SHIP-2024-ABC123";
const dataValues = Array.from(content).map((ch) => ch.charCodeAt(0) - 32);

let checksum = START_B;
dataValues.forEach((value, i) => {
  checksum += value * (i + 1);
});
checksum %= 103;

const symbolValues = [START_B, ...dataValues, checksum, STOP];

// Flatten symbols into a sequence of bar/space elements (bar first, alternating)
const elements = symbolValues.flatMap((symbol) =>
  CODE128_B[symbol].map((moduleWidth, i) => ({ moduleWidth, dark: i % 2 === 0 }))
);

// --- Layout ------------------------------------------------------------------
const QUIET_MODULES = 10; // minimum quiet zone per Code 128 spec, each side
const totalModules = elements.reduce((sum, e) => sum + e.moduleWidth, 0) + QUIET_MODULES * 2;

const marginX = 100;
const moduleSize = Math.floor((width - marginX * 2) / totalModules);
const barcodeWidth = moduleSize * totalModules;
const barcodeX = (width - barcodeWidth) / 2;

// Shifted down from the top so the whitespace above the barcode block
// balances the whitespace below the caption (see review feedback).
const barTop = 242;
const barHeight = 380;

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Bars ---------------------------------------------------------------------
// Bars use theme-adaptive ink (rather than a fixed data color) — the bar
// pattern IS the encoded content, not a categorical series, so it follows
// chrome contrast rules: dark ink on the light surface, light ink on the
// dark surface, always maximally contrasted against the page background.
// Module position (in module units, not pixels) maps to pixel-x through an
// idiomatic D3 linear scale, rather than accumulating raw pixel offsets.
const moduleScale = d3.scaleLinear().domain([0, totalModules]).range([barcodeX, barcodeX + barcodeWidth]);

let modulePos = QUIET_MODULES;
const bars = [];
for (const el of elements) {
  if (el.dark) {
    bars.push({
      x: moduleScale(modulePos),
      w: moduleScale(modulePos + el.moduleWidth) - moduleScale(modulePos),
    });
  }
  modulePos += el.moduleWidth;
}

svg.selectAll("rect.bar").data(bars).join("rect")
  .attr("class", "bar")
  .attr("x", (d) => d.x)
  .attr("y", barTop)
  .attr("width", (d) => d.w)
  .attr("height", barHeight)
  .attr("fill", t.ink);

// --- Human-readable text below the barcode -------------------------------
svg.append("text")
  .attr("x", width / 2)
  .attr("y", barTop + barHeight + 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-family", "monospace")
  .style("font-size", "34px")
  .style("font-weight", "600")
  .style("letter-spacing", "6px")
  .text(content);

// --- Caption: encoding metadata ------------------------------------------
svg.append("text")
  .attr("x", width / 2)
  .attr("y", barTop + barHeight + 96)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "20px")
  .text(
    `Code Set B · ${content.length} characters · check digit ${checksum} (mod 103) · ${symbolValues.length} symbols`
  );

// --- Title ---------------------------------------------------------------
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("barcode-code128 · javascript · d3 · anyplot.ai");
