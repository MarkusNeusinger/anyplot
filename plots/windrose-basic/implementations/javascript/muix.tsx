// anyplot.ai
// windrose-basic: Wind Rose Chart
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 92/100 | Created: 2026-08-05
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// The 16-point compass, clockwise from north; each sector is centred on its point.
const COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
const SPEED_BINS = 4; // speed classes, few enough that neighbouring ramp steps stay apart; the last one is open-ended
const TOP_BIN_QUANTILE = 0.9; // the open-ended class starts near this quantile of the speeds
const RING_COUNT = 4; // about this many frequency rings
const NICE_STEPS = [1, 2, 2.5, 5, 10]; // round step multipliers for bin widths and rings
const SECTOR_GAP_DEG = 1.4; // gap between neighbouring spokes
const LABEL_BAND = 48; // px between the outer ring and the compass labels' edge
const TITLE = "windrose-basic · javascript · muix · anyplot.ai";
const TITLE_H = 80;
const LEGEND_H = 64;

// Columns: set these to your data's column names
const DIRECTION = "Wind direction (°)"; // role: direction
const SPEED = "Wind speed (m/s)"; // role: speed

// Data: replace this block with your own records, one object per row
// Half a year of hourly readings at a coastal weather station: a prevailing
// south-westerly, a brisk north-westerly regime and light winds from anywhere.
const data = (() => {
  let a = 42;
  const rand = () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let x = Math.imul(a ^ (a >>> 15), 1 | a);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
  const normal = () => Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-6))) * Math.cos(2 * Math.PI * rand());
  return Array.from({ length: 4380 }, () => {
    const regime = rand();
    let direction;
    let scale;
    if (regime < 0.6) {
      direction = 225 + normal() * 36;
      scale = 3.4;
    } else if (regime < 0.78) {
      direction = 315 + normal() * 24;
      scale = 3.0;
    } else {
      direction = rand() * 360;
      scale = 1.7;
    }
    const speed = -Math.log(1 - rand()) * scale;
    return {
      [DIRECTION]: Math.round((((direction % 360) + 360) % 360) * 10) / 10,
      [SPEED]: Math.round(speed * 100) / 100,
    };
  });
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[DIRECTION] != null && d[SPEED] != null);
const n = rows.length;
const SECTOR_DEG = 360 / COMPASS.length;
const SPEED_UNIT = SPEED.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";

// Speed classes of one round width, chosen so the open-ended top class starts
// near the TOP_BIN_QUANTILE of the observed speeds.
const sortedSpeeds = rows.map((d) => d[SPEED]).sort((x, y) => x - y);
const rawStep = sortedSpeeds[Math.floor(TOP_BIN_QUANTILE * (n - 1))] / (SPEED_BINS - 1);
const stepMagnitude = 10 ** Math.floor(Math.log10(rawStep));
const speedStep = NICE_STEPS.map((m) => m * stepMagnitude).find((s) => s >= rawStep);
const binStarts = Array.from({ length: SPEED_BINS }, (_, i) => i * speedStep);
const binLabels = binStarts.map((lo, i) =>
  i < SPEED_BINS - 1 ? `${lo}–${lo + speedStep} ${SPEED_UNIT}` : `≥ ${lo} ${SPEED_UNIT}`,
);

// Share of all observations (%) per compass sector and speed class
const counts = COMPASS.map(() => binStarts.map(() => 0));
rows.forEach((d) => {
  const sector = Math.round((((d[DIRECTION] % 360) + 360) % 360) / SECTOR_DEG) % COMPASS.length;
  const bin = Math.min(SPEED_BINS - 1, Math.floor(d[SPEED] / speedStep));
  counts[sector][bin] += 1;
});
const pct = counts.map((row) => row.map((c) => (c / n) * 100));
const cumulative = pct.map((row) => row.map((_, i) => row.slice(0, i + 1).reduce((x, y) => x + y, 0)));
const totals = cumulative.map((row) => row[row.length - 1]);
const maxTotal = Math.max(...totals);
const rawRing = maxTotal / RING_COUNT;
const ringMagnitude = 10 ** Math.floor(Math.log10(rawRing));
const ringStep = NICE_STEPS.map((m) => m * ringMagnitude).find((s) => s >= rawRing);
const ringMax = ringStep * Math.ceil(maxTotal / ringStep);
const rings = Array.from({ length: Math.round(ringMax / ringStep) }, (_, i) => (i + 1) * ringStep);

// Calm to strong along the Imprint sequential ramp
const seqRgb = t.seq.map((hex) => [1, 3, 5].map((k) => parseInt(hex.slice(k, k + 2), 16)));
const binColors = binStarts.map(
  (_, i) =>
    `rgb(${seqRgb[0].map((c, k) => Math.round(c + ((seqRgb[1][k] - c) * i) / (SPEED_BINS - 1))).join(",")})`,
);

