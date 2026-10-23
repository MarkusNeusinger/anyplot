//# anyplot-orientation: landscape
// anyplot.ai
// heatmap-periodic-table: Periodic Table Property Heatmap
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 78/100 | Updated: 2026-10-23
// anyplot.ai
// heatmap-periodic-table: Periodic Table Property Heatmap
// Library: MUI X Charts | React | Node
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-15

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const ATOMIC_NUMBER = "Atomic number"; // role: id
const SYMBOL = "Symbol"; // role: label
const GROUP = "Group"; // role: column (null = f-block, placed in the detached rows)
const PERIOD = "Period"; // role: row
const VALUE = "Pauling electronegativity"; // role: value (null = no value)

// Data: replace this block with your own records, one object per row
const el = (z, symbol, group, period, value) => ({
  [ATOMIC_NUMBER]: z, [SYMBOL]: symbol, [GROUP]: group, [PERIOD]: period, [VALUE]: value,
});
const data = [
  el(1, "H", 1, 1, 2.20), el(2, "He", 18, 1, null),
  el(3, "Li", 1, 2, 0.98), el(4, "Be", 2, 2, 1.57), el(5, "B", 13, 2, 2.04), el(6, "C", 14, 2, 2.55),
  el(7, "N", 15, 2, 3.04), el(8, "O", 16, 2, 3.44), el(9, "F", 17, 2, 3.98), el(10, "Ne", 18, 2, null),
  el(11, "Na", 1, 3, 0.93), el(12, "Mg", 2, 3, 1.31), el(13, "Al", 13, 3, 1.61), el(14, "Si", 14, 3, 1.90),
  el(15, "P", 15, 3, 2.19), el(16, "S", 16, 3, 2.58), el(17, "Cl", 17, 3, 3.16), el(18, "Ar", 18, 3, null),
  el(19, "K", 1, 4, 0.82), el(20, "Ca", 2, 4, 1.00), el(21, "Sc", 3, 4, 1.36), el(22, "Ti", 4, 4, 1.54),
  el(23, "V", 5, 4, 1.63), el(24, "Cr", 6, 4, 1.66), el(25, "Mn", 7, 4, 1.55), el(26, "Fe", 8, 4, 1.83),
  el(27, "Co", 9, 4, 1.88), el(28, "Ni", 10, 4, 1.91), el(29, "Cu", 11, 4, 1.90), el(30, "Zn", 12, 4, 1.65),
  el(31, "Ga", 13, 4, 1.81), el(32, "Ge", 14, 4, 2.01), el(33, "As", 15, 4, 2.18), el(34, "Se", 16, 4, 2.55),
  el(35, "Br", 17, 4, 2.96), el(36, "Kr", 18, 4, 3.00),
  el(37, "Rb", 1, 5, 0.82), el(38, "Sr", 2, 5, 0.95), el(39, "Y", 3, 5, 1.22), el(40, "Zr", 4, 5, 1.33),
  el(41, "Nb", 5, 5, 1.60), el(42, "Mo", 6, 5, 2.16), el(43, "Tc", 7, 5, 1.90), el(44, "Ru", 8, 5, 2.20),
  el(45, "Rh", 9, 5, 2.28), el(46, "Pd", 10, 5, 2.20), el(47, "Ag", 11, 5, 1.93), el(48, "Cd", 12, 5, 1.69),
  el(49, "In", 13, 5, 1.78), el(50, "Sn", 14, 5, 1.96), el(51, "Sb", 15, 5, 2.05), el(52, "Te", 16, 5, 2.10),
  el(53, "I", 17, 5, 2.66), el(54, "Xe", 18, 5, 2.60),
  el(55, "Cs", 1, 6, 0.79), el(56, "Ba", 2, 6, 0.89),
  el(57, "La", null, 6, 1.10), el(58, "Ce", null, 6, 1.12), el(59, "Pr", null, 6, 1.13), el(60, "Nd", null, 6, 1.14),
  el(61, "Pm", null, 6, null), el(62, "Sm", null, 6, 1.17), el(63, "Eu", null, 6, null), el(64, "Gd", null, 6, 1.20),
  el(65, "Tb", null, 6, null), el(66, "Dy", null, 6, 1.22), el(67, "Ho", null, 6, 1.23), el(68, "Er", null, 6, 1.24),
  el(69, "Tm", null, 6, 1.25), el(70, "Yb", null, 6, null), el(71, "Lu", null, 6, 1.27),
  el(72, "Hf", 4, 6, 1.30), el(73, "Ta", 5, 6, 1.50), el(74, "W", 6, 6, 2.36), el(75, "Re", 7, 6, 1.90),
  el(76, "Os", 8, 6, 2.20), el(77, "Ir", 9, 6, 2.20), el(78, "Pt", 10, 6, 2.28), el(79, "Au", 11, 6, 2.54),
  el(80, "Hg", 12, 6, 2.00), el(81, "Tl", 13, 6, 1.62), el(82, "Pb", 14, 6, 2.33), el(83, "Bi", 15, 6, 2.02),
  el(84, "Po", 16, 6, 2.00), el(85, "At", 17, 6, 2.20), el(86, "Rn", 18, 6, null),
  el(87, "Fr", 1, 7, 0.70), el(88, "Ra", 2, 7, 0.90),
  el(89, "Ac", null, 7, 1.10), el(90, "Th", null, 7, 1.30), el(91, "Pa", null, 7, 1.50), el(92, "U", null, 7, 1.38),
  el(93, "Np", null, 7, 1.36), el(94, "Pu", null, 7, 1.28), el(95, "Am", null, 7, 1.30), el(96, "Cm", null, 7, 1.30),
  el(97, "Bk", null, 7, 1.30), el(98, "Cf", null, 7, 1.30), el(99, "Es", null, 7, 1.30), el(100, "Fm", null, 7, 1.30),
  el(101, "Md", null, 7, 1.30), el(102, "No", null, 7, 1.30), el(103, "Lr", null, 7, null),
  el(104, "Rf", 4, 7, null), el(105, "Db", 5, 7, null), el(106, "Sg", 6, 7, null), el(107, "Bh", 7, 7, null),
  el(108, "Hs", 8, 7, null), el(109, "Mt", 9, 7, null), el(110, "Ds", 10, 7, null), el(111, "Rg", 11, 7, null),
  el(112, "Cn", 12, 7, null), el(113, "Nh", 13, 7, null), el(114, "Fl", 14, 7, null), el(115, "Mc", 15, 7, null),
  el(116, "Lv", 16, 7, null), el(117, "Ts", 17, 7, null), el(118, "Og", 18, 7, null),
];

