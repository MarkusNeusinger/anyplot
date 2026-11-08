// anyplot.ai
// map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { getLuminance } from "@mui/material/styles";
import { useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TILE_GAP_SHARE = 0.08; // share of the tile pitch left open between neighbouring tiles
const INK_SWITCH = 0.19; // relative luminance where #1A1A17 and #FAF8F1 reach equal contrast on a tile
const DARK_INK = "#1A1A17";
const LIGHT_INK = "#FAF8F1";

// Columns: set these to your data's column names
const COUNTRY = "Country"; // role: region
const SHARE = "Renewable electricity share (%)"; // role: value
const ROW = "Grid row"; // role: row
const COL = "Grid column"; // role: col

// Data: replace this block with your own records, one object per row
// Renewable share of electricity by European country on a compass tile grid (row 0 = north, col 0 = west).
const data = [
  ["IS", 0, 0, 99], ["NO", 0, 3, 98], ["SE", 0, 5, 65], ["FI", 0, 7, 55],
  ["IE", 1, 0, 40], ["GB", 1, 1, 43], ["DK", 1, 4, 62], ["EE", 1, 8, 32],
  ["NL", 2, 2, 37], ["DE", 2, 4, 46], ["PL", 2, 6, 18], ["LT", 2, 8, 28],
  ["BE", 3, 1, 24], ["CZ", 3, 4, 17], ["SK", 3, 5, 23], ["UA", 3, 8, 9],
  ["FR", 4, 1, 25], ["CH", 4, 3, 72], ["AT", 4, 4, 78], ["HU", 4, 5, 14], ["RO", 4, 7, 43],
  ["PT", 5, 0, 61], ["ES", 5, 1, 46], ["IT", 5, 4, 35], ["HR", 5, 5, 55], ["RS", 5, 6, 30], ["BG", 5, 7, 19],
  ["GR", 6, 6, 40],
].map(([country, row, col, share]) => ({ [COUNTRY]: country, [ROW]: row, [COL]: col, [SHARE]: share }));

// Plot: reads only data and the constants above
const tiles = data.filter((d) => d[ROW] != null && d[COL] != null);
const nCols = Math.max(...tiles.map((d) => d[COL])) + 1;
const nRows = Math.max(...tiles.map((d) => d[ROW])) + 1;
const shares = tiles.map((d) => d[SHARE]).filter((v) => v != null);
const minShare = Math.min(...shares);
const maxShare = Math.max(...shares);
const unit = SHARE.match(/\(([^)]+)\)/)?.[1] ?? "";
const lowest = tiles.find((d) => d[SHARE] === minShare);
const highest = tiles.find((d) => d[SHARE] === maxShare);

const TITLE = "map-tilegrid · javascript · muix · anyplot.ai";
const SUBTITLE = `${tiles.length} countries, one equal tile each · ${SHARE} from ${minShare}${unit} (${lowest[COUNTRY]}) to ${maxShare}${unit} (${highest[COUNTRY]})`;
const HEADER_H = 80;
const LEGEND_W = 190;
const PAD = 24;

function Tiles() {
  const xScale = useXScale();
  const yScale = useYScale();
  const colorScale = useZColorScale();
  const pitch = xScale(1) - xScale(0);
  const gap = pitch * TILE_GAP_SHARE;
  const size = pitch - gap;
  return (
    <g>
      {tiles.map((d) => {
        const x = xScale(d[COL]) + gap / 2;
        const y = yScale(d[ROW]) + gap / 2;
        const fill = d[SHARE] == null ? t.elevatedBg : colorScale(d[SHARE]);
        // Fixed ink by the tile's relative luminance, so the label stays legible in both themes
        const ink = d[SHARE] == null ? t.inkSoft : getLuminance(fill) > INK_SWITCH ? DARK_INK : LIGHT_INK;
        return (
          <g key={d[COUNTRY]}>
            <rect x={x} y={y} width={size} height={size} rx={size * 0.1} fill={fill} />
            <text
              x={x + size / 2}
              y={y + size * 0.44}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={Math.max(14, size * 0.3)}
              fontWeight={700}
              fill={ink}
            >
              {d[COUNTRY]}
            </text>
            <text x={x + size / 2} y={y + size * 0.76} textAnchor="middle" dominantBaseline="central" fontSize={15} fill={ink}>
              {d[SHARE] == null ? "–" : `${d[SHARE]}${unit}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const bodyH = height - HEADER_H;
  // One pitch on both axes keeps every tile square; the grid sits centred left of the colour bar
  const pitch = Math.floor(Math.min((width - LEGEND_W - 3 * PAD) / nCols, (bodyH - 2 * PAD) / nRows));
  const gridW = pitch * nCols;
  const gridH = pitch * nRows;
  const left = Math.round((width - LEGEND_W - PAD - gridW) / 2);
  const top = Math.round((bodyH - gridH) / 2);
  const margin = { top, left, right: width - left - gridW, bottom: bodyH - top - gridH };

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: `16px 40px 0 ${left}px`, boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <div style={{ position: "relative", width, height: bodyH }}>
        <ChartsDataProvider
          width={width}
          height={bodyH}
          margin={margin}
          series={[]}
          skipAnimation
          xAxis={[{ id: "col", scaleType: "linear", min: 0, max: nCols, position: "none" }]}
          yAxis={[{ id: "row", scaleType: "linear", min: 0, max: nRows, reverse: true, position: "none" }]}
          zAxis={[
            {
              id: "share",
              colorMap: { type: "continuous", min: minShare, max: maxShare, color: [t.seq[0], t.seq[1]] },
            },
          ]}
        >
          <ChartsSurface>
            <Tiles />
          </ChartsSurface>
          <div
            style={{
              position: "absolute",
              left: left + gridW + 2 * PAD,
              top: top + gridH * 0.2,
              width: LEGEND_W,
              height: gridH * 0.6,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 500, color: t.ink, marginBottom: 12 }}>{SHARE}</div>
            <ContinuousColorLegend
              axisDirection="z"
              axisId="share"
              direction="vertical"
              thickness={20}
              minLabel={`${minShare}${unit}`}
              maxLabel={`${maxShare}${unit}`}
              sx={{ flex: 1, color: t.inkSoft, "& *": { fontSize: 15 } }}
            />
          </div>
        </ChartsDataProvider>
      </div>
    </div>
  );
}
