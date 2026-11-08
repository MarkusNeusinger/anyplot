// anyplot.ai
// line-3d-trajectory: 3D Line Plot for Trajectory Visualization
// Library: chartjs 4.6.1 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const X = "X position (1000 km)"; // role: x
const Y = "Y position (1000 km)"; // role: y
const Z = "Altitude (1000 km)"; // role: z
const ELAPSED = "Elapsed time (h)"; // role: color

// Data: replace this block with your own records, one object per row
// A decaying satellite orbit spiraling inward and down toward re-entry
const POINT_COUNT = 260;
const REVOLUTIONS = 3.5;
const DURATION_H = 18;
const data = [];
for (let i = 0; i < POINT_COUNT; i++) {
  const progress = i / (POINT_COUNT - 1);
  const angle = progress * REVOLUTIONS * 2 * Math.PI;
  const radius = 6.4 - 5.2 * progress;
  data.push({
    [X]: radius * Math.cos(angle),
    [Y]: radius * Math.sin(angle),
    [Z]: 5.5 * Math.pow(1 - progress, 1.3),
    [ELAPSED]: progress * DURATION_H,
  });
}

// Plot: reads only data and the constants above
// Chart.js has no 3D chart type, so every (x, y, z) point is projected onto the 2D canvas with an
// orthographic camera; dragging changes the camera angles and the wheel zooms, both re-projecting.
const AXIS_COLUMNS = [X, Y, Z];
const extent = AXIS_COLUMNS.map((col) => {
  const values = data.map((d) => d[col]).filter(Number.isFinite);
  return [Math.min(...values), Math.max(...values)];
});
const center = extent.map(([lo, hi]) => (lo + hi) / 2);
const rawStep = Math.max(...extent.map(([lo, hi]) => hi - lo)) / 8;
const magnitude = 10 ** Math.floor(Math.log10(rawStep));
const tickStep = [1, 2, 5, 10].map((m) => m * magnitude).find((s) => s >= rawStep);
const times = data.map((d) => d[ELAPSED]);
const [timeLow, timeHigh] = [Math.min(...times), Math.max(...times)];
const seqRgb = t.seq.map((hex) => [16, 8, 0].map((shift) => (parseInt(hex.slice(1), 16) >> shift) & 255));

const camera = { azimuth: Math.PI / 4, elevation: Math.PI / 5.5, zoom: 1 };

// Screen x, screen y, and depth (larger = nearer the viewer) of a point in data units
function project([x, y, z]) {
  const [dx, dy, dz] = [x - center[0], y - center[1], z - center[2]];
  const across = dx * Math.cos(camera.azimuth) - dy * Math.sin(camera.azimuth);
  const toward = dx * Math.sin(camera.azimuth) + dy * Math.cos(camera.azimuth);
  return {
    x: across,
    y: dz * Math.cos(camera.elevation) - toward * Math.sin(camera.elevation),
    depth: toward * Math.cos(camera.elevation) + dz * Math.sin(camera.elevation),
  };
}

// Three axes leave the floor corner farthest from the viewer, each spanning its column's data range
function buildAxes() {
  const corners = [0, 1].flatMap((i) => [0, 1].map((j) => [extent[0][i], extent[1][j], extent[2][0]]));
  const back = corners.reduce((a, b) => (project(a).depth < project(b).depth ? a : b));
  return AXIS_COLUMNS.map((name, k) => {
    const [lo, hi] = extent[k];
    const end = back[k] === lo ? hi : lo;
    const at = (v) => project(back.map((c, j) => (j === k ? v : c)));
    const ticks = [];
    for (let v = Math.ceil(lo / tickStep) * tickStep; v <= hi + 1e-9; v += tickStep) {
      // A tick at the shared corner would collide with the other two axes' ticks
      if (Math.abs(v - back[k]) < tickStep / 4) continue;
      ticks.push({ label: String(Math.round(v / magnitude) * magnitude), ...at(v) });
    }
    return { name, origin: at(back[k]), tip: at(end), ticks };
  });
}

function layoutScene(chart) {
  const axes = buildAxes();
  const points = data.map((d) => ({ ...project(AXIS_COLUMNS.map((c) => d[c])), record: d }));
  const [orbit, start, impact, ...axisSets] = chart.data.datasets;
  orbit.data = points;
  start.data = [points[0]];
  impact.data = [points[points.length - 1]];
  axisSets.forEach((set, k) => (set.data = [axes[k].origin, axes[k].tip]));
  chart.$axes = axes;

  // Equal screen units in both directions, so the 16:9 canvas does not stretch the path
  const frame = [...points, ...axes.flatMap((a) => [a.origin, a.tip])];
  const xs = frame.map((p) => p.x);
  const ys = frame.map((p) => p.y);
  const { width, height } = chart.chartArea;
  const unitsPerPx = (1.18 * Math.max((Math.max(...xs) - Math.min(...xs)) / width, (Math.max(...ys) - Math.min(...ys)) / height)) / camera.zoom;
  const [midX, midY] = [(Math.max(...xs) + Math.min(...xs)) / 2, (Math.max(...ys) + Math.min(...ys)) / 2];
  Object.assign(chart.options.scales.x, { min: midX - (unitsPerPx * width) / 2, max: midX + (unitsPerPx * width) / 2 });
  Object.assign(chart.options.scales.y, { min: midY - (unitsPerPx * height) / 2, max: midY + (unitsPerPx * height) / 2 });
  chart.update("none");
}

