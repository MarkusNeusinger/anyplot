// anyplot.ai
// rug-basic: Basic Rug Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic, fixed-seed LCG) ------------------------
// Daily screen time (hours) for 350 survey respondents: a light-use cluster
// and a heavy-use cluster with a visible gap between them, plus a handful of
// high-end outliers — exactly the clustering/gap/outlier pattern a rug plot
// reveals that a histogram's bin width would smooth over.
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function gaussian(mean, sd) {
  const u1 = Math.max(lcg(), 1e-9);
  const u2 = lcg();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * sd;
}

const screenTimeHours = [];
for (let i = 0; i < 220; i++) screenTimeHours.push(Math.max(0.1, gaussian(2.0, 0.6)));
for (let i = 0; i < 130; i++) screenTimeHours.push(Math.max(0.1, gaussian(6.4, 0.9)));
[9.6, 10.3, 11.1, 12.4, 13.0, 9.9].forEach((v) => screenTimeHours.push(v));

const rugData = screenTimeHours.map((v) => [v, 1]);

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: { type: "column", backgroundColor: "transparent", animation: false,
           style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "rug-basic · javascript · highcharts · anyplot.ai",
           style: { color: t.ink, fontSize: "22px", fontWeight: "600" } },
  subtitle: { text: "Daily screen time reported by 356 survey respondents",
              style: { color: t.inkSoft, fontSize: "14px" } },
  xAxis: {
    title: { text: "Daily Screen Time (hours)",
             style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft, tickColor: t.inkSoft, gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    min: 0, tickInterval: 2, minPadding: 0.02, maxPadding: 0.04,
  },
  yAxis: {
    visible: false,
    min: 0, max: 4,
  },
  legend: { enabled: false },
  tooltip: {
    backgroundColor: t.elevatedBg, borderWidth: 0,
    style: { color: t.ink, fontSize: "13px" },
    headerFormat: "",
    pointFormatter: function () {
      return "Screen time: <b>" + this.x.toFixed(1) + " h</b>";
    },
  },
  plotOptions: {
    series: { animation: false },
    column: {
      pointWidth: 3,
      pointPadding: 0,
      groupPadding: 0,
      borderWidth: 0,
      color: Highcharts.color(t.palette[0]).setOpacity(0.55).get("rgba"),
      states: { hover: { brightness: 0.1 } },
    },
  },
  series: [{ name: "Respondent", data: rugData }],
});
