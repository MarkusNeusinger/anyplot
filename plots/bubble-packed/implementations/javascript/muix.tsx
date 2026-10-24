// anyplot.ai
// bubble-packed: Basic Packed Bubble Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 82/100 | Updated: 2026-10-24
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const HEADER_H = 118;
const MARGIN = 24;
const FILL_RATIO = 0.44;
const PADDING = 5;
const ATTRACTION = 0.032;
const ITERATIONS = 420;
const ANCHOR_SPREAD = 1.1; // pushes the group anchors outward from the centre of the drawing area
const DARK_TEXT = "#1A1A17";
const LIGHT_TEXT = "#FAF8F1";

// Columns: set these to your data's column names
const LABEL = "Product line"; // role: label
const VALUE = "Annual revenue ($M)"; // role: value
const GROUP = "Division"; // role: group

// Data: replace this block with your own records, one object per row
const data = [
  { [LABEL]: "Smart Speakers", [GROUP]: "Consumer Electronics", [VALUE]: 42 },
  { [LABEL]: "Wireless Earbuds", [GROUP]: "Consumer Electronics", [VALUE]: 68 },
  { [LABEL]: "4K Televisions", [GROUP]: "Consumer Electronics", [VALUE]: 55 },
  { [LABEL]: "Home Routers", [GROUP]: "Consumer Electronics", [VALUE]: 24 },
  { [LABEL]: "Streaming Devices", [GROUP]: "Consumer Electronics", [VALUE]: 31 },
  { [LABEL]: "Digital Cameras", [GROUP]: "Consumer Electronics", [VALUE]: 18 },
  { [LABEL]: "Gaming Consoles", [GROUP]: "Consumer Electronics", [VALUE]: 74 },
  { [LABEL]: "Tablets", [GROUP]: "Consumer Electronics", [VALUE]: 47 },
  { [LABEL]: "Laptops", [GROUP]: "Consumer Electronics", [VALUE]: 89 },
  { [LABEL]: "Cloud Storage", [GROUP]: "Software & Cloud", [VALUE]: 95 },
  { [LABEL]: "Productivity Suite", [GROUP]: "Software & Cloud", [VALUE]: 61 },
  { [LABEL]: "Video Conferencing", [GROUP]: "Software & Cloud", [VALUE]: 38 },
  { [LABEL]: "Cybersecurity Tools", [GROUP]: "Software & Cloud", [VALUE]: 52 },
  { [LABEL]: "Analytics Platform", [GROUP]: "Software & Cloud", [VALUE]: 44 },
  { [LABEL]: "CRM Software", [GROUP]: "Software & Cloud", [VALUE]: 33 },
  { [LABEL]: "Developer Tools", [GROUP]: "Software & Cloud", [VALUE]: 27 },
  { [LABEL]: "AI Assistant", [GROUP]: "Software & Cloud", [VALUE]: 58 },
  { [LABEL]: "Collaboration Suite", [GROUP]: "Software & Cloud", [VALUE]: 29 },
  { [LABEL]: "Robotic Arms", [GROUP]: "Industrial Equipment", [VALUE]: 71 },
  { [LABEL]: "CNC Machines", [GROUP]: "Industrial Equipment", [VALUE]: 48 },
  { [LABEL]: "Conveyor Systems", [GROUP]: "Industrial Equipment", [VALUE]: 22 },
  { [LABEL]: "Industrial Sensors", [GROUP]: "Industrial Equipment", [VALUE]: 36 },
  { [LABEL]: "3D Printers", [GROUP]: "Industrial Equipment", [VALUE]: 19 },
  { [LABEL]: "Hydraulic Presses", [GROUP]: "Industrial Equipment", [VALUE]: 41 },
  { [LABEL]: "Welding Robots", [GROUP]: "Industrial Equipment", [VALUE]: 53 },
  { [LABEL]: "Packaging Machines", [GROUP]: "Industrial Equipment", [VALUE]: 26 },
  { [LABEL]: "Quality Scanners", [GROUP]: "Industrial Equipment", [VALUE]: 15 },
  { [LABEL]: "Fitness Trackers", [GROUP]: "Health & Wearables", [VALUE]: 39 },
  { [LABEL]: "Smartwatches", [GROUP]: "Health & Wearables", [VALUE]: 62 },
  { [LABEL]: "Blood Pressure Monitors", [GROUP]: "Health & Wearables", [VALUE]: 21 },
  { [LABEL]: "Glucose Monitors", [GROUP]: "Health & Wearables", [VALUE]: 34 },
  { [LABEL]: "Sleep Trackers", [GROUP]: "Health & Wearables", [VALUE]: 17 },
  { [LABEL]: "Posture Sensors", [GROUP]: "Health & Wearables", [VALUE]: 12 },
  { [LABEL]: "Hearing Aids", [GROUP]: "Health & Wearables", [VALUE]: 45 },
  { [LABEL]: "Smart Scales", [GROUP]: "Health & Wearables", [VALUE]: 14 },
  { [LABEL]: "Recovery Devices", [GROUP]: "Health & Wearables", [VALUE]: 23 },
];