// Axis lines get tick marks, tick values and names; ticks point away from the projected path
const axisLabelPlugin = {
  id: "axisLabels",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    const px = (p) => [scales.x.getPixelForValue(p.x), scales.y.getPixelForValue(p.y)];
    const [cx, cy] = px(project([center[0], center[1], extent[2][0]]));
    ctx.save();
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1.5;
    for (const axis of chart.$axes ?? []) {
      const [ox, oy] = px(axis.origin);
      const [tx, ty] = px(axis.tip);
      const len = Math.hypot(tx - ox, ty - oy) || 1;
      const [ux, uy] = [(tx - ox) / len, (ty - oy) / len];
      // Floor axes: away from the floor's center; the altitude axis: to the left
      const isAltitude = axis.name === Z;
      const away = isAltitude ? uy : -uy * ((ox + tx) / 2 - cx) + ux * ((oy + ty) / 2 - cy);
      const outward = away >= 0 ? 1 : -1;
      const [dx, dy] = [-uy * outward, ux * outward];
      ctx.fillStyle = t.inkSoft;
      ctx.font = "18px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      for (const tick of axis.ticks) {
        const [x, y] = px(tick);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + dx * 8, y + dy * 8);
        ctx.stroke();
        ctx.fillText(tick.label, x + dx * 24, y + dy * 24);
      }
      ctx.fillStyle = t.ink;
      ctx.font = "20px sans-serif";
      ctx.textAlign = ux < -0.3 ? "right" : ux > 0.3 ? "left" : "center";
      ctx.textBaseline = uy < -0.3 ? "bottom" : uy > 0.3 ? "top" : "middle";
      ctx.fillText(axis.name, tx + ux * 12, ty + uy * 12);
    }
    ctx.restore();
  },
};

const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

const chart = new Chart(canvas, {
  type: "line",
  data: {
    datasets: [
      {
        label: `Orbit (color = ${ELAPSED.toLowerCase()})`,
        data: [],
        borderColor: t.palette[0],
        borderWidth: 3,
        pointRadius: 0,
        pointStyle: "line",
        // A bezier curve through the points; straight segments would also snap the
        // near-vertical sides of each loop to whole pixel columns
        tension: 0.3,
        segment: {
          borderColor: (ctx) => {
            const time = (data[ctx.p0DataIndex][ELAPSED] + data[ctx.p1DataIndex][ELAPSED]) / 2;
            const ratio = timeHigh > timeLow ? (time - timeLow) / (timeHigh - timeLow) : 0;
            const [r, g, b] = seqRgb[0].map((c, k) => Math.round(c + (seqRgb[1][k] - c) * ratio));
            return `rgb(${r}, ${g}, ${b})`;
          },
        },
        order: 2,
      },
      {
        label: "Orbit start",
        data: [],
        showLine: false,
        pointRadius: 11,
        pointBackgroundColor: t.palette[0],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
        order: 1,
      },
      {
        label: "Re-entry (impact)",
        data: [],
        showLine: false,
        pointRadius: 11,
        pointStyle: "triangle",
        pointBackgroundColor: t.palette[4],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
        order: 1,
      },
      ...AXIS_COLUMNS.map((name) => ({
        label: name,
        isAxis: true,
        data: [],
        borderColor: t.inkSoft,
        borderWidth: 1.5,
        pointRadius: 0,
        pointHitRadius: 0,
        order: 3,
      })),
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: 24 },
    parsing: { xAxisKey: "x", yAxisKey: "y" },
    onResize: (c) => requestAnimationFrame(() => layoutScene(c)),
    plugins: {
      title: {
        display: true,
        text: "line-3d-trajectory · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 18 },
          usePointStyle: true,
          padding: 24,
          filter: (item, chartData) => !chartData.datasets[item.datasetIndex].isAxis,
        },
      },
      tooltip: {
        filter: (item) => !item.dataset.isAxis,
        callbacks: {
          label: (ctx) => {
            const d = ctx.raw.record;
            return [X, Y, Z, ELAPSED].map((col) => `${col}: ${d[col].toFixed(2)}`);
          },
        },
      },
    },
    scales: {
      x: { type: "linear", display: false },
      y: { type: "linear", display: false },
    },
  },
  plugins: [axisLabelPlugin],
});
layoutScene(chart);

// Drag rotates the camera (azimuth and elevation), the wheel zooms
let dragFrom = null;
canvas.addEventListener("pointerdown", (e) => {
  dragFrom = { x: e.clientX, y: e.clientY };
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove", (e) => {
  if (!dragFrom) return;
  camera.azimuth += (e.clientX - dragFrom.x) * 0.01;
  camera.elevation = Math.min(Math.PI / 2, Math.max(-Math.PI / 2, camera.elevation + (e.clientY - dragFrom.y) * 0.01));
  dragFrom = { x: e.clientX, y: e.clientY };
  layoutScene(chart);
});
canvas.addEventListener("pointerup", () => (dragFrom = null));
canvas.addEventListener(
  "wheel",
  (e) => {
    e.preventDefault();
    camera.zoom = Math.min(5, Math.max(0.4, camera.zoom * Math.exp(-e.deltaY * 0.001)));
    layoutScene(chart);
  },
  { passive: false },
);