// Plot: reads only data and the constants above
const F_START_GROUP = 3; // f-block rows start under group 3, as in the canonical layout
const F_GAP = 0.4; // gap between the main body and the f-block rows, in tile pitches
const TILE_INSET = 2; // px of page showing between neighbouring tiles

const valued = data.filter((d) => d[VALUE] !== null);
const minEl = valued.reduce((a, b) => (b[VALUE] < a[VALUE] ? b : a));
const maxEl = valued.reduce((a, b) => (b[VALUE] > a[VALUE] ? b : a));
const nGroups = Math.max(...data.map((d) => d[GROUP] ?? 0));
const nPeriods = Math.max(...data.map((d) => d[PERIOD]));

// f-block elements fill their detached row in atomic-number order
const fPeriods = [...new Set(data.filter((d) => d[GROUP] === null).map((d) => d[PERIOD]))].sort((a, b) => a - b);
const tiles = data.map((d) => {
  if (d[GROUP] !== null) return { ...d, col: d[GROUP] - 1, row: d[PERIOD] - 1 };
  const series = data
    .filter((e) => e[GROUP] === null && e[PERIOD] === d[PERIOD])
    .sort((a, b) => a[ATOMIC_NUMBER] - b[ATOMIC_NUMBER]);
  return {
    ...d,
    col: F_START_GROUP - 1 + series.indexOf(d),
    row: nPeriods + F_GAP + fPeriods.indexOf(d[PERIOD]),
  };
});
const placeholders = fPeriods.map((p) => {
  const zs = data.filter((d) => d[GROUP] === null && d[PERIOD] === p).map((d) => d[ATOMIC_NUMBER]);
  return { period: p, label: `${Math.min(...zs)}–${Math.max(...zs)}` };
});
const nRows = nPeriods + F_GAP + fPeriods.length;

