// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: chartjs 4.6.1 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Constants
const TARGET_LEVELS = 14; // about this many evenly stepped isolines across the field's range
const REFINE = 4; // interpolated steps per grid cell, so isolines and band edges curve between grid nodes

// Columns: set these to your data's column names
const X = "Easting (km)"; // role: x
const Y = "Northing (km)"; // role: y
const Z = "Elevation anomaly (m)"; // role: z

// Data: replace this block with your own records, one object per grid point
// Terrain elevation anomaly over a 6 km x 6 km survey area, modeled by the "peaks" surface on a 70 x 70 grid
const N = 70;
const RANGE = 3;
const data = [];
for (let i = 0; i < N; i++) {
  for (let j = 0; j < N; j++) {
    const x = -RANGE + (2 * RANGE * i) / (N - 1);
    const y = -RANGE + (2 * RANGE * j) / (N - 1);
    const z =
      3 * (1 - x) ** 2 * Math.exp(-(x ** 2) - (y + 1) ** 2) -
      10 * (x / 5 - x ** 3 - y ** 5) * Math.exp(-(x ** 2) - y ** 2) -
      (1 / 3) * Math.exp(-((x + 1) ** 2) - y ** 2);
    data.push({ [X]: x, [Y]: y, [Z]: z });
  }
}

// Plot: reads only data and the constants above
// Pivot the records into a grid: grid[i][j] is z at (xs[i], ys[j])
const xs = [...new Set(data.map((d) => d[X]))].sort((a, b) => a - b);
const ys = [...new Set(data.map((d) => d[Y]))].sort((a, b) => a - b);
const xIndex = new Map(xs.map((v, i) => [v, i]));
const yIndex = new Map(ys.map((v, j) => [v, j]));
const grid = xs.map(() => ys.map(() => NaN));
for (const d of data) grid[xIndex.get(d[X])][yIndex.get(d[Y])] = d[Z];
const zFinite = data.map((d) => d[Z]).filter(Number.isFinite);
const zMin = zFinite.reduce((a, b) => Math.min(a, b));
const zMax = zFinite.reduce((a, b) => Math.max(a, b));

// Catmull-Rom refinement along x, then along y (linear phantom nodes at the ends); each pass refines the
// columns of the current matrix and stores them as rows, so two passes return fine[i][j] on the refined grid
let fine = grid;
for (let pass = 0; pass < 2; pass++) {
  fine = fine[0].map((_, j) => {
    const line = fine.map((row) => row[j]);
    const n = line.length;
    const at = (k) => (k < 0 ? 2 * line[0] - line[1] : k >= n ? 2 * line[n - 1] - line[n - 2] : line[k]);
    const out = [];
    for (let k = 0; k < n - 1; k++) {
      const [p0, p1, p2, p3] = [at(k - 1), at(k), at(k + 1), at(k + 2)];
      for (let s = 0; s < REFINE; s++) {
        const u = s / REFINE;
        out.push(p1 + 0.5 * u * (p2 - p0 + u * (2 * p0 - 5 * p1 + 4 * p2 - p3 + u * (3 * (p1 - p2) + p3 - p0))));
      }
    }
    out.push(line[n - 1]);
    return out;
  });
}
// The refined nodes sit at even steps between neighbouring grid coordinates
const [fineXs, fineYs] = [xs, ys].map((coords) =>
  coords.flatMap((v, k) =>
    k < coords.length - 1 ? Array.from({ length: REFINE }, (_, s) => v + (s / REFINE) * (coords[k + 1] - v)) : [v],
  ),
);

// Evenly stepped levels at a round step (1, 2, 2.5 or 5 times a power of ten)
const rawStep = (zMax - zMin) / TARGET_LEVELS;
const magnitude = 10 ** Math.floor(Math.log10(rawStep));
const step = [1, 2, 2.5, 5, 10]
  .map((m) => m * magnitude)
  .reduce((best, s) => (Math.abs(s - rawStep) < Math.abs(best - rawStep) ? s : best));
const levels = [];
for (let k = Math.ceil(zMin / step); k * step <= zMax; k++) levels.push(Number((k * step).toFixed(10)));

