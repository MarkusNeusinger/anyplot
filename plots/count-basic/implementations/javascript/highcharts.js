// anyplot.ai
// count-basic: Basic Count Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-11

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Raw per-checkout genre observations from a library lending log; the count
// plot tallies occurrences from these raw records rather than pre-aggregated
// values.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const random = lcg(42);

const genres = ["Fiction", "Fantasy", "Mystery", "Sci-Fi", "Biography", "Romance", "History", "Poetry"];
const weights = [0.22, 0.18, 0.15, 0.13, 0.1, 0.09, 0.07, 0.06];
const cumulative = weights.reduce((acc, w, i) => {
  acc.push((acc[i - 1] || 0) + w);
  return acc;
}, []);

const checkouts = [];
for (let i = 0; i < 1200; i++) {
  const r = random();
  checkouts.push(genres[cumulative.findIndex((c) => r <= c)]);
}

const counts = {};
genres.forEach((genre) => (counts[genre] = 0));
checkouts.forEach((genre) => (counts[genre] += 1));

const sorted = genres
  .map((genre) => ({ genre, count: counts[genre] }))
  .sort((a, b) => b.count - a.count);

const categories = sorted.map((d) => d.genre);
const values = sorted.map((d) => d.count);

// --- Chart -----------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "column",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "count-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Checkouts", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    column: {
      borderWidth: 0,
      colorByPoint: true,
      dataLabels: {
        enabled: true,
        color: t.ink,
        style: { fontSize: "14px", fontWeight: "500", textOutline: "none" },
      },
    },
  },
  series: [{ name: "Checkouts", data: values }],
});
