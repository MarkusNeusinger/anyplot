//# anyplot-orientation: square
// anyplot.ai
// hexbin-basic: Basic Hexbin Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-25

import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const HEX_RADIUS_SHARE = 0.075; // hexagon radius as a share of the plotted half-width

// Columns: set these to your data's column names
const X = "Distance east of plaza (m)"; // role: x
const Y = "Distance north of plaza (m)"; // role: y

// Data: replace this block with your own records, one object per row
// Pedestrian GPS pings across a city district (three foot-traffic hotspots plus
// an ambient background cluster).
const data = (() => {
  function makeLcg(seed: number) {
    let state = seed >>> 0;
    return () => {
      state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
      return state / 4294967296;
    };
  }
  const rng = makeLcg(42);

  function gaussian() {
    const u1 = Math.max(rng(), 1e-9);
    const u2 = rng();
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  }

  const domainLimit = 60;
  const clusters = [
    { cx: 0, cy: 6, sx: 9, sy: 8, weight: 0.42 }, // Central Plaza
    { cx: 34, cy: -24, sx: 7, sy: 10, weight: 0.28 }, // Transit Hub
    { cx: -31, cy: 21, sx: 11, sy: 6, weight: 0.22 }, // Waterfront Promenade
    { cx: 0, cy: 0, sx: 30, sy: 26, weight: 0.08 }, // Ambient foot traffic
  ];

  const pointCount = 30000;
  const rows: { [X]: number; [Y]: number }[] = [];
  let attempts = 0;
  while (rows.length < pointCount && attempts < pointCount * 4) {
    attempts += 1;
    const r = rng();
    let acc = 0;
    let cluster = clusters[clusters.length - 1];
    for (let c = 0; c < clusters.length; c += 1) {
      acc += clusters[c].weight;
      if (r <= acc) {
        cluster = clusters[c];
        break;
      }
    }
    const x = cluster.cx + gaussian() * cluster.sx;
    const y = cluster.cy + gaussian() * cluster.sy;
    if (Math.abs(x) > domainLimit || Math.abs(y) > domainLimit) continue;
    rows.push({ [X]: x, [Y]: y });
  }
  return rows;
})();

// Plot: reads only data and the constants above
const DOMAIN = Math.ceil(
  Math.max(...data.map((d) => Math.max(Math.abs(d[X]), Math.abs(d[Y])))),
);
const HEX_RADIUS = DOMAIN * HEX_RADIUS_SHARE;
const hexDx = HEX_RADIUS * Math.sqrt(3);
const hexDy = HEX_RADIUS * 1.5;

function hexBin(rawPoints: typeof data) {
  const binsById = new Map<
    string,
    { id: string; cx: number; cy: number; count: number }
  >();
  rawPoints.forEach((row) => {
    const px = row[X];
    const py = row[Y];
    const py1 = py / hexDy;
    let pj = Math.round(py1);
    const px1 = px / hexDx - (pj & 1) / 2;
    let pi = Math.round(px1);
    const py2 = py1 - pj;
    if (Math.abs(py2) * 3 > 1) {
      const px2 = px1 - pi;
      const pi2 = pi + (px1 < pi ? -1 : 1) / 2;
      const pj2 = pj + (py1 < pj ? -1 : 1);
      const px3 = px1 - pi2;
      const py3 = py2 - pj2;
      if (px2 * px2 + py2 * py2 > px3 * px3 + py3 * py3) {
        pi = pi2 + (pj & 1 ? 1 : -1) / 2;
        pj = pj2;
      }
    }
    const id = `${pi}-${pj}`;
    const existing = binsById.get(id);
    if (existing) {
      existing.count += 1;
    } else {
      binsById.set(id, {
        id,
        cx: (pi + (pj & 1) / 2) * hexDx,
        cy: pj * hexDy,
        count: 1,
      });
    }
  });
  return Array.from(binsById.values());
}

const hexBins = hexBin(data);
const binCountMax = Math.max(...hexBins.map((b) => b.count));
const binCountMin = Math.min(...hexBins.map((b) => b.count));

// Color on a log scale so both dense cores and sparse fringes remain distinct.
const colorDomainMin = Math.log1p(binCountMin);
const colorDomainMax = Math.log1p(binCountMax);

function mixHex(hexA: string, hexB: string, ratio: number) {
  const a = parseInt(hexA.slice(1), 16);
  const b = parseInt(hexB.slice(1), 16);
  const channel = (shift: number) => {
    const av = (a >> shift) & 255;
    const bv = (b >> shift) & 255;
    return Math.round(av + (bv - av) * Math.min(1, Math.max(0, ratio)));
  };
  return `#${[16, 8, 0].map((shift) => channel(shift).toString(16).padStart(2, "0")).join("")}`;
}

function logSequentialColor(ratio: number) {
  const count = binCountMin + ratio * (binCountMax - binCountMin);
  const logRatio =
    (Math.log1p(count) - colorDomainMin) /
    (colorDomainMax - colorDomainMin || 1);
  return mixHex(t.seq[0], t.seq[1], logRatio);
}

