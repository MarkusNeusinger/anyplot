// anyplot.ai
// pictogram-basic: Pictogram Chart (Isotype Visualization)
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-08-20
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const MAX_ICONS = 8; // the longest row holds at most this many icons
const NICE_STEPS = [1, 2, 2.5, 5, 10]; // icon values are one of these times a power of ten
const ICON_SHARE = 0.4; // icon radius as a share of the smaller of row height and icon pitch
const MIN_REMAINDER = 0.02; // remainders below this share of an icon are not drawn
const TITLE_H = 52;
const LEGEND_H = 44;
const LEGEND_ICON = 20;

// Columns: set these to your data's column names
const FRUIT = "Fruit"; // role: category
const HARVEST = "Weekly harvest (tons)"; // role: value

// Data: replace this block with your own records, one object per row
// Weekly harvest of a small farm co-op
const data = [
  { [FRUIT]: "Apples", [HARVEST]: 35 },
  { [FRUIT]: "Oranges", [HARVEST]: 22 },
  { [FRUIT]: "Bananas", [HARVEST]: 18 },
  { [FRUIT]: "Mangoes", [HARVEST]: 27 },
  { [FRUIT]: "Grapes", [HARVEST]: 14 },
];

// Plot: reads only data and the constants above
const fruits = data.map((d) => d[FRUIT]);
const maxValue = Math.max(...data.map((d) => d[HARVEST]));

// Value of one icon: the smallest nice step that keeps the longest row within MAX_ICONS
const magnitude = 10 ** Math.floor(Math.log10(maxValue / MAX_ICONS));
const unitValue = magnitude * NICE_STEPS.find((step) => step * magnitude >= maxValue / MAX_ICONS);
const iconSlots = Math.ceil(maxValue / unitValue - 1e-9);

const rows = data.map((d) => {
  const count = d[HARVEST] / unitValue;
  const full = Math.floor(count + 1e-9);
  const remainder = count - full;
  return { fruit: d[FRUIT], full, remainder: remainder >= MIN_REMAINDER ? remainder : 0 };
});

const unitMatch = HARVEST.match(/\(([^)]+)\)/);
const unit = unitMatch ? unitMatch[1] : "";

const TITLE = "Weekly Fruit Harvest · pictogram-basic · javascript · muix · anyplot.ai";

function IconRows() {
  const yScale = useYScale("fruit");
  const { left, width } = useDrawingArea();
  // Icons sit at one pitch across the full drawing width, so the longest row reaches its right
  // edge; the radius fits both that pitch and the row height, so every icon keeps one size
  const pitch = width / iconSlots;
  const radius = Math.min(yScale.bandwidth(), pitch) * ICON_SHARE;

  return (
    <g>
      {rows.map((row, r) => {
        const cy = yScale(row.fruit) + yScale.bandwidth() / 2;
        const partialX = left + (row.full + 0.5) * pitch;
        return (
          <g key={row.fruit}>
            {Array.from({ length: row.full }, (_, i) => (
              <circle key={i} cx={left + (i + 0.5) * pitch} cy={cy} r={radius} fill={t.palette[0]} />
            ))}
            {row.remainder > 0 && (
              <g>
                <clipPath id={`pictogram-remainder-${r}`}>
                  <rect x={partialX - radius} y={cy - radius} width={2 * radius * row.remainder} height={2 * radius} />
                </clipPath>
                <circle cx={partialX} cy={cy} r={radius} fill="none" stroke={t.palette[0]} strokeWidth={2.5} strokeOpacity={0.7} />
                <circle cx={partialX} cy={cy} r={radius} fill={t.palette[0]} clipPath={`url(#pictogram-remainder-${r})`} />
              </g>
            )}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: 10, fontSize: 16, color: t.inkSoft }}>
        <svg width={LEGEND_ICON} height={LEGEND_ICON}>
          <circle cx={LEGEND_ICON / 2} cy={LEGEND_ICON / 2} r={LEGEND_ICON / 2} fill={t.palette[0]} />
        </svg>
        <span>
          = {unitValue.toLocaleString("en-US")} {unit} · a cut icon shows the remainder
        </span>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H - LEGEND_H}
        margin={{ top: 16, right: 64, bottom: 32, left: 24 }}
        series={[]}
        xAxis={[{ id: "slots", scaleType: "linear", min: 0, max: iconSlots, position: "none" }]}
        yAxis={[
          {
            id: "fruit",
            scaleType: "band",
            data: fruits,
            categoryGapRatio: 0.15,
            label: FRUIT,
            width: 140,
            disableTicks: true,
            disableLine: true,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        skipAnimation
      >
        <IconRows />
        <ChartsYAxis axisId="fruit" />
      </ChartsContainer>
    </div>
  );
}
