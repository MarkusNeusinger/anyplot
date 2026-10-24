// anyplot.ai
// qrcode-basic: Basic QR Code Generator
// Library: muix 7.29.1 | JavaScript 22.23.0
// Quality: 83/100 | Created: 2026-06-24
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { Box } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "qrcode-basic · javascript · muix · anyplot.ai";
const QUIET_ZONE = 4;
const MODULE_DARK = "#000000";
const MODULE_LIGHT = "#FFFFFF";

// Columns: set these to your data's column names
const CONTENT = "Encoded URL or text"; // role: content
const ERROR_CORRECTION = "Error correction level"; // role: error_correction

// Data: replace this block with your own records
const data = [
  {
    [CONTENT]: "https://anyplot.ai",
    [ERROR_CORRECTION]: "M (15%)",
    version: 2,
    modules: [
      [1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
      [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],
      [1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1],
      [1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1],
      [1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1],
      [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],
      [1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1],
      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
      [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1],
      [0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0],
      [1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1],
      [0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1],
      [1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1],
      [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0],
      [1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1],
      [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1],
      [1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0],
      [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1],
      [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0],
      [1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1],
      [1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1],
      [1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1],
      [1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1],
      [1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1],
    ],
  },
];

// Plot: reads only data and the constants above
const record = data[0];
const contentText = String(record[CONTENT]);
const ecText = String(record[ERROR_CORRECTION]);
const qrModules = record.modules;
const qrSize = qrModules.length;
const totalModules = qrSize + QUIET_ZONE * 2;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  const cellPx = Math.floor((width * 0.55) / totalModules);
  const qrPx = cellPx * totalModules;

  const titleH = 28;
  const urlH = 22;
  const captionH = 18;
  const gap1 = 10;
  const gap2 = 28;
  const gap3 = 28;
  const contentH = titleH + gap1 + urlH + gap2 + qrPx + gap3 + captionH;
  const yStart = Math.round((height - contentH) / 2);

  const titleY = yStart + titleH;
  const urlY = titleY + gap1 + urlH;
  const qrTop = urlY + gap2;
  const qrLeft = Math.round((width - qrPx) / 2);
  const captionY = qrTop + qrPx + gap3 + captionH;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg }}>
      <ChartsContainer width={width} height={height} series={[]} skipAnimation>
        <text
          x={width / 2}
          y={titleY}
          textAnchor="middle"
          fontSize={22}
          fontWeight="500"
          fill={t.ink}
        >
          {TITLE}
        </text>

        <text
          x={width / 2}
          y={urlY}
          textAnchor="middle"
          fontSize={16}
          fill={t.inkSoft}
        >
          {contentText}
        </text>

        <rect
          x={qrLeft}
          y={qrTop}
          width={qrPx}
          height={qrPx}
          fill={MODULE_LIGHT}
          shapeRendering="crispEdges"
        />

        {qrModules.map((row, r) =>
          row.map((v, c) =>
            v === 1 ? (
              <rect
                key={`${r}-${c}`}
                x={qrLeft + (QUIET_ZONE + c) * cellPx}
                y={qrTop + (QUIET_ZONE + r) * cellPx}
                width={cellPx}
                height={cellPx}
                fill={MODULE_DARK}
                shapeRendering="crispEdges"
              />
            ) : null
          )
        )}

        <text
          x={width / 2}
          y={captionY}
          textAnchor="middle"
          fontSize={14}
          fill={t.inkSoft}
        >
          {`Scan to visit ${contentText} · ${ERROR_CORRECTION}: ${ecText} · Version ${record.version} · ${qrSize}×${qrSize}`}
        </text>
      </ChartsContainer>
    </Box>
  );
}
