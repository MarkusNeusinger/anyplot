// The toolchain build's check of the JavaScript row (agents/renderer/toolchain.Dockerfile): a
// Chart.js chart with a non-ASCII title through the catalogue's harness, as the row runs it.
const t = window.ANYPLOT_TOKENS;
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);
new Chart(canvas, {
  type: "bar",
  data: { labels: ["a", "b", "c"], datasets: [{ data: [3, 1, 2], backgroundColor: t.palette[0] }] },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: { title: { display: true, text: "Größe – Überblick", color: t.ink } },
  },
});
