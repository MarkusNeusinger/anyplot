// anyplot.ai
// dashboard-metrics-tiles: Real-Time Dashboard Tiles
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG — no seeded RNG in the browser) ----
function lcg(seed) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}

function history(seed, n, base, trend, noiseFrac) {
  const rand = lcg(seed);
  const values = [];
  let v = base;
  for (let i = 0; i < n; i++) {
    v += trend + (rand() - 0.5) * base * noiseFrac;
    values.push(Math.max(0, Math.round(v * 100) / 100));
  }
  return values;
}

const STATUS_COLOR = { good: t.palette[0], warning: t.amber, critical: t.palette[4] };

const tiles = [
  {
    label: "CPU Usage",
    value: "45%",
    changePercent: -5.2,
    favorableDirection: "down",
    status: "good",
    history: history(1, 24, 50, -0.22, 0.05),
  },
  {
    label: "Memory Usage",
    value: "72%",
    changePercent: 8.1,
    favorableDirection: "down",
    status: "warning",
    history: history(2, 24, 63, 0.36, 0.04),
  },
  {
    label: "Response Time",
    value: "120 ms",
    changePercent: -15.4,
    favorableDirection: "down",
    status: "good",
    history: history(3, 24, 148, -1.1, 0.06),
  },
  {
    label: "Error Rate",
    value: "2.3%",
    changePercent: 24.0,
    favorableDirection: "down",
    status: "critical",
    history: history(4, 24, 1.6, 0.028, 0.18),
  },
  {
    label: "Active Users",
    value: "8,412",
    changePercent: 12.3,
    favorableDirection: "up",
    status: "good",
    history: history(5, 24, 7180, 55, 0.03),
  },
  {
    label: "Throughput",
    value: "340 MB/s",
    changePercent: 6.7,
    favorableDirection: "up",
    status: "good",
    history: history(6, 24, 305, 1.6, 0.05),
  },
];

// --- Layout (dashboard grid built as DOM, sparklines rendered by Highcharts) --
const root = document.getElementById("container");

const header = document.createElement("div");
header.style.cssText = `padding:22px 28px 4px; font-size:22px; font-weight:600; color:${t.ink}; font-family:inherit;`;
header.textContent = "dashboard-metrics-tiles · javascript · highcharts · anyplot.ai";
root.appendChild(header);

const grid = document.createElement("div");
grid.style.cssText =
  "display:grid; grid-template-columns:repeat(3, 1fr); grid-template-rows:repeat(2, 1fr); " +
  "gap:22px; margin:14px 28px 28px; height:calc(100% - 90px);";
root.appendChild(grid);

tiles.forEach((tile, index) => {
  const statusColor = STATUS_COLOR[tile.status];
  const isFavorable =
    (tile.favorableDirection === "down" && tile.changePercent < 0) ||
    (tile.favorableDirection === "up" && tile.changePercent > 0);
  const changeColor = isFavorable ? t.palette[0] : t.palette[4];
  const arrow = tile.changePercent >= 0 ? "▲" : "▼";

  const card = document.createElement("div");
  card.style.cssText = `background:${t.elevatedBg}; border-radius:14px; padding:22px 26px; display:flex; flex-direction:column; justify-content:flex-start;`;

  const headerRow = document.createElement("div");
  headerRow.style.cssText = "display:flex; align-items:center; justify-content:space-between;";
  const labelEl = document.createElement("span");
  labelEl.textContent = tile.label;
  labelEl.style.cssText = `font-size:15px; font-weight:500; color:${t.inkSoft}; letter-spacing:0.02em;`;
  const dotEl = document.createElement("span");
  dotEl.style.cssText = `width:12px; height:12px; border-radius:50%; background:${statusColor}; display:inline-block;`;
  headerRow.appendChild(labelEl);
  headerRow.appendChild(dotEl);

  const valueRow = document.createElement("div");
  valueRow.style.cssText = "display:flex; align-items:baseline; gap:14px; margin-top:8px;";
  const valueEl = document.createElement("span");
  valueEl.textContent = tile.value;
  valueEl.style.cssText = `font-size:46px; font-weight:700; color:${t.ink}; line-height:1;`;
  const changeEl = document.createElement("span");
  changeEl.textContent = `${arrow} ${Math.abs(tile.changePercent).toFixed(1)}%`;
  changeEl.style.cssText = `font-size:17px; font-weight:600; color:${changeColor};`;
  valueRow.appendChild(valueEl);
  valueRow.appendChild(changeEl);

  const sparkEl = document.createElement("div");
  sparkEl.id = `spark-${index}`;
  sparkEl.style.cssText = "flex:1; min-height:64px; margin-top:8px;";

  card.appendChild(headerRow);
  card.appendChild(valueRow);
  card.appendChild(sparkEl);
  grid.appendChild(card);
});

// --- Sparkline charts (one Highcharts instance per tile, mounted after the DOM
//     nodes above are attached so Highcharts can measure each mount's size) ----
tiles.forEach((tile, index) => {
  const statusColor = STATUS_COLOR[tile.status];
  Highcharts.chart(`spark-${index}`, {
    chart: {
      type: "area",
      backgroundColor: "transparent",
      animation: false,
      margin: [4, 2, 4, 2],
    },
    credits: { enabled: false },
    title: { text: null },
    xAxis: { visible: false },
    yAxis: { visible: false },
    legend: { enabled: false },
    tooltip: { enabled: false },
    plotOptions: {
      series: {
        animation: false,
        enableMouseTracking: false,
        marker: { enabled: false },
        lineWidth: 2.5,
      },
      area: { fillOpacity: 0.16 },
    },
    series: [{ data: tile.history, color: statusColor }],
  });
});
