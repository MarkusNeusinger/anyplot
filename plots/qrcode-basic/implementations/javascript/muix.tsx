// anyplot.ai
// qrcode-basic: Basic QR Code Generator
// Library: muix 7.29.1 | JavaScript 22.23.0
// Quality: pending | Created: 2026-06-24
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// A QR symbol is black on white in both themes; only the page chrome flips
const MODULE_INK = "#1A1A17";
const SYMBOL_PAPER = "#FAF8F1";
const QUIET_ZONE = 4; // modules of blank border, the QR standard's minimum
const EC_RECOVERY = { L: 7, M: 15, Q: 25, H: 30 }; // percent of codewords each level can restore
const TITLE_H = 64;
const CAPTION_H = 56;
const OUTER_MARGIN = 40;

// Data: replace these parameters with your own content and its encoded symbol
const CONTENT = "https://anyplot.ai"; // role: content
const ERROR_CORRECTION = "M"; // role: error_correction
// The symbol a QR encoder writes for CONTENT at ERROR_CORRECTION (segno 1.6.6: version 2, byte mode,
// mask 1), one string per module row, 1 = dark. The browser has no QR encoder, so new content needs
// a new matrix from one, for example segno.make_qr(content, error="m").matrix
// The matrix is precomputed for CONTENT and ERROR_CORRECTION: changing CONTENT does not re-encode it.
const SYMBOL_ROWS = [
  "1111111010101010001111111",
  "1000001000000000101000001",
  "1011101011011101101011101",
  "1011101001000000001011101",
  "1011101001011110001011101",
  "1000001010101000001000001",
  "1111111010101010101111111",
  "0000000001001001100000000",
  "1010001100010110100100101",
  "1001000011111101001101011",
  "0111111100011001100011101",
  "0010100101111100101001000",
  "0111001101001101001100001",
  "0101110010101001111100011",
  "1110011010101111010001101",
  "0011010001011011110111000",
  "1100101100100110111110010",
  "0000000010100110100010001",
  "1111111011010000101010001",
  "1000001000000101100010001",
  "1011101000111101111110011",
  "1011101000001000010010110",
  "1011101011101110000111011",
  "1000001001111010100110000",
  "1111111011000110111001001",
];

// Plot: reads only the parameters and the constants above
const size = SYMBOL_ROWS.length;
const darkModules = SYMBOL_ROWS.flatMap((row, r) => [...row].flatMap((cell, c) => (cell === "1" ? [{ r, c }] : [])));
const version = (size - 17) / 4;

const TITLE = "qrcode-basic · javascript · muix · anyplot.ai";
const CAPTION = `Encodes “${CONTENT}” · error correction ${ERROR_CORRECTION} (${EC_RECOVERY[ERROR_CORRECTION]} %) · version ${version}, ${size} × ${size} modules`;

// Whole-pixel module size so every module edge is sharp; the quiet zone is part of the tile
function SymbolModules() {
  const { left, top, width } = useDrawingArea();
  const cell = Math.floor(width / (size + 2 * QUIET_ZONE));
  const tile = cell * (size + 2 * QUIET_ZONE);
  const x0 = left + (width - tile) / 2;
  const y0 = top + (width - tile) / 2;

  return (
    <g shapeRendering="crispEdges">
      <rect x={x0} y={y0} width={tile} height={tile} fill={SYMBOL_PAPER} />
      {darkModules.map(({ r, c }) => (
        <rect
          key={`${r}-${c}`}
          x={x0 + (QUIET_ZONE + c) * cell}
          y={y0 + (QUIET_ZONE + r) * cell}
          width={cell}
          height={cell}
          fill={MODULE_INK}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const side = Math.min(width, height - TITLE_H - CAPTION_H) - OUTER_MARGIN * 2;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <ChartsContainer
          width={side}
          height={side}
          series={[]}
          xAxis={[{ position: "none" }]}
          yAxis={[{ position: "none" }]}
          margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          skipAnimation
        >
          <SymbolModules />
        </ChartsContainer>
      </div>
      <div style={{ height: CAPTION_H, display: "flex", alignItems: "center", fontSize: 16, color: t.inkSoft }}>
        {CAPTION}
      </div>
    </div>
  );
}
