// anyplot.ai
// line-3d-trajectory: 3D Line Plot for Trajectory Visualization
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-10

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: a decaying satellite orbit spiraling toward re-entry -----------
// Chart.js has no native 3D chart type, so the (x, y, z) trajectory is
// projected onto the 2D canvas with a fixed isometric transform before it is
// handed to a standard line dataset — the same approach a static 3D plot
// uses internally, just computed by hand instead of by a 3D engine.
const POINT_COUNT = 260;
const REVOLUTIONS = 3.5;
const RADIUS_START = 6.4;
const RADIUS_END = 1.2;
const ALTITUDE_START = 5.5;
const COS30 = Math.cos(Math.PI / 6);
const SIN30 = Math.sin(Math.PI / 6);

function project(x, y, z) {
  return { x: (x - y) * COS30, y: z - (x + y) * SIN30 };
}

const trajectory = [];
for (let i = 0; i < POINT_COUNT; i++) {
  const progress = i / (POINT_COUNT - 1);
  const angle = progress * REVOLUTIONS * 2 * Math.PI;
  const radius = RADIUS_START - (RADIUS_START - RADIUS_END) * progress;
  const origX = radius * Math.cos(angle);
  const origY = radius * Math.sin(angle);
  const origZ = ALTITUDE_START * Math.pow(1 - progress, 1.3);
  trajectory.push({
    ...project(origX, origY, origZ),
    origX,
    origY,
    origZ,
    progress,
  });
}

// --- 3D axes: drawn from the origin, each with its own scale and its name at the tip ---
// The canvas frame would only show projected screen coordinates, so it stays hidden and the
// drawn axes carry the scale instead.
const TICK_STEP = 2;
const axes = [
  { name: "X position", unit: [1, 0, 0], length: RADIUS_START + 1.2 },
  { name: "Y position", unit: [0, 1, 0], length: RADIUS_START + 1.2 },
  { name: "Altitude Z", unit: [0, 0, 1], length: ALTITUDE_START + 1 },
].map((axis) => {
  const at = (v) => {
    const [ux, uy, uz] = axis.unit.map((u) => u * v);
    return { ...project(ux, uy, uz), origX: ux, origY: uy, origZ: uz };
  };
  const ticks = [];
  for (let v = TICK_STEP; v < axis.length - TICK_STEP / 4; v += TICK_STEP) ticks.push({ value: v, ...at(v) });
  return { ...axis, origin: at(0), tip: at(axis.length), ticks };
});

// Equal units on both screen directions so the projection is not stretched by the 16:9 canvas
const LAYOUT_PADDING = 24;
const HEADER_HEIGHT = 100; // title and legend above the plot area
const frame = [...trajectory, ...axes.map((axis) => axis.tip)];
const screenXs = frame.map((p) => p.x);
const screenYs = frame.map((p) => p.y);
const [xLow, xHigh] = [Math.min(...screenXs), Math.max(...screenXs)];
const [yLow, yHigh] = [Math.min(...screenYs), Math.max(...screenYs)];
const areaW = window.ANYPLOT_SIZE.width - 2 * LAYOUT_PADDING;
const areaH = window.ANYPLOT_SIZE.height - 2 * LAYOUT_PADDING - HEADER_HEIGHT;
const unitsPerPx = 1.06 * Math.max((xHigh - xLow) / areaW, (yHigh - yLow) / areaH);
const halfW = (unitsPerPx * areaW) / 2;
const halfH = (unitsPerPx * areaH) / 2;

// --- Color: elapsed time mapped through the Imprint sequential scale ------
function lerpChannel(a, b, ratio) {
  return Math.round(a + (b - a) * ratio);
}
function lerpColor(hexA, hexB, ratio) {
  const a = parseInt(hexA.slice(1), 16);
  const b = parseInt(hexB.slice(1), 16);
  const r = lerpChannel((a >> 16) & 255, (b >> 16) & 255, ratio);
  const g = lerpChannel((a >> 8) & 255, (b >> 8) & 255, ratio);
  const bl = lerpChannel(a & 255, b & 255, ratio);
  return `rgb(${r}, ${g}, ${bl})`;
}