// Imprint colormap: imprint_div centered on zero for a two-signed field, imprint_seq otherwise
const hexToRgb = (hex) => [1, 3, 5].map((o) => parseInt(hex.slice(o, o + 2), 16));
const mix = (a, b, f) => a.map((v, c) => Math.round(v + (b[c] - v) * Math.max(0, Math.min(1, f))));
const [divLow, divMid, divHigh] = t.div.map(hexToRgb);
const [seqLow, seqHigh] = t.seq.map(hexToRgb);
const colorAt = (z) =>
  zMin < 0 && zMax > 0
    ? z < 0
      ? mix(divMid, divLow, z / zMin)
      : mix(divMid, divHigh, z / zMax)
    : mix(seqLow, seqHigh, (z - zMin) / (zMax - zMin));
// Band k lies between levels[k - 1] and levels[k]; band 0 sits below the lowest level
const bandOf = (z) => Math.min(levels.length, Math.max(0, Math.floor((z - levels[0]) / step) + 1));
const bandRgb = Array.from({ length: levels.length + 1 }, (_, k) =>
  colorAt(Math.min(zMax, Math.max(zMin, levels[0] + (k - 0.5) * step))),
);

// Isolines by marching squares on the refined grid; a saddle cell is resolved by its center value
const [inkR, inkG, inkB] = hexToRgb(t.ink);
const datasets = levels.map((level) => {
  const points = [];
  for (let i = 0; i < fineXs.length - 1; i++) {
    for (let j = 0; j < fineYs.length - 1; j++) {
      const corners = [
        [i, j],
        [i + 1, j],
        [i + 1, j + 1],
        [i, j + 1],
      ];
      const zs = corners.map(([a, b]) => fine[a][b]);
      const above = zs.map((z) => z >= level);
      if (!zs.every(Number.isFinite) || above.every((v) => v === above[0])) continue;
      const crossings = [];
      for (let e = 0; e < 4; e++) {
        const f = (e + 1) % 4;
        if (above[e] === above[f]) continue;
        const s = (level - zs[e]) / (zs[f] - zs[e]);
        const [[ia, ja], [ib, jb]] = [corners[e], corners[f]];
        crossings.push({
          x: fineXs[ia] + s * (fineXs[ib] - fineXs[ia]),
          y: fineYs[ja] + s * (fineYs[jb] - fineYs[ja]),
        });
      }
      const centerAbove = zs.reduce((a, b) => a + b) / 4 >= level;
      const pairs =
        crossings.length === 2 ? [[0, 1]] : centerAbove === above[0] ? [[0, 1], [2, 3]] : [[3, 0], [1, 2]];
      for (const [a, b] of pairs) points.push(crossings[a], crossings[b], { x: null, y: null });
    }
  }
  return {
    label: String(level),
    data: points,
    showLine: true,
    // A tension routes the path through Chart.js's bezier drawing, which keeps sub-pixel positions; the default
    // straight-line path merges points per whole pixel column and steps steep isolines. Two-point segments stay straight.
    tension: 0.5,
    borderColor: `rgba(${inkR},${inkG},${inkB},0.5)`,
    borderWidth: 1.25,
    borderCapStyle: "round",
    pointRadius: 0,
    pointHoverRadius: 0,
    pointHitRadius: 6,
  };
});

