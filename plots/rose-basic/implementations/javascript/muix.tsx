//# anyplot-orientation: square
// anyplot.ai
// rose-basic: Basic Rose Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-07-25
import { PieChart } from "@mui/x-charts/PieChart";

const t = window.ANYPLOT_TOKENS;
const TITLE = "rose-basic · javascript · muix · anyplot.ai";

// --- Data (in-memory, deterministic): average monthly rainfall, mm ----------
const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const RAINFALL_MM = [88, 65, 70, 52, 48, 32, 22, 28, 45, 78, 95, 92];

// Linear interpolation between two Imprint hex stops (imprint_seq).
function mixHex(hexA, hexB, ratio) {
  const a = [1, 3, 5].map((i) => parseInt(hexA.slice(i, i + 2), 16));
  const b = [1, 3, 5].map((i) => parseInt(hexB.slice(i, i + 2), 16));
  const mixed = a.map((v, i) => Math.round(v + (b[i] - v) * ratio));
  return `#${mixed.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

// 0deg = 12 o'clock, positive = clockwise (matches PieChart's own arc convention).
function polarPoint(cx, cy, radius, angleDeg) {
  const angleRad = (angleDeg * Math.PI) / 180;
  return [cx + radius * Math.sin(angleRad), cy - radius * Math.cos(angleRad)];
}

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 64;
  const side = Math.min(width, height - titleHeight);
  const cx = width / 2;
  const cy = titleHeight + side / 2;
  const outerMargin = 96;
  const maxRadius = side / 2 - outerMargin;
  const innerFloor = maxRadius * 0.1;

  const maxValue = Math.max(...RAINFALL_MM);
  const radiusFor = (value) =>
    innerFloor + (value / maxValue) * (maxRadius - innerFloor);

  const sliceAngle = 360 / MONTHS.length;
  const gapDeg = 3;
  const halfWidth = (sliceAngle - gapDeg) / 2;

  // Radial gridlines — three value rings; their values are called out in a
  // corner caption rather than inline (inline labels crowd the short petals).
  const gridTicks = [1 / 3, 2 / 3, 1].map((frac) => Math.round(maxValue * frac));

  const petals = MONTHS.map((month, i) => {
    const value = RAINFALL_MM[i];
    const centerAngle = i * sliceAngle;
    return {
      type: "pie",
      id: `petal-${month}`,
      data: [
        {
          id: month,
          value: 1,
          label: `${month}: ${value} mm`,
          color: mixHex(t.seq[0], t.seq[1], value / maxValue),
        },
      ],
      cx,
      cy,
      innerRadius: 0,
      outerRadius: radiusFor(value),
      cornerRadius: 3,
      startAngle: centerAngle - halfWidth,
      endAngle: centerAngle + halfWidth,
    };
  });

  return (
    <div style={{ position: "relative", width, height }}>
      <svg width={width} height={height} style={{ position: "absolute", top: 0, left: 0 }}>
        <text x={width / 2} y={36} textAnchor="middle" fontSize={22} fontWeight={500} fill={t.ink}>
          {TITLE}
        </text>
        <text x={width - 32} y={36} textAnchor="end" fontSize={14} fill={t.inkSoft}>
          {`gridlines: ${gridTicks.join(" / ")} mm`}
        </text>

        {gridTicks.map((tick) => (
          <circle
            key={`ring-${tick}`}
            cx={cx}
            cy={cy}
            r={radiusFor(tick)}
            fill="none"
            stroke={t.grid}
            strokeWidth={1.5}
          />
        ))}

        {MONTHS.map((month, i) => {
          const [x2, y2] = polarPoint(cx, cy, maxRadius, i * sliceAngle);
          return (
            <line
              key={`spoke-${month}`}
              x1={cx}
              y1={cy}
              x2={x2}
              y2={y2}
              stroke={t.grid}
              strokeWidth={1}
            />
          );
        })}

        {MONTHS.map((month, i) => {
          const angle = i * sliceAngle;
          const [x, y] = polarPoint(cx, cy, maxRadius + 28, angle);
          const dx = x - cx;
          let anchor = "middle";
          let baseline = "middle";
          if (angle < 1 || angle > 359) {
            baseline = "auto";
          } else if (Math.abs(angle - 180) < 1) {
            baseline = "hanging";
          } else {
            anchor = dx > 0 ? "start" : "end";
          }
          return (
            <text key={`label-${month}`} x={x} y={y} textAnchor={anchor} dominantBaseline={baseline} fontSize={15} fill={t.inkSoft}>
              {month}
            </text>
          );
        })}
      </svg>

      <div style={{ position: "absolute", top: titleHeight, left: (width - side) / 2 }}>
        <PieChart
          width={side}
          height={side}
          series={petals}
          margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          legend={{ hidden: true }}
          skipAnimation
        />
      </div>
    </div>
  );
}
