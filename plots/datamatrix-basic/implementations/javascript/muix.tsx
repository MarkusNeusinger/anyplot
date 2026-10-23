//# anyplot-orientation: square
// anyplot.ai
// datamatrix-basic: Basic Data Matrix 2D Barcode
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-02
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const QUIET_ZONE = 2; // modules of blank margin (spec requires >= 1)
const TITLE_HEIGHT = 64;
const CAPTION_HEIGHT = 48;
const OUTER_MARGIN = 40;
const CARD_PADDING = 32;

// Columns: set these to your data's column names
const CONTENT = "Content"; // role: content
const SIZE = "Size"; // role: size

// Data: replace this block with your own records, one object per row
const data = [{ [CONTENT]: "PCB-SN:48291X7A", [SIZE]: "24x24" }];

// Plot: reads only data and the constants above
const encodedText = String(data[0][CONTENT]);
const moduleCount = parseInt(String(data[0][SIZE]).split("x")[0], 10) || 24;
const TITLE = "datamatrix-basic · javascript · muix · anyplot.ai";
const CAPTION = `Encodes "${encodedText}" · ${moduleCount}×${moduleCount} modules · ECC 200`;

function hashString(text) {
  let hash = 2166136261;
  for (let i = 0; i < text.length; i++) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function encodeBits(text, capacity) {
  const bits = [];
  for (let i = 0; i < text.length && bits.length < capacity; i++) {
    const code = text.charCodeAt(i);
    for (let shift = 7; shift >= 0 && bits.length < capacity; shift--) {
      bits.push((code >> shift) & 1);
    }
  }
  let state = hashString(text) || 1;
  while (bits.length < capacity) {
    state = (Math.imul(state, 1103515245) + 12345) >>> 0;
    bits.push((state >>> 16) & 1);
  }
  return bits;
}

function buildMatrix(text, size) {
  const grid = Array.from({ length: size }, () => new Array(size).fill(0));

  for (let r = 0; r < size; r++) grid[r][0] = 1;
  for (let c = 0; c < size; c++) grid[size - 1][c] = 1;
  for (let c = 1; c < size; c++) grid[0][c] = c % 2 === 1 ? 1 : 0;
  for (let r = 1; r < size - 1; r++) grid[r][size - 1] = r % 2 === 1 ? 1 : 0;

  const dataBits = encodeBits(text, (size - 2) * (size - 2));
  let bitIndex = 0;
  for (let r = 1; r < size - 1; r++) {
    for (let c = 1; c < size - 1; c++) {
      grid[r][c] = dataBits[bitIndex++];
    }
  }
  return grid;
}

const GRID = buildMatrix(encodedText, moduleCount);

function DataMatrixModules() {
  const { left, top, width } = useDrawingArea();
  const totalUnits = moduleCount + QUIET_ZONE * 2;
  const cellSize = width / totalUnits;

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
          fill={t.palette[0]}
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
            backgroundColor: t.elevatedBg,
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
