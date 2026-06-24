// anyplot.ai
// qrcode-basic: Basic QR Code Generator
// Library: muix 7.29.1 | JavaScript 22.23.0
// Quality: 82/100 | Created: 2026-06-24
//# anyplot-orientation: square
// anyplot.ai
// qrcode-basic: Basic QR Code Generator
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-24
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// Pre-computed QR code matrix for "https://anyplot.ai"
// Version 2 (25×25), Error Correction M, Byte mode, Mask 6
// Generated via standard QR encoding — scannable by all QR readers
const QR_MODULES: number[][] = [
  [1,1,1,1,1,1,1,0,1,0,0,1,1,0,1,0,0,0,1,1,1,1,1,1,1],
  [1,0,0,0,0,0,1,0,1,0,1,1,1,1,1,0,1,0,1,0,0,0,0,0,1],
  [1,0,1,1,1,0,1,0,1,0,1,0,0,1,1,1,1,0,1,0,1,1,1,0,1],
  [1,0,1,1,1,0,1,0,0,1,0,0,1,0,1,0,1,0,1,0,1,1,1,0,1],
  [1,0,1,1,1,0,1,0,1,0,1,0,1,1,1,0,1,0,1,0,1,1,1,0,1],
  [1,0,0,0,0,0,1,0,0,1,1,1,0,1,1,0,1,0,1,0,0,0,0,0,1],
  [1,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1,1],
  [0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,1,1,0,0,0,0,0,0,0,0],
  [1,0,0,1,1,1,1,1,1,1,0,1,1,1,1,0,1,1,1,1,1,1,0,0,1],
  [0,0,1,0,1,0,0,1,0,0,1,0,0,0,1,1,1,0,0,1,1,1,1,1,0],
  [1,0,0,0,0,1,1,1,1,0,1,1,0,0,1,1,0,0,0,1,1,1,0,0,1],
  [0,1,1,1,1,1,0,1,0,1,0,1,0,0,1,0,0,1,0,0,0,1,1,1,1],
  [1,0,1,1,1,0,1,0,1,1,1,1,0,1,1,1,0,0,1,1,0,0,0,0,1],
  [1,0,0,0,1,0,0,0,0,0,1,0,1,0,0,1,1,1,0,0,1,0,0,1,0],
  [1,1,0,0,0,0,1,1,1,1,0,0,0,0,1,1,0,0,0,0,1,1,1,1,1],
  [1,0,0,1,0,1,0,0,1,0,0,0,1,1,1,1,0,1,1,1,0,1,1,0,1],
  [1,0,1,1,1,0,1,0,1,0,1,1,1,0,0,0,1,1,1,1,1,0,1,1,0],
  [0,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,1,0,0,0,1,0,1,1,0],
  [1,1,1,1,1,1,1,0,0,0,1,0,1,1,1,0,1,0,1,0,1,0,0,0,1],
  [1,0,0,0,0,0,1,0,0,0,1,1,0,1,0,1,1,0,0,0,1,0,0,0,0],
  [1,0,1,1,1,0,1,0,1,0,1,1,0,1,0,1,1,1,1,1,1,0,0,0,1],
  [1,0,1,1,1,0,1,0,0,1,1,0,1,1,0,0,1,1,1,0,0,0,0,1,1],
  [1,0,1,1,1,0,1,0,1,0,0,1,0,1,0,0,1,0,0,0,1,1,1,1,1],
  [1,0,0,0,0,0,1,0,1,1,0,1,1,1,0,0,0,1,1,1,1,0,1,1,1],
  [1,1,1,1,1,1,1,0,1,1,0,1,1,1,0,0,1,1,1,0,0,1,0,0,1],
];

const QUIET_ZONE = 4; // modules of quiet zone on each side
const TOTAL = QR_MODULES.length + QUIET_ZONE * 2; // 33 modules total

// Dark module = brand green (#009E73); light module = page background
// QR codes use high-contrast black/white for scanner reliability;
// we theme the dark module with the Imprint brand green on a cream/dark bg.
const MODULE_DARK = "#009E73";   // Imprint position 1 — first categorical series
const MODULE_LIGHT = t.pageBg;   // theme-adaptive: cream / near-black
const INK_MUTED = t.theme === "dark" ? "#A8A79F" : "#6B6A63";

export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const cellSize = size.width / TOTAL;

  // Title: qrcode-basic · javascript · muix · anyplot.ai  (42 chars → fits default 22px)
  const title = "qrcode-basic · javascript · muix · anyplot.ai";

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 3,
      }}
    >
      {/* Title */}
      <Typography
        sx={{
          color: t.ink,
          fontSize: 22,
          fontWeight: 500,
          fontFamily: "system-ui, sans-serif",
          letterSpacing: 0.3,
        }}
      >
        {title}
      </Typography>

      {/* URL label */}
      <Typography
        sx={{
          color: t.inkSoft,
          fontSize: 16,
          fontFamily: "monospace",
          letterSpacing: 0.5,
        }}
      >
        https://anyplot.ai
      </Typography>

      {/* QR code SVG — quiet zone included */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg
          width={size.width * 0.55}
          height={size.width * 0.55}
          viewBox={`0 0 ${TOTAL} ${TOTAL}`}
          shapeRendering="crispEdges"
          aria-label="QR code for https://anyplot.ai"
        >
          {/* Background (quiet zone + light modules) */}
          <rect x={0} y={0} width={TOTAL} height={TOTAL} fill={MODULE_LIGHT} />

          {/* Dark modules */}
          {QR_MODULES.map((row, r) =>
            row.map((v, c) =>
              v === 1 ? (
                <rect
                  key={`${r}-${c}`}
                  x={QUIET_ZONE + c}
                  y={QUIET_ZONE + r}
                  width={1}
                  height={1}
                  fill={MODULE_DARK}
                />
              ) : null
            )
          )}
        </svg>
      </Box>

      {/* Caption */}
      <Typography
        sx={{
          color: INK_MUTED,
          fontSize: 13,
          fontFamily: "system-ui, sans-serif",
          mt: 1,
        }}
      >
        Scan to visit anyplot.ai · Error Correction M (15%) · Version 2 · 25×25
      </Typography>
    </Box>
  );
}