// Plot: reads only data and the constants above
const groups = Array.from(new Set(data.map((d) => d[GROUP])));

const groupMeta = Object.fromEntries(
  groups.map((g, i) => {
    const color = t.palette[i];
    const hexVal = Number.parseInt(color.replace("#", ""), 16);
    const srgb = [(hexVal >> 16) & 255, (hexVal >> 8) & 255, hexVal & 255].map(
      (v) => {
        const c = v / 255;
        return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
      },
    );
    const lum = 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2];
    const darkContrast = (Math.max(lum, 0.01) + 0.05) / (0.01 + 0.05);
    const lightContrast = (0.96 + 0.05) / (Math.min(lum, 0.96) + 0.05);
    const labelInk = darkContrast >= lightContrast ? DARK_TEXT : LIGHT_TEXT;
    return [g, { index: i, color, labelInk }];
  }),
);

const totalValue = data.reduce((sum, d) => sum + d[VALUE], 0);
const TITLE = "bubble-packed · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} bubbles (${LABEL}) · ${groups.length} groups (${GROUP}) · Area ∝ ${VALUE}, total ${totalValue.toLocaleString("en-US")}`;

function PackedBubblesLayer() {
  const { left, top, width, height } = useDrawingArea();
  const radiusScale = Math.sqrt(
    (FILL_RATIO * width * height) / (Math.PI * (totalValue || 1)),
  );

  const cols = Math.ceil(Math.sqrt(groups.length));
  const rows = Math.ceil(groups.length / cols);

  const anchors = Object.fromEntries(
    groups.map((g, idx) => {
      const col = idx % cols;
      const row = Math.floor(idx / cols);
      const ax = left + width * (0.5 + ((col + 0.5) / cols - 0.5) * ANCHOR_SPREAD);
      const ay = top + height * (0.5 + ((row + 0.5) / rows - 0.5) * ANCHOR_SPREAD);
      return [g, { x: ax, y: ay }];
    }),
  );

  let seedState = 42;
  const bubbles = data.map((d) => {
    const groupName = d[GROUP];
    const anchor = anchors[groupName];
    seedState = (seedState * 1664525 + 1013904223) % 4294967296;
    const rx = seedState / 4294967296 - 0.5;
    seedState = (seedState * 1664525 + 1013904223) % 4294967296;
    const ry = seedState / 4294967296 - 0.5;
    return {
      label: d[LABEL],
      group: groupName,
      value: d[VALUE],
      r: radiusScale * Math.sqrt(Math.max(0, d[VALUE])),
      x: anchor.x + rx * 60,
      y: anchor.y + ry * 60,
    };
  });

  const resolveCollisions = () => {
    let maxOverlap = 0;
    for (let i = 0; i < bubbles.length; i += 1) {
      for (let j = i + 1; j < bubbles.length; j += 1) {
        const a = bubbles[i];
        const c = bubbles[j];
        const dx = c.x - a.x;
        const dy = c.y - a.y;
        const dist = Math.hypot(dx, dy) || 0.01;
        const minDist = a.r + c.r + PADDING;
        if (dist < minDist) {
          const overlap = (minDist - dist) / 2;
          maxOverlap = Math.max(maxOverlap, overlap);
          const ux = dx / dist;
          const uy = dy / dist;
          a.x -= ux * overlap;
          a.y -= uy * overlap;
          c.x += ux * overlap;
          c.y += uy * overlap;
        }
      }
    }
    return maxOverlap;
  };

  for (let iter = 0; iter < ITERATIONS; iter += 1) {
    const pull = ATTRACTION * (1 - iter / ITERATIONS);
    for (const b of bubbles) {
      const anchor = anchors[b.group];
      b.x += (anchor.x - b.x) * pull;
      b.y += (anchor.y - b.y) * pull;
    }
    resolveCollisions();
    for (const b of bubbles) {
      b.x = Math.min(left + width - b.r, Math.max(left + b.r, b.x));
      b.y = Math.min(top + height - b.r, Math.max(top + b.r, b.y));
    }
  }
  // Collision-only passes: no attraction or clamp, so no circle ends crossing another
  let pass = 0;
  while (pass < 500 && resolveCollisions() > 0.01) pass += 1;

  return (
    <g>
      {bubbles.map((b) => {
        const meta = groupMeta[b.group];
        const valueStr = b.value.toLocaleString("en-US");
        const words = b.label.split(" ");
        const singleLineFits = b.label.length * 8.4 + 20 <= b.r * 2 && b.r >= 52;
        const twoLines =
          !singleLineFits && words.length === 2
            ? [words[0], words[1]]
            : !singleLineFits && words.length === 3
              ? [`${words[0]} ${words[1]}`, words[2]]
              : [b.label];
        const longestLineChars = Math.max(...twoLines.map((line) => line.length));
        const multiLineFits =
          twoLines.length > 1 &&
          longestLineChars * 8.2 + 18 <= b.r * 1.82 &&
          b.r >= 48;
        const showName = singleLineFits || multiLineFits;
        const nameLines = singleLineFits ? [b.label] : twoLines;
        const showValue = b.r >= 30;

        return (
          <g key={b.label}>
            <circle
              cx={b.x}
              cy={b.y}
              r={b.r}
              fill={meta.color}
              stroke={t.pageBg}
              strokeWidth={2}
            >
              <title>{`${b.label} (${b.group}) · ${VALUE}: ${valueStr}`}</title>
            </circle>
            {showName &&
              nameLines.map((line, idx) => {
                const baseOffset =
                  nameLines.length === 1
                    ? -8
                    : idx === 0
                      ? -18
                      : -1;
                return (
                  <text
                    key={`${b.label}-line-${idx}`}
                    x={b.x}
                    y={b.y + baseOffset}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize={14}
                    fontWeight={600}
                    fill={meta.labelInk}
                  >
                    {line}
                  </text>
                );
              })}
            {showValue && (
              <text
                x={b.x}
                y={
                  b.y +
                  (showName
                    ? nameLines.length === 1
                      ? 12
                      : 18
                    : 0)
                }
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={14}
                fontWeight={showName ? 500 : 600}
                fill={meta.labelInk}
              >
                {valueStr}
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const surfaceHeight = height - HEADER_H;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          paddingLeft: MARGIN,
          paddingRight: MARGIN,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 24,
            alignItems: "center",
            paddingTop: 2,
          }}
        >
          {groups.map((g) => (
            <div
              key={g}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 14,
                color: t.inkSoft,
              }}
            >
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  background: groupMeta[g].color,
                  display: "inline-block",
                }}
              />
              <span>{g}</span>
            </div>
          ))}
        </div>
      </div>

      <ChartsContainer
        width={width}
        height={surfaceHeight}
        series={[]}
        skipAnimation
        margin={{ top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }}
      >
        <PackedBubblesLayer />
      </ChartsContainer>
    </div>
  );
}