// --- Axis scales and names, drawn on the canvas at the projected positions ---
const axisLabelPlugin = {
  id: "axisLabels",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    const px = (p) => [scales.x.getPixelForValue(p.x), scales.y.getPixelForValue(p.y)];
    ctx.save();
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1.5;
    for (const axis of axes) {
      const [ox, oy] = px(axis.origin);
      const [tx, ty] = px(axis.tip);
      const len = Math.hypot(tx - ox, ty - oy);
      const [ux, uy] = [(tx - ox) / len, (ty - oy) / len];
      // Ticks point away from the trajectory: down from the floor axes, left of the vertical axis
      const [dx, dy] = axis.unit[2] ? [-1, 0] : ux > 0 ? [-uy, ux] : [uy, -ux];
      ctx.fillStyle = t.inkSoft;
      ctx.font = "14px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      for (const tick of axis.ticks) {
        const [x, y] = px(tick);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + dx * 8, y + dy * 8);
        ctx.stroke();
        ctx.fillText(String(tick.value), x + dx * 20, y + dy * 20);
      }
      ctx.fillStyle = t.ink;
      ctx.font = "16px sans-serif";
      ctx.textAlign = ux < -0.3 ? "right" : ux > 0.3 ? "left" : "center";
      ctx.textBaseline = uy < -0.3 ? "bottom" : uy > 0.3 ? "top" : "middle";
      ctx.fillText(axis.name, tx + ux * 10, ty + uy * 10);
    }
    ctx.restore();
  },
};

// --- Mount ------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    datasets: [
      ...axes.map((axis) => ({
        label: axis.name,
        isAxis: true,
        data: [axis.origin, axis.tip],
        borderColor: t.inkSoft,
        borderWidth: 1.5,
        pointRadius: 0,
        order: 3,
      })),
      {
        label: "Orbit (color = elapsed time)",
        data: trajectory,
        borderColor: t.palette[0],
        borderWidth: 3,
        pointRadius: 0,
        // A bezier curve through the 260 points; the straight-line path would also snap the
        // near-vertical sides of each loop to whole pixel columns
        tension: 0.3,
        segment: {
          borderColor: (ctx) => {
            const p0 = trajectory[ctx.p0DataIndex];
            const p1 = trajectory[ctx.p1DataIndex];
            const avgProgress = (p0.progress + p1.progress) / 2;
            return lerpColor(t.seq[0], t.seq[1], avgProgress);
          },
        },
        order: 2,
      },
      {
        label: "Orbit start",
        data: [trajectory[0]],
        showLine: false,
        pointRadius: 11,
        backgroundColor: t.palette[0],
        pointBackgroundColor: t.palette[0],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
        order: 1,
      },
      {
        label: "Re-entry (impact)",
        data: [trajectory[trajectory.length - 1]],
        showLine: false,
        pointRadius: 11,
        pointStyle: "triangle",
        backgroundColor: t.palette[4],
        pointBackgroundColor: t.palette[4],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
        order: 1,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: LAYOUT_PADDING },
    parsing: { xAxisKey: "x", yAxisKey: "y" },
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
          font: { size: 15 },
          filter: (item, data) => !data.datasets[item.datasetIndex].isAxis,
        },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const p = ctx.raw;
            return `x=${p.origX.toFixed(2)}, y=${p.origY.toFixed(2)}, z=${p.origZ.toFixed(2)}`;
          },
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        display: false,
        min: (xLow + xHigh) / 2 - halfW,
        max: (xLow + xHigh) / 2 + halfW,
      },
      y: {
        type: "linear",
        display: false,
        min: (yLow + yHigh) / 2 - halfH,
        max: (yLow + yHigh) / 2 + halfH,
      },
    },
  },
  plugins: [axisLabelPlugin],
});
