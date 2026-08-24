// anyplot.ai
// bump-basic: Basic Bump Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-08-24

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// A regional football league table: rank (1 = top) per team across matchweeks.
const matchweeks = ["MW1", "MW2", "MW3", "MW4", "MW5", "MW6", "MW7", "MW8"];
const standings = [
  { team: "Falcons", ranks: [3, 2, 1, 1, 2, 1, 1, 1], symbol: "circle" },
  { team: "Comets", ranks: [1, 1, 2, 2, 1, 2, 3, 2], symbol: "diamond" },
  { team: "Vipers", ranks: [2, 3, 3, 4, 4, 3, 2, 3], symbol: "square" },
  { team: "Titans", ranks: [5, 4, 4, 3, 3, 4, 4, 4], symbol: "triangle" },
  { team: "Wolves", ranks: [4, 5, 6, 5, 6, 6, 5, 5], symbol: "triangle-down" },
  { team: "Sharks", ranks: [6, 6, 5, 6, 5, 5, 6, 6], symbol: "circle" },
];
const lastIndex = matchweeks.length - 1;

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    marginRight: 130,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "bump-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: matchweeks,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Matchweek", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: {
    title: { text: "League Position (1 = top)", style: { color: t.inkSoft, fontSize: "16px" } },
    min: 1,
    max: standings.length,
    tickInterval: 1,
    allowDecimals: false,
    reversed: true,
    gridLineColor: t.grid,
    lineColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  tooltip: { headerFormat: "<b>{point.key}</b><br/>", pointFormat: "{series.name}: rank {point.y}" },
  plotOptions: {
    series: {
      animation: false,
      lineWidth: 2.5,
      marker: { radius: 5 },
      dataLabels: { enabled: false, crop: false, overflow: "allow" },
    },
  },
  series: standings.map((entry) => ({
    name: entry.team,
    marker: { symbol: entry.symbol },
    data: entry.ranks.map((rank, i) =>
      i === lastIndex
        ? {
            y: rank,
            dataLabels: {
              enabled: true,
              align: "left",
              x: 10,
              format: entry.team,
              style: { color: t.ink, fontSize: "14px", fontWeight: "600", textOutline: "none" },
            },
          }
        : { y: rank }
    ),
  })),
});
