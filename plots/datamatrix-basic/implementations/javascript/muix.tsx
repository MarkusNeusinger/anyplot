// anyplot.ai
// datamatrix-basic: Basic Data Matrix 2D Barcode
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 79/100 | Updated: 2026-10-23
//# anyplot-orientation: square
// anyplot.ai
// datamatrix-basic: Basic Data Matrix 2D Barcode
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const QUIET_ZONE = 2; // modules of blank margin (spec requires >= 1)
const TITLE_HEIGHT = 64;
const CAPTION_HEIGHT = 48;
const OUTER_MARGIN = 40;
const CARD_PADDING = 32;
// Barcode symbology is black on white in both themes; only the page chrome flips
const MODULE_INK = "#1A1A17";
const SYMBOL_TILE = "#FAF8F1";

// Columns: set these to your data's column names
const CONTENT = "Content"; // role: content
const SIZE = "Size"; // role: size

// Data: replace this block with your own records, one object per row
const data = [{ [CONTENT]: "PCB-SN:48291X7A", [SIZE]: "24x24" }];

// Plot: reads only data and the constants above
const encodedText = String(data[0][CONTENT]);
const moduleCount = parseInt(String(data[0][SIZE]).split("x")[0], 10) || 24;
const TITLE = "datamatrix-basic · javascript · muix · anyplot.ai";
const CAPTION = `Part marking "${encodedText}" · ${moduleCount}×${moduleCount} modules · illustrative data region`;

// Data region: the content's 8-bit ASCII, then a fixed-seed LCG fills the rest
const capacity = (moduleCount - 2) * (moduleCount - 2);
const dataBits = [];
for (const ch of encodedText) {
  for (let shift = 7; shift >= 0; shift--) dataBits.push((ch.charCodeAt(0) >> shift) & 1);
}
let lcgState = 20260902;
while (dataBits.length < capacity) {
  lcgState = (Math.imul(lcgState, 1103515245) + 12345) >>> 0;
  dataBits.push((lcgState >>> 16) & 1);
}

// Symbol grid: finder L on the left column and bottom row, clock on top and right
const GRID = Array.from({ length: moduleCount }, () => new Array(moduleCount).fill(0));
for (let r = 0; r < moduleCount; r++) {
  GRID[r][0] = 1;
  GRID[r][moduleCount - 1] = (moduleCount - 1 - r) % 2 === 0 ? 1 : 0;
}
for (let c = 0; c < moduleCount; c++) {
  GRID[moduleCount - 1][c] = 1;
  GRID[0][c] = c % 2 === 0 ? 1 : 0;
}
let bitIndex = 0;
for (let r = 1; r < moduleCount - 1; r++) {
  for (let c = 1; c < moduleCount - 1; c++) GRID[r][c] = dataBits[bitIndex++];
}

function DataMatrixModules() {
  const { left, top, width } = useDrawingArea();
  const cellSize = width / (moduleCount + QUIET_ZONE * 2);

  const modules = [];
  for (let r = 0; r < moduleCount; r++) {
    for (let c = 0; c < moduleCount; c++) {
      if (!GRID[r][c]) continue;
      modules.push(
        <rect
          key={`${r}-${c}`}
          x={left + (QUIET_ZONE + c) * cellSize}
          y={top + (QUIET_ZONE + r) * cellSize}
          width={cellSize + 0.6}
          height={cellSize + 0.6}
          fill={MODULE_INK}
          shapeRendering="crispEdges"
        />,
      );
    }
  }
  return <g>{modules}</g>;
}

export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const cardSide = Math.min(
    size.width,
    size.height - TITLE_HEIGHT - CAPTION_HEIGHT - OUTER_MARGIN * 2,
  );
  const matrixSide = cardSide - CARD_PADDING * 2;

  return (
    <div
      style={{
        width: size.width,
        height: size.height,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          lineHeight: `${TITLE_HEIGHT}px`,
          paddingLeft: 24,
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            width: cardSide,
            height: cardSide,
            boxSizing: "border-box",
            padding: CARD_PADDING,
            backgroundColor: SYMBOL_TILE,
            border: `1px solid ${t.grid}`,
            borderRadius: 20,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <ChartsContainer
            width={matrixSide}
            height={matrixSide}
            series={[]}
            xAxis={[{ position: "none" }]}
            yAxis={[{ position: "none" }]}
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
            skipAnimation
          >
            <DataMatrixModules />
          </ChartsContainer>
        </div>
      </div>
      <div
        style={{
          height: CAPTION_HEIGHT,
          lineHeight: `${CAPTION_HEIGHT}px`,
          textAlign: "center",
          fontSize: 16,
          color: t.inkSoft,
        }}
      >
        {CAPTION}
      </div>
    </div>
  );
}
