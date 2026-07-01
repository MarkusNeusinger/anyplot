// anyplot.ai
// lollipop-basic: Basic Lollipop Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-07-01
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (website traffic by marketing channel, sorted descending) --------
const channels = [
  "Paid Search", "Organic", "Social Media", "Blog",
  "Direct", "Email", "Influencer", "Referral",
  "Video Ads", "Podcast"
];
const visitors = [312, 285, 198, 176, 165, 142, 118, 89, 67, 43];

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart (lollipop: thin bars as stems + line points as dots) -----------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: channels,
    datasets: [
      {
        // Stems: very thin bars from baseline to value
        type: "bar",
        label: "Visitors (K)",
        data: visitors,
        backgroundColor: t.palette[0],
        barThickness: 3,
        order: 1,
      },
      {
        // Dots: large circular points at each value
        type: "line",
        label: "Visitors (K)",
        data: visitors,
        backgroundColor: t.palette[0],
        borderColor: t.pageBg,
        borderWidth: 2,
        pointRadius: 14,
        pointHoverRadius: 16,
        showLine: false,
        order: 2,
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
        text: "lollipop-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "bold" },
        padding: { top: 20, bottom: 30 },
      },
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
        },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Marketing Channel",
          color: t.ink,
          font: { size: 16 },
          padding: { top: 12 },
        },
      },
      y: {
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
        },
        grid: { color: t.grid },
        beginAtZero: true,
        title: {
          display: true,
          text: "Monthly Visitors (thousands)",
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 12 },
        },
      },
    },
    layout: {
      padding: { top: 10, bottom: 20, left: 30, right: 30 },
    },
  },
});