// Filled bands: each device pixel of the plot area takes the band of the bilinearly sampled refined field
let bandImage = null;
const bandFillPlugin = {
  id: "bandFill",
  beforeDatasetsDraw(chart) {
    const { ctx, chartArea: ca, scales } = chart;
    const dpr = chart.currentDevicePixelRatio;
    const w = Math.round((ca.right - ca.left) * dpr);
    const h = Math.round((ca.bottom - ca.top) * dpr);
    if (!bandImage || bandImage.width !== w || bandImage.height !== h) {
      bandImage = ctx.createImageData(w, h);
      // Fractional refined-grid index of every pixel column and row (-1 outside the grid), by binary search
      const [cols, rows] = [
        [fineXs, w, scales.x, ca.left],
        [fineYs, h, scales.y, ca.top],
      ].map(([coords, count, scale, start]) =>
        Array.from({ length: count }, (_, k) => {
          const v = scale.getValueForPixel(start + (k + 0.5) / dpr);
          if (!(v >= coords[0] && v <= coords[coords.length - 1])) return -1;
          let lo = 0;
          let hi = coords.length - 1;
          while (hi - lo > 1) {
            const mid = (lo + hi) >> 1;
            if (coords[mid] <= v) lo = mid;
            else hi = mid;
          }
          return lo + (v - coords[lo]) / (coords[hi] - coords[lo]);
        }),
      );
      for (let r = 0; r < h; r++) {
        if (rows[r] < 0) continue;
        const j = Math.min(Math.floor(rows[r]), fineYs.length - 2);
        const b = rows[r] - j;
        for (let c = 0; c < w; c++) {
          if (cols[c] < 0) continue;
          const i = Math.min(Math.floor(cols[c]), fineXs.length - 2);
          const a = cols[c] - i;
          const z =
            (1 - a) * (1 - b) * fine[i][j] + a * (1 - b) * fine[i + 1][j] + (1 - a) * b * fine[i][j + 1] + a * b * fine[i + 1][j + 1];
          if (!Number.isFinite(z)) continue;
          const o = (r * w + c) * 4;
          bandImage.data.set(bandRgb[bandOf(z)], o);
          bandImage.data[o + 3] = 255;
        }
      }
    }
    ctx.putImageData(bandImage, Math.round(ca.left * dpr), Math.round(ca.top * dpr));
  },
};

// Color bar: the same bands as the plot, a tick at every isoline level, the quantity as its title
const colorBarPlugin = {
  id: "colorBar",
  afterDraw(chart) {
    const { ctx, chartArea: ca } = chart;
    const barX = ca.right + 28;
    const barW = 26;
    const toY = (z) => ca.bottom - ((z - zMin) / (zMax - zMin)) * (ca.bottom - ca.top);
    const edges = [zMin, ...levels, zMax];
    ctx.save();
    for (let k = 0; k < edges.length - 1; k++) {
      ctx.fillStyle = `rgb(${bandRgb[k].join(",")})`;
      ctx.fillRect(barX, toY(edges[k + 1]), barW, toY(edges[k]) - toY(edges[k + 1]));
    }
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1;
    ctx.strokeRect(barX, ca.top, barW, ca.bottom - ca.top);
    ctx.fillStyle = t.inkSoft;
    ctx.font = "14px sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    for (const level of levels) {
      const y = toY(level);
      ctx.beginPath();
      ctx.moveTo(barX + barW, y);
      ctx.lineTo(barX + barW + 6, y);
      ctx.stroke();
      ctx.fillText(String(level), barX + barW + 10, y);
    }
    ctx.fillStyle = t.ink;
    ctx.font = "16px sans-serif";
    ctx.textAlign = "center";
    ctx.translate(barX + barW + 54, (ca.top + ca.bottom) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(Z, 0, 0);
    ctx.restore();
  },
};

const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

new Chart(canvas, {
  type: "scatter",
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 42, right: 136, bottom: 42, left: 8 } },
    interaction: { mode: "nearest", intersect: true },
    plugins: {
      title: {
        display: true,
        text: "contour-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "bold" },
        padding: { top: 12, bottom: 18 },
      },
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: () => "",
          label: (item) => `${Z} = ${item.dataset.label}`,
        },
      },
    },
    // The band fill covers the plot area, so grid lines are off and the axis lines draw above the datasets
    scales: {
      x: {
        type: "linear",
        min: xs[0],
        max: xs[xs.length - 1],
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        border: { color: t.inkSoft, z: 1 },
        title: { display: true, text: X, color: t.ink, font: { size: 16 } },
      },
      y: {
        type: "linear",
        min: ys[0],
        max: ys[ys.length - 1],
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        border: { color: t.inkSoft, z: 1 },
        title: { display: true, text: Y, color: t.ink, font: { size: 16 } },
      },
    },
  },
  plugins: [bandFillPlugin, colorBarPlugin],
});
