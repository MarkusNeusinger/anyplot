// anyplot.ai
// facet-grid: Faceted Grid Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-05
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
function makeLcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);
function randNormal(mean, std) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

const vehicleClasses = ["Sedan", "SUV"];
const drivetrains = ["FWD", "AWD", "RWD"];
const engineBaseByClass = { Sedan: 2.0, SUV: 3.2 };
const mpgPenaltyByDrivetrain = { FWD: 0, AWD: -3, RWD: -5 };

const POINTS_PER_FACET = 140;
const facets = [];
for (const vehicleClass of vehicleClasses) {
  for (const drivetrain of drivetrains) {
    const points = [];
    for (let i = 0; i < POINTS_PER_FACET; i++) {
      const engineSize = Math.max(
        1.0,
        randNormal(engineBaseByClass[vehicleClass], 0.6),
      );
      const baseMpg = 45 - engineSize * 6 + mpgPenaltyByDrivetrain[drivetrain];
      const fuelEconomy = Math.max(8, baseMpg + randNormal(0, 2.5));
      points.push({ x: engineSize, y: fuelEconomy });
    }
    facets.push({ row: vehicleClass, col: drivetrain, points });
  }
}

// Shared axis range across every facet, per the spec's "same axes scales by default"
const allX = facets.flatMap((f) => f.points.map((p) => p.x));
const allY = facets.flatMap((f) => f.points.map((p) => p.y));
const xPad = (Math.max(...allX) - Math.min(...allX)) * 0.08;
const yPad = (Math.max(...allY) - Math.min(...allY)) * 0.08;
const X_MIN = Math.floor(Math.min(...allX) - xPad);
const X_MAX = Math.ceil(Math.max(...allX) + xPad);
const Y_MIN = Math.floor(Math.min(...allY) - yPad);
const Y_MAX = Math.ceil(Math.max(...allY) + yPad);

// --- Scaffolding -------------------------------------------------------------
const style = document.createElement("style");
style.textContent = "#container, #container * { box-sizing: border-box; }";
document.head.appendChild(style);

const container = document.getElementById("container");
container.style.display = "flex";
container.style.flexDirection = "column";
container.style.padding = "20px 28px 16px 28px";
container.style.background = t.pageBg;
container.style.fontFamily =
  "system-ui, -apple-system, Helvetica, Arial, sans-serif";

const title = document.createElement("div");
title.textContent = "facet-grid · javascript · chartjs · anyplot.ai";
title.style.color = t.ink;
title.style.fontSize = "22px";
title.style.fontWeight = "600";
title.style.textAlign = "center";
title.style.marginBottom = "14px";
container.appendChild(title);

const body = document.createElement("div");
body.style.display = "flex";
body.style.flex = "1";
body.style.minHeight = "0";
container.appendChild(body);

const yAxisLabel = document.createElement("div");
yAxisLabel.textContent = "Fuel Economy (mpg)";
yAxisLabel.style.color = t.ink;
yAxisLabel.style.fontSize = "16px";
yAxisLabel.style.writingMode = "vertical-rl";
yAxisLabel.style.transform = "rotate(180deg)";
yAxisLabel.style.display = "flex";
yAxisLabel.style.alignItems = "center";
yAxisLabel.style.justifyContent = "center";
yAxisLabel.style.padding = "0 8px";
body.appendChild(yAxisLabel);

const gridArea = document.createElement("div");
gridArea.style.display = "flex";
gridArea.style.flexDirection = "column";
gridArea.style.flex = "1";
gridArea.style.minWidth = "0";
body.appendChild(gridArea);

// Column strip labels (top), with a trailing spacer matching the row-label column
const colHeaderRow = document.createElement("div");
colHeaderRow.style.display = "flex";
colHeaderRow.style.gap = "6px";
for (const drivetrain of drivetrains) {
  const cell = document.createElement("div");
  cell.textContent = `Drivetrain: ${drivetrain}`;
  cell.style.flex = "1";
  cell.style.textAlign = "center";
  cell.style.color = t.ink;
  cell.style.fontSize = "15px";
  cell.style.fontWeight = "600";
  cell.style.paddingBottom = "8px";
  colHeaderRow.appendChild(cell);
}
const colHeaderSpacer = document.createElement("div");
colHeaderSpacer.style.width = "32px";
colHeaderSpacer.style.flexShrink = "0";
colHeaderRow.appendChild(colHeaderSpacer);
gridArea.appendChild(colHeaderRow);

const rowsWrap = document.createElement("div");
rowsWrap.style.display = "flex";
rowsWrap.style.flexDirection = "column";
rowsWrap.style.flex = "1";
rowsWrap.style.minHeight = "0";
rowsWrap.style.gap = "6px";
gridArea.appendChild(rowsWrap);

vehicleClasses.forEach((vehicleClass, rowIdx) => {
  const rowDiv = document.createElement("div");
  rowDiv.style.display = "flex";
  rowDiv.style.flex = "1";
  rowDiv.style.minHeight = "0";
  rowDiv.style.gap = "6px";

  drivetrains.forEach((drivetrain, colIdx) => {
    const cellWrap = document.createElement("div");
    cellWrap.style.position = "relative";
    cellWrap.style.flex = "1";
    cellWrap.style.minWidth = "0";
    cellWrap.style.background = t.elevatedBg;
    cellWrap.style.border = `1px solid ${t.grid}`;

    const canvas = document.createElement("canvas");
    cellWrap.appendChild(canvas);
    rowDiv.appendChild(cellWrap);

    const facet = facets.find(
      (f) => f.row === vehicleClass && f.col === drivetrain,
    );
    const isLeftCol = colIdx === 0;
    const isBottomRow = rowIdx === vehicleClasses.length - 1;

    new Chart(canvas, {
      type: "scatter",
      data: {
        datasets: [
          {
            data: facet.points,
            backgroundColor: t.palette[0],
            pointRadius: 3.2,
            pointHoverRadius: 3.2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: { legend: { display: false }, title: { display: false } },
        scales: {
          x: {
            min: X_MIN,
            max: X_MAX,
            ticks: {
              display: isBottomRow,
              color: t.inkSoft,
              font: { size: 12 },
              maxTicksLimit: 5,
            },
            grid: { color: t.grid },
          },
          y: {
            min: Y_MIN,
            max: Y_MAX,
            ticks: {
              display: isLeftCol,
              color: t.inkSoft,
              font: { size: 12 },
              maxTicksLimit: 5,
            },
            grid: { color: t.grid },
          },
        },
      },
    });
  });

  const rowLabel = document.createElement("div");
  rowLabel.textContent = `Class: ${vehicleClass}`;
  rowLabel.style.width = "32px";
  rowLabel.style.flexShrink = "0";
  rowLabel.style.display = "flex";
  rowLabel.style.alignItems = "center";
  rowLabel.style.justifyContent = "center";
  rowLabel.style.writingMode = "vertical-rl";
  rowLabel.style.color = t.ink;
  rowLabel.style.fontSize = "15px";
  rowLabel.style.fontWeight = "600";
  rowDiv.appendChild(rowLabel);

  rowsWrap.appendChild(rowDiv);
});

const xAxisLabel = document.createElement("div");
xAxisLabel.textContent = "Engine Size (L)";
xAxisLabel.style.color = t.ink;
xAxisLabel.style.fontSize = "16px";
xAxisLabel.style.textAlign = "center";
xAxisLabel.style.marginTop = "10px";
gridArea.appendChild(xAxisLabel);