function fullHexGrid() {
  const cells: { id: string; cx: number; cy: number }[] = [];
  const rowPad = 1;
  const pjMin = Math.floor(-DOMAIN / hexDy) - rowPad;
  const pjMax = Math.ceil(DOMAIN / hexDy) + rowPad;
  for (let pj = pjMin; pj <= pjMax; pj += 1) {
    const offset = (pj & 1) / 2;
    const piMin = Math.floor(-DOMAIN / hexDx - offset) - rowPad;
    const piMax = Math.ceil(DOMAIN / hexDx - offset) + rowPad;
    for (let pi = piMin; pi <= piMax; pi += 1) {
      const cx = (pi + (pj & 1) / 2) * hexDx;
      const cy = pj * hexDy;
      if (Math.abs(cx) > DOMAIN + HEX_RADIUS || Math.abs(cy) > DOMAIN + HEX_RADIUS) continue;
      cells.push({ id: `${pi}-${pj}`, cx, cy });
    }
  }
  return cells;
}

const occupiedById = new Map(hexBins.map((bin) => [bin.id, bin]));
const hexBinPoints = fullHexGrid().map((cell) => {
  const occupied = occupiedById.get(cell.id);
  const count = occupied ? occupied.count : 0;
  return {
    id: cell.id,
    x: cell.cx,
    y: cell.cy,
    z: count > 0 ? count : binCountMin,
    isEmpty: count === 0,
  };
});

function HexCell(props: any) {
  const { series, xScale, yScale, colorGetter, color } = props;
  const radiusX = Math.abs(xScale(HEX_RADIUS) - xScale(0));
  const radiusY = Math.abs(yScale(HEX_RADIUS) - yScale(0));

  const [xr0, xr1] = xScale.range();
  const [yr0, yr1] = yScale.range();
  const clipX = Math.min(xr0, xr1);
  const clipY = Math.min(yr0, yr1);
  const clipWidth = Math.abs(xr1 - xr0);
  const clipHeight = Math.abs(yr1 - yr0);

  return (
    <g clipPath="url(#hexbin-plot-clip)">
      <defs>
        <clipPath id="hexbin-plot-clip">
          <rect x={clipX} y={clipY} width={clipWidth} height={clipHeight} />
        </clipPath>
      </defs>
      {series.data.map((point: any, i: number) => {
        const ccx = xScale(point.x);
        const ccy = yScale(point.y);
        let d = "";
        for (let k = 0; k < 6; k += 1) {
          const angle = (k * Math.PI) / 3;
          const vx = ccx + Math.sin(angle) * radiusX;
          const vy = ccy - Math.cos(angle) * radiusY;
          d += `${k === 0 ? "M" : "L"}${vx},${vy}`;
        }
        return (
          <path
            key={point.id}
            d={`${d}Z`}
            fill={point.isEmpty ? t.seq[0] : colorGetter ? colorGetter(i) : color}
            fillOpacity={point.isEmpty ? 0.12 : 1}
            stroke={t.pageBg}
            strokeWidth={1}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 70;
  const captionHeight = 56;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Typography
        sx={{
          color: t.ink,
          fontSize: 26,
          fontWeight: 600,
          textAlign: "center",
          lineHeight: 1.2,
          pt: "18px",
          height: titleHeight,
          fontFamily: "inherit",
        }}
      >
        hexbin-basic · javascript · muix · anyplot.ai
      </Typography>
      <ScatterChart
        width={width}
        height={height - titleHeight - captionHeight}
        skipAnimation
        disableHitArea
        series={[
          {
            id: "hex-density",
            type: "scatter",
            data: hexBinPoints,
            label: "Ping count",
            zAxisId: "count",
          },
        ]}
        xAxis={[
          {
            height: 68,
            scaleType: "linear",
            min: -DOMAIN,
            max: DOMAIN,
            label: X,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            width: 88,
            scaleType: "linear",
            min: -DOMAIN,
            max: DOMAIN,
            label: Y,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        zAxis={[
          {
            id: "count",
            min: binCountMin,
            max: binCountMax,
            colorMap: {
              type: "continuous",
              min: binCountMin,
              max: binCountMax,
              color: logSequentialColor,
            },
          },
        ]}
        margin={{ top: 30, right: 134, bottom: 24, left: 80 }}
        slots={{ scatter: HexCell, legend: ContinuousColorLegend }}
        slotProps={{
          legend: {
            axisId: "count",
            axisDirection: "z",
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            thickness: 16,
            sx: {
              width: "45%",
              color: t.inkSoft,
              fontSize: 14,
              fontFamily: "inherit",
            },
          } as any,
        }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      />
      <Typography
        sx={{
          height: captionHeight,
          pt: "6px",
          textAlign: "center",
          color: t.inkSoft,
          fontSize: 14,
          fontFamily: "inherit",
        }}
      >
        Ping count per bin (log scale)
      </Typography>
    </Box>
  );
}
