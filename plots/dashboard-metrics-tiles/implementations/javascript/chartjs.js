// anyplot.ai
// dashboard-metrics-tiles: Real-Time Dashboard Tiles
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-01

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Tiny fixed-seed LCG — the browser has no seeded RNG.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

// Builds a short trend history that drifts toward `drift` each step, then
// derives the tile's headline value from the trend's final point so the
// sparkline and the big number always agree.
function buildMetric(
  name,
  unit,
  decimals,
  base,
  spread,
  drift,
  points,
  changePercent,
  higherIsBetter,
  status,
) {
  const data = [];
  let v = base;
  for (let i = 0; i < points; i++) {
    v = Math.max(0, v + (rand() - 0.5) * spread + drift);
    data.push(v);
  }
  const value =
    decimals > 0
      ? +data[data.length - 1].toFixed(decimals)
      : Math.round(data[data.length - 1]);
  return { name, unit, value, data, changePercent, higherIsBetter, status };
}

const metrics = [
  buildMetric("CPU Usage", "%", 0, 50, 6, -0.35, 16, -5.2, false, "good"),
  buildMetric("Memory", "%", 0, 64, 5, 0.55, 16, 8.4, false, "warning"),
  buildMetric(
    "Response Time",
    "ms",
    0,
    140,
    12,
    -1.3,
    16,
    -15.3,
    false,
    "good",
  ),
  buildMetric(
    "Error Rate",
    "%",
    1,
    2.2,
    0.6,
    0.12,
    16,
    42.1,
    false,
    "critical",
  ),
  buildMetric("Requests/sec", "", 0, 1700, 90, 8, 16, 6.7, true, "good"),
  buildMetric("Active Users", "", 0, 9500, 220, -18, 16, -2.1, true, "warning"),
];

// good/warning/critical are a traffic-light convention readers already expect —
// semantic exception from the Imprint palette rather than ordinal position.
const STATUS_COLOR = {
  good: t.palette[0],
  warning: t.amber,
  critical: t.palette[4],
};

// null = flat (no favorable/unfavorable read); otherwise "does this change help".
function favorableColor(m) {
  if (m.changePercent === 0) return t.inkSoft;
  const favorable = m.changePercent > 0 === m.higherIsBetter;
  return favorable ? t.palette[0] : t.palette[4];
}

// --- Mount -------------------------------------------------------------------
const root = document.getElementById("container");
root.style.display = "flex";
root.style.flexDirection = "column";
root.style.padding = "36px 44px 40px";
root.style.gap = "22px";

const heading = document.createElement("div");
heading.textContent =
  "dashboard-metrics-tiles · javascript · chartjs · anyplot.ai";
heading.style.fontSize = "22px";
heading.style.fontWeight = "600";
heading.style.color = t.ink;
root.appendChild(heading);

const grid = document.createElement("div");
grid.style.flex = "1";
grid.style.display = "grid";
grid.style.gridTemplateColumns = "repeat(3, 1fr)";
grid.style.gridTemplateRows = "repeat(2, 1fr)";
grid.style.gap = "22px";
root.appendChild(grid);

// --- Tiles ---------------------------------------------------------------
metrics.forEach((m) => {
  const tile = document.createElement("div");
  tile.style.background = t.elevatedBg;
  tile.style.borderRadius = "16px";
  tile.style.padding = "24px 28px";
  tile.style.display = "flex";
  tile.style.flexDirection = "column";
  tile.style.justifyContent = "space-between";
  grid.appendChild(tile);

  const labelRow = document.createElement("div");
  labelRow.style.display = "flex";
  labelRow.style.alignItems = "center";
  labelRow.style.gap = "10px";
  tile.appendChild(labelRow);

  const dot = document.createElement("span");
  dot.style.width = "11px";
  dot.style.height = "11px";
  dot.style.borderRadius = "50%";
  dot.style.background = STATUS_COLOR[m.status];
  dot.style.flex = "none";
  labelRow.appendChild(dot);

  const label = document.createElement("span");
  label.textContent = m.name;
  label.style.fontSize = "16px";
  label.style.fontWeight = "500";
  label.style.color = t.inkSoft;
  labelRow.appendChild(label);

  const valueRow = document.createElement("div");
  valueRow.style.display = "flex";
  valueRow.style.alignItems = "baseline";
  valueRow.style.gap = "14px";
  tile.appendChild(valueRow);

  const value = document.createElement("span");
  value.textContent = `${m.value}${m.unit}`;
  value.style.fontSize = "46px";
  value.style.fontWeight = "700";
  value.style.color = t.ink;
  valueRow.appendChild(value);

  const arrow = m.changePercent > 0 ? "▲" : m.changePercent < 0 ? "▼" : "–";
  const change = document.createElement("span");
  change.textContent = `${arrow} ${Math.abs(m.changePercent).toFixed(1)}%`;
  change.style.fontSize = "18px";
  change.style.fontWeight = "600";
  change.style.color = favorableColor(m);
  valueRow.appendChild(change);

  const sparkWrap = document.createElement("div");
  sparkWrap.style.height = "84px";
  sparkWrap.style.marginTop = "6px";
  tile.appendChild(sparkWrap);

  const canvas = document.createElement("canvas");
  sparkWrap.appendChild(canvas);

  new Chart(canvas, {
    type: "line",
    data: {
      labels: m.data.map((_, i) => i),
      datasets: [
        {
          data: m.data,
          borderColor: STATUS_COLOR[m.status],
          backgroundColor: `${STATUS_COLOR[m.status]}26`,
          borderWidth: 2.5,
          pointRadius: 0,
          fill: true,
          tension: 0.35,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: { x: { display: false }, y: { display: false } },
    },
  });
});