// Dark or light tile text by the WCAG relative luminance of the fill
function textOn(fill) {
  const lin = fill.match(/\d+/g).slice(0, 3).map((c) => {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2] > 0.18 ? "#1A1A17" : "#F0EFE8";
}

function Tiles({ nullFill }) {
  const xScale = useXScale();
  const yScale = useYScale();
  const colorScale = useZColorScale();
  const pitch = xScale(1) - xScale(0);
  const size = pitch - 2 * TILE_INSET;

  return (
    <g>
      {placeholders.map(({ period, label }) => {
        const x = xScale(F_START_GROUP - 1) + TILE_INSET;
        const y = yScale(period - 1) + TILE_INSET;
        return (
          <g key={label}>
            <rect x={x} y={y} width={size} height={size} rx={2} fill="none"
              stroke={t.inkSoft} strokeWidth={1} strokeDasharray="4,3" />
            <text x={x + size / 2} y={y + size / 2 + 5} textAnchor="middle"
              fontSize={14} fill={t.inkSoft} fontFamily="monospace">
              {label}
            </text>
          </g>
        );
      })}
      {tiles.map((d) => {
        const x = xScale(d.col) + TILE_INSET;
        const y = yScale(d.row) + TILE_INSET;
        const hasValue = d[VALUE] !== null;
        const fill = hasValue ? colorScale(d[VALUE]) : nullFill;
        const ink = hasValue ? textOn(fill) : t.inkSoft;
        return (
          <g key={d[ATOMIC_NUMBER]}>
            <rect x={x} y={y} width={size} height={size} rx={2} fill={fill} />
            <text x={x + 5} y={y + 16} fontSize={14} fill={ink} fontFamily="monospace">
              {d[ATOMIC_NUMBER]}
            </text>
            <text x={x + size / 2} y={y + size / 2 + 9} textAnchor="middle" fontSize={28}
              fontWeight={700} fill={ink} fontFamily="Inter, Roboto, sans-serif">
              {d[SYMBOL]}
            </text>
            {hasValue && (
              <text x={x + size / 2} y={y + size - 7} textAnchor="middle" fontSize={14}
                fill={ink} fontFamily="monospace">
                {d[VALUE].toFixed(2)}
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const nullFill = window.ANYPLOT_THEME === "light" ? "#CCCBC3" : "#3E3E3A";

  // Square tiles: one pitch for both axes, the table centred below the title band
  const TOP = 96;
  const pitch = Math.floor(Math.min((W - 80) / nGroups, (H - TOP - 20) / nRows));
  const left = Math.round((W - pitch * nGroups) / 2);
  const margin = { top: TOP, left, right: W - left - pitch * nGroups, bottom: H - TOP - pitch * nRows };

  // The empty band between groups 2 and 13 in periods 1–3 holds the color legend
  const legendLeft = left + pitch * 2.6;
  const legendWidth = pitch * (12 - 2.6) - pitch * 0.3;

  return (
    <Box sx={{ position: "relative", width: W, height: H }}>
      <ChartsDataProvider
        width={W}
        height={H}
        margin={margin}
        series={[]}
        skipAnimation
        xAxis={[{ id: "group", scaleType: "linear", min: 0, max: nGroups, position: "none" }]}
        yAxis={[{ id: "row", scaleType: "linear", min: 0, max: nRows, reverse: true, position: "none" }]}
        zAxis={[{
          id: "value",
          colorMap: { type: "continuous", min: minEl[VALUE], max: maxEl[VALUE], color: [t.seq[0], t.seq[1]] },
        }]}
      >
        <ChartsSurface>
          <text x={W / 2} y={44} textAnchor="middle" fontSize={24} fontWeight={500}
            fill={t.ink} fontFamily="Inter, Roboto, sans-serif">
            heatmap-periodic-table · javascript · muix · anyplot.ai
          </text>
          <text x={W / 2} y={74} textAnchor="middle" fontSize={17}
            fill={t.inkSoft} fontFamily="Inter, Roboto, sans-serif">
            {VALUE} — rising toward fluorine at the top right, falling toward francium at the bottom left
          </text>
          <Tiles nullFill={nullFill} />
        </ChartsSurface>
        <Box sx={{ position: "absolute", left: legendLeft, top: TOP + pitch * 0.35, width: legendWidth }}>
          <Typography sx={{ fontSize: 17, fontWeight: 500, color: t.ink, textAlign: "center" }}>
            {VALUE} (Pauling scale, dimensionless)
          </Typography>
          <ContinuousColorLegend
            axisDirection="z"
            axisId="value"
            thickness={22}
            minLabel={`Low: ${minEl[SYMBOL]} ${minEl[VALUE].toFixed(2)}`}
            maxLabel={`High: ${maxEl[SYMBOL]} ${maxEl[VALUE].toFixed(2)}`}
            sx={{ width: "100%", m: 0, mt: 1, color: t.inkSoft, "& *": { fontSize: 15, whiteSpace: "nowrap" } }}
          />
          <Typography sx={{ mt: 1.5, fontSize: 15, fontStyle: "italic", color: t.inkSoft, textAlign: "center" }}>
            Grey tiles: no {VALUE} value
          </Typography>
        </Box>
      </ChartsDataProvider>
    </Box>
  );
}
