// anyplot.ai
// violin-swarm: Violin Plot with Overlaid Swarm Points
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (LCG) + Box-Muller for reproducible normal samples --
let seed = 42;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randomNormal(mean, stdDev) {
  const u1 = lcgRandom() || 1e-9;
  const u2 = lcgRandom();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

// --- Data: reaction times (ms) across 4 caffeine dosage conditions ---------
const categories = ["Placebo", "Low Dose", "Medium Dose", "High Dose"];
const samplesByCategory = [
  Array.from({ length: 55 }, () => randomNormal(340, 40)),
  // bimodal: a subset of subjects respond strongly to the low dose
  Array.from({ length: 60 }, (_, i) =>
    i % 3 === 0 ? randomNormal(320, 28) : randomNormal(255, 24)
  ),
  Array.from({ length: 48 }, () => randomNormal(252, 32)),
  Array.from({ length: 65 }, () => randomNormal(205, 22)),
];

// --- Kernel density estimation (Gaussian kernel, Silverman bandwidth) ------
function mean(values) {
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}
function stdDev(values) {
  const m = mean(values);
  return Math.sqrt(mean(values.map((v) => (v - m) ** 2)));
}
function quantile(sortedValues, q) {
  const pos = (sortedValues.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  return sortedValues[base + 1] !== undefined
    ? sortedValues[base] + rest * (sortedValues[base + 1] - sortedValues[base])
    : sortedValues[base];
}
function silvermanBandwidth(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const spread = Math.min(
    stdDev(values),
    (quantile(sorted, 0.75) - quantile(sorted, 0.25)) / 1.34
  );
  return 0.9 * (spread || stdDev(values)) * Math.pow(values.length, -0.2);
}
function gaussianKde(values, bandwidth) {
  return (y) => {
    const sum = values.reduce((acc, v) => {
      const u = (y - v) / bandwidth;
      return acc + Math.exp(-0.5 * u * u);
    }, 0);
    return sum / (values.length * bandwidth * Math.sqrt(2 * Math.PI));
  };
}

// --- Violin geometry: one density profile per category, normalized width --
const GRID_POINTS = 80;
const MAX_HALF_WIDTH = 0.38;

const violins = categories.map((category, index) => {
  const values = samplesByCategory[index];
  const bandwidth = silvermanBandwidth(values);
  const yMin = Math.min(...values) - 2.5 * bandwidth;
  const yMax = Math.max(...values) + 2.5 * bandwidth;
  const density = gaussianKde(values, bandwidth);
  const grid = Array.from(
    { length: GRID_POINTS },
    (_, i) => yMin + (i / (GRID_POINTS - 1)) * (yMax - yMin)
  );
  const densities = grid.map(density);
  const maxDensity = Math.max(...densities);
  const halfWidths = densities.map((d) => (d / maxDensity) * MAX_HALF_WIDTH);
  return { category, index, values, grid, halfWidths };
});

function halfWidthAt(violin, y) {
  const { grid, halfWidths } = violin;
  if (y <= grid[0]) return halfWidths[0];
  if (y >= grid[grid.length - 1]) return halfWidths[halfWidths.length - 1];
  for (let i = 0; i < grid.length - 1; i++) {
    if (y >= grid[i] && y <= grid[i + 1]) {
      const frac = (y - grid[i]) / (grid[i + 1] - grid[i]);
      return halfWidths[i] + frac * (halfWidths[i + 1] - halfWidths[i]);
    }
  }
  return 0;
}

// --- Swarm layout: bin observations along y, spread them within the local -
// --- violin half-width so points never spill past the density outline -----
const SWARM_BINS = 28;
const MAX_POINT_SPACING = 0.045;

function beeswarmOffsets(violin) {
  const { values, grid } = violin;
  const yMin = grid[0];
  const yMax = grid[grid.length - 1];
  const binWidth = (yMax - yMin) / SWARM_BINS;
  const bins = Array.from({ length: SWARM_BINS }, () => []);
  values
    .map((_, i) => i)
    .sort((a, b) => values[a] - values[b])
    .forEach((i) => {
      const binIndex = Math.min(
        SWARM_BINS - 1,
        Math.max(0, Math.floor((values[i] - yMin) / binWidth))
      );
      bins[binIndex].push(i);
    });
  const offsets = new Array(values.length).fill(0);
  bins.forEach((indices, binIndex) => {
    const count = indices.length;
    if (count === 0) return;
    const binCenterY = yMin + (binIndex + 0.5) * binWidth;
    const spacing = Math.min(MAX_POINT_SPACING, (2 * halfWidthAt(violin, binCenterY)) / count);
    indices.forEach((valueIndex, k) => {
      offsets[valueIndex] = (k - (count - 1) / 2) * spacing;
    });
  });
  return offsets;
}

violins.forEach((violin) => {
  violin.offsets = beeswarmOffsets(violin);
});

// --- Series data --------------------------------------------------------
const violinOutlines = violins.map((violin) => {
  const points = [];
  for (let i = 0; i < violin.grid.length; i++) {
    points.push([violin.index + violin.halfWidths[i], violin.grid[i]]);
  }
  for (let i = violin.grid.length - 1; i >= 0; i--) {
    points.push([violin.index - violin.halfWidths[i], violin.grid[i]]);
  }
  return points;
});

const swarmPoints = violins.flatMap((violin) =>
  violin.values.map((value, i) => [violin.index + violin.offsets[i], value])
);

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function renderViolin(params, api) {
  const points = violinOutlines[params.dataIndex].map((p) => api.coord(p));
  return {
    type: "polygon",
    shape: { points },
    style: {
      fill: hexToRgba(t.palette[0], 0.4),
      stroke: t.palette[0],
      lineWidth: 1.5,
    },
  };
}

// --- Chart ----------------------------------------------------------------
const titleText = "Reaction Time by Caffeine Dose · violin-swarm · javascript · echarts · anyplot.ai";
const titleFontSize =
  titleText.length > 67 ? Math.max(14, Math.round(22 * (67 / titleText.length))) : 22;

const chart = echarts.init(document.getElementById("container"));
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  color: t.palette,
  title: {
    text: titleText,
    left: "center",
    top: 18,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  legend: {
    top: 60,
    left: "center",
    itemWidth: 18,
    itemHeight: 12,
    textStyle: { color: t.inkSoft, fontSize: 15 },
    data: ["Density", "Observations"],
  },
  grid: { left: 100, right: 60, top: 130, bottom: 90 },
  xAxis: {
    type: "value",
    min: -0.65,
    max: categories.length - 1 + 0.65,
    axisLabel: {
      customValues: categories.map((_, i) => i),
      formatter: (val) => categories[val],
      color: t.inkSoft,
      fontSize: 16,
    },
    axisTick: { customValues: categories.map((_, i) => i) },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
    name: "Experimental Condition",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 18 },
  },
  yAxis: {
    type: "value",
    name: "Reaction Time (ms)",
    nameLocation: "middle",
    nameGap: 65,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { onZero: false, lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Density",
      type: "custom",
      coordinateSystem: "cartesian2d",
      xAxisIndex: 0,
      yAxisIndex: 0,
      renderItem: renderViolin,
      data: categories.map((_, i) => i),
      itemStyle: { color: hexToRgba(t.palette[0], 0.6) },
      clip: true,
      silent: true,
      z: 2,
    },
    {
      name: "Observations",
      type: "scatter",
      data: swarmPoints,
      symbolSize: 9,
      itemStyle: {
        color: t.palette[1],
        opacity: 0.85,
        borderColor: t.pageBg,
        borderWidth: 1,
      },
      z: 3,
    },
  ],
});