// Wedges in unit radii (share of the outer ring) and SVG angles (0 at 3 o'clock)
const toSvg = Math.PI / 180;
const wedges = COMPASS.flatMap((_, s) =>
  binStarts.map((_, b) => ({
    key: `${s}-${b}`,
    color: binColors[b],
    inner: (cumulative[s][b] - pct[s][b]) / ringMax,
    outer: cumulative[s][b] / ringMax,
    a0: ((s - 0.5) * SECTOR_DEG + SECTOR_GAP_DEG / 2 - 90) * toSvg,
    a1: ((s + 0.5) * SECTOR_DEG - SECTOR_GAP_DEG / 2 - 90) * toSvg,
  })),
).filter((w) => w.outer > w.inner);
// Ring labels run along the sector boundary whose two neighbours hold the fewest observations
const quietBoundary = COMPASS.reduce(
  (best, _, s) => (totals[s] + totals[(s + 1) % COMPASS.length] < totals[best] + totals[(best + 1) % COMPASS.length] ? s : best),
  0,
);
const ringAngle = ((quietBoundary + 0.5) * SECTOR_DEG - 90) * toSvg;
const SUBTITLE = `${n.toLocaleString("en-US")} observations · ${COMPASS.length} sectors of ${SECTOR_DEG}° · spoke length: share of all observations (%)`;

// The community package has no polar bar chart: a custom layer maps the stacked
// sectors onto the chart's drawing area.
function WindRoseLayer() {
  const { left, top, width, height } = useDrawingArea();
  const cx = left + width / 2;
  const cy = top + height / 2;
  const R = Math.min(width, height) / 2 - LABEL_BAND;

  return (
    <g>
      {rings.map((level) => (
        <circle key={`ring-${level}`} cx={cx} cy={cy} r={(level / ringMax) * R} fill="none" stroke={t.grid} strokeWidth={1.25} />
      ))}
      {wedges.map((w) => (
        <path
          key={w.key}
          d={`M ${cx + w.outer * R * Math.cos(w.a0)} ${cy + w.outer * R * Math.sin(w.a0)} A ${w.outer * R} ${w.outer * R} 0 0 1 ${cx + w.outer * R * Math.cos(w.a1)} ${cy + w.outer * R * Math.sin(w.a1)} L ${cx + w.inner * R * Math.cos(w.a1)} ${cy + w.inner * R * Math.sin(w.a1)} A ${w.inner * R} ${w.inner * R} 0 0 0 ${cx + w.inner * R * Math.cos(w.a0)} ${cy + w.inner * R * Math.sin(w.a0)} Z`}
          fill={w.color}
          stroke={t.pageBg}
          strokeWidth={1}
        />
      ))}
      {rings.map((level) => (
        <text
          key={`ring-label-${level}`}
          x={cx + (level / ringMax) * R * Math.cos(ringAngle)}
          y={cy + (level / ringMax) * R * Math.sin(ringAngle)}
          dx={4}
          dy={-4}
          fontSize={15}
          fill={t.inkSoft}
          stroke={t.pageBg}
          strokeWidth={4}
          paintOrder="stroke"
        >
          {`${level} %`}
        </text>
      ))}
      {COMPASS.map((point, s) => {
        const a = (s * SECTOR_DEG - 90) * toSvg;
        const cos = Math.cos(a);
        const sin = Math.sin(a);
        const rank = s % 4 === 0 ? 0 : s % 2 === 0 ? 1 : 2; // cardinal, intercardinal, secondary
        return (
          <text
            key={`label-${point}`}
            x={cx + (R + 14) * cos}
            y={cy + (R + 14) * sin}
            textAnchor={cos > 0.15 ? "start" : cos < -0.15 ? "end" : "middle"}
            dominantBaseline={sin > 0.5 ? "hanging" : sin < -0.5 ? "auto" : "central"}
            fontSize={[16, 15, 14][rank]}
            fontWeight={[700, 600, 400][rank]}
            fill={rank < 2 ? t.ink : t.inkSoft}
          >
            {point}
          </text>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, paddingTop: 18, boxSizing: "border-box", textAlign: "center" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H - LEGEND_H}
        series={[]}
        skipAnimation
        margin={{ top: 16, right: 24, bottom: 8, left: 24 }}
      >
        <WindRoseLayer />
      </ChartsContainer>
      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 26,
        }}
      >
        <span style={{ fontSize: 16, fontWeight: 600, color: t.ink }}>{SPEED}</span>
        {binLabels.map((label, i) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 18, height: 18, borderRadius: 3, background: binColors[i], display: "inline-block" }} />
            <span style={{ fontSize: 16, color: t.ink }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
