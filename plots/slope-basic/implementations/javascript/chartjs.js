// anyplot.ai
// slope-basic: Basic Slope Chart (Slopegraph)
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 93/100 | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Reading tutoring program: student scores (out of 100) before and after.
const students = [
  "Ava", "Liam", "Sophia", "Mason", "Isabella",
  "Ethan", "Mia", "Noah", "Amelia", "Lucas",
];
const preTest = [62, 58, 71, 45, 80, 55, 67, 73, 49, 61];
const postTest = [78, 65, 74, 52, 88, 70, 66, 90, 61, 59];

const INCREASE = t.palette[0]; // #009E73 brand green — up/gain (semantic exception)
const DECREASE = "#AE3030"; // matte red — down/loss (semantic anchor, slot 5)

const datasets = students.map((name, i) => {
  const color = postTest[i] >= preTest[i] ? INCREASE : DECREASE;
  return {
    label: name,
    data: [preTest[i], postTest[i]],
    borderColor: color,
    backgroundColor: color,
    pointBackgroundColor: color,
    pointBorderColor: color,
    pointRadius: 6,
    pointHoverRadius: 6,
    borderWidth: 3,
    tension: 0,
  };
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Endpoint label plugin (native Chart.js plugin API, no external deps) ---
// Draws entity name + value at both ends of each line, matching the spec's
// "labels at both endpoints" requirement while keeping the legend uncluttered.
const endpointLabels = {
  id: "slopeEndpointLabels",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    ctx.save();
    ctx.font = "600 15px sans-serif";
    ctx.textBaseline = "middle";
    chart.data.datasets.forEach((ds, i) => {
      const meta = chart.getDatasetMeta(i);
      if (meta.hidden) return;
      const [p0, p1] = meta.data;
      ctx.fillStyle = ds.borderColor;
      ctx.textAlign = "right";
      ctx.fillText(`${ds.label}  ${ds.data[0]}`, p0.x - 14, p0.y);
      ctx.textAlign = "left";
      ctx.fillText(`${ds.data[1]}  ${ds.label}`, p1.x + 14, p1.y);
    });
    ctx.restore();
  },
};
Chart.register(endpointLabels);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels: ["Pre-Test", "Post-Test"],
    datasets,
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: {
      padding: { left: 190, right: 190, top: 20, bottom: 10 },
    },
    plugins: {
      title: {
        display: true,
        text: "slope-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          generateLabels: () => [
            { text: "Increase", fillStyle: INCREASE, strokeStyle: INCREASE, lineWidth: 0 },
            { text: "Decrease", fillStyle: DECREASE, strokeStyle: DECREASE, lineWidth: 0 },
          ],
        },
        onClick: () => {},
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "category",
        offset: false,
        ticks: { color: t.inkSoft, font: { size: 18, weight: "600" } },
        grid: { color: t.grid, drawTicks: false },
        border: { color: t.grid },
      },
      y: {
        display: false,
      },
    },
  },
});
