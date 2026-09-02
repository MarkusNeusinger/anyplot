// anyplot.ai
// point-and-figure-basic: Point and Figure Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: synthetic daily close prices for a fictitious stock -------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const numDays = 300; // ~14 trading months
const closes = [118];
for (let day = 1; day < numDays; day++) {
  const macroTrend = Math.sin((day / numDays) * Math.PI * 22) * 3.2;
  const dailyNoise = (rand() - 0.5) * 5.0;
  const next = closes[day - 1] + macroTrend + dailyNoise;
  closes.push(Math.max(70, next));
}

// --- Point and Figure construction (close-based, 3-box reversal) -----------
const boxSize = 1; // $1 per box
const reversalBoxes = 3; // classic 3-box reversal method
const boxIndexOf = (price) => Math.floor(price / boxSize);

let direction = 0; // 0 = undetermined, 1 = X column, -1 = O column
let colTop = boxIndexOf(closes[0]);
let colBottom = colTop;
const columns = [];

for (let i = 1; i < closes.length; i++) {
  const idx = boxIndexOf(closes[i]);

  if (direction === 0) {
    if (idx > colTop) {
      direction = 1;
      colTop = idx;
    } else if (idx < colBottom) {
      direction = -1;
      colBottom = idx;
    }
    continue;
  }

  if (direction === 1) {
    if (idx > colTop) {
      colTop = idx;
    } else if (idx <= colTop - reversalBoxes) {
      columns.push({ dir: 1, top: colTop, bottom: colBottom });
      direction = -1;
      colBottom = idx;
      colTop = colTop - 1;
    }
  } else {
    if (idx < colBottom) {
      colBottom = idx;
    } else if (idx >= colBottom + reversalBoxes) {
      columns.push({ dir: -1, top: colTop, bottom: colBottom });
      direction = 1;
      colTop = idx;
      colBottom = colBottom + 1;
    }
  }
}
columns.push({ dir: direction || 1, top: colTop, bottom: colBottom });

// --- Flatten columns into per-box scatter points ----------------------------
const risingBoxes = [];
const fallingBoxes = [];
columns.forEach((col, colIndex) => {
  for (let box = col.bottom; box <= col.top; box++) {
    const point = { x: colIndex + 1, y: box * boxSize };
    if (col.dir === 1) risingBoxes.push(point);
    else fallingBoxes.push(point);
  }
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "X — rising",
        data: risingBoxes,
        pointStyle: "crossRot",
        pointRadius: 11,
        pointBorderWidth: 3,
        pointBorderColor: t.palette[0],
        pointBackgroundColor: t.palette[0],
        showLine: false,
      },
      {
        label: "O — falling",
        data: fallingBoxes,
        pointStyle: "circle",
        pointRadius: 11,
        pointBorderWidth: 3,
        pointBorderColor: t.palette[4],
        pointBackgroundColor: "transparent",
        showLine: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "point-and-figure-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 }, usePointStyle: true },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        suggestedMax: columns.length + 1,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: {
          display: true,
          text: "Column (price reversal sequence)",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        ticks: {
          stepSize: 10,
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => `$${value}`,
        },
        grid: { color: t.grid },
        title: { display: true, text: "Price ($)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
