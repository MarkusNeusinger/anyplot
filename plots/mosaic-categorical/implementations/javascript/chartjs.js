// anyplot.ai
// mosaic-categorical: Mosaic Plot for Categorical Association Analysis
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Survey of employees: department (category_1, column width) vs. work mode
// (category_2, stacked row height) — a classic contingency-table scenario.
const departments = ["Engineering", "Sales", "Marketing", "Support"];
const workModes = ["Remote", "Hybrid", "Onsite"];
const counts = [
  [180, 90, 30], // Engineering
  [40, 60, 100], // Sales
  [70, 50, 30], // Marketing
  [20, 40, 90], // Support
];

const rowTotals = counts.map((row) => row.reduce((sum, n) => sum + n, 0));
const grandTotal = rowTotals.reduce((sum, n) => sum + n, 0);

// Column edges as fractions of [0, 1] — width encodes the marginal share of
// each department among all employees.
const colEdges = [0];
rowTotals.forEach((total) => colEdges.push(colEdges[colEdges.length - 1] + total / grandTotal));

// Stacked segment heights as fractions of [0, 1] within a column — height
// encodes the conditional share of each work mode within that department.
const segmentFractions = workModes.map((_, modeIndex) =>
  counts.map((row, deptIndex) => row[modeIndex] / rowTotals[deptIndex]),
);

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Plugin: draw the mosaic tiles + department labels -----------------------
// Chart.js has no native mosaic/variable-width-bar controller, so the tiles are
// drawn directly onto the chart's own canvas from the finalized chartArea —
// this uses only core Chart.js plugin hooks (no external plugin package).
const tileGap = 4;
const mosaicPlugin = {
  id: "mosaicTiles",
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    const { left, top, width, height, bottom } = chartArea;

    ctx.save();
    departments.forEach((dept, colIndex) => {
      const xStart = left + colEdges[colIndex] * width;
      const xEnd = left + colEdges[colIndex + 1] * width;
      const colWidth = xEnd - xStart;

      let yCursor = top;
      workModes.forEach((mode, modeIndex) => {
        const segHeight = segmentFractions[modeIndex][colIndex] * height;
        ctx.fillStyle = t.palette[modeIndex];
        ctx.fillRect(
          xStart + tileGap / 2,
          yCursor + tileGap / 2,
          Math.max(0, colWidth - tileGap),
          Math.max(0, segHeight - tileGap),
        );
        yCursor += segHeight;
      });
    });
    ctx.restore();

    // Department labels (category_1) directly below their column.
    ctx.save();
    ctx.fillStyle = t.ink;
    ctx.font = "14px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    departments.forEach((dept, colIndex) => {
      const xCenter = left + ((colEdges[colIndex] + colEdges[colIndex + 1]) / 2) * width;
      ctx.fillText(dept, xCenter, bottom + 12);
    });
    ctx.font = "12px sans-serif";
    ctx.fillStyle = t.inkSoft;
    ctx.fillText("Department (column width ∝ headcount share)", left + width / 2, bottom + 32);
    ctx.restore();
  },
};

// --- Chart ---------------------------------------------------------------
// No dataset elements are rendered — the y scale supplies the percentage
// ruler and reserves layout space, while mosaicPlugin paints the tiles.
new Chart(canvas, {
  type: "bar",
  data: { labels: departments, datasets: [] },
  plugins: [mosaicPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 16, bottom: 46, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "mosaic-categorical · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        position: "right",
        labels: {
          color: t.ink,
          font: { size: 16 },
          boxWidth: 20,
          generateLabels: () =>
            workModes.map((mode, i) => ({
              text: mode,
              fillStyle: t.palette[i],
              strokeStyle: t.palette[i],
              lineWidth: 0,
            })),
        },
        title: { display: true, text: "Work mode", color: t.ink, font: { size: 14 } },
        onClick: () => {},
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: { display: false },
      y: {
        min: 0,
        max: 1,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => `${Math.round(value * 100)}%`,
        },
        grid: { color: t.grid },
        border: { display: false },
        title: { display: true, text: "Share within department", color: t.ink, font: { size: 14 } },
      },
    },
  },
});
