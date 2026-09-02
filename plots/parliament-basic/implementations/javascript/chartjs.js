// anyplot.ai
// parliament-basic: Parliament Seat Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Generic fictional legislature, ordered left-to-right along the political
// spectrum so seat blocks read naturally once laid out below.
const parties = [
  { name: "Green Alliance", seats: 38 },
  { name: "Social Democrats", seats: 52 },
  { name: "Liberal Union", seats: 24 },
  { name: "Centrist Coalition", seats: 18 },
  { name: "Conservative Bloc", seats: 46 },
  { name: "Independents", seats: 22 },
];
const totalSeats = parties.reduce((sum, p) => sum + p.seats, 0);

// --- Semicircular seat layout ------------------------------------------------
// Seats sit on concentric arcs; each arc's seat capacity scales with its
// radius (longer arc = more room), so dot spacing stays roughly even across
// rows. Seats are then globally ordered by angle (left = pi, right = 0) so
// each party forms a contiguous wedge from the outer edge to the center.
const numRows = 6;
const rMin = 0.38;
const rMax = 1.0;
const rowRadii = Array.from({ length: numRows }, (_, i) => rMin + (i * (rMax - rMin)) / (numRows - 1));
const capacitySum = rowRadii.reduce((sum, r) => sum + r, 0);

let assignedSeats = 0;
const seatsPerRow = rowRadii.map((radius, i) => {
  if (i === numRows - 1) return totalSeats - assignedSeats;
  const rowSeats = Math.round((totalSeats * radius) / capacitySum);
  assignedSeats += rowSeats;
  return rowSeats;
});

const seatPositions = [];
rowRadii.forEach((radius, i) => {
  const rowSeats = seatsPerRow[i];
  for (let j = 0; j < rowSeats; j++) {
    const angle = Math.PI - ((j + 0.5) / rowSeats) * Math.PI;
    seatPositions.push({ x: radius * Math.cos(angle), y: radius * Math.sin(angle), angle });
  }
});
seatPositions.sort((a, b) => b.angle - a.angle);

let cursor = 0;
const datasets = parties.map((party, i) => {
  const points = seatPositions.slice(cursor, cursor + party.seats).map(({ x, y }) => ({ x, y }));
  cursor += party.seats;
  return {
    label: `${party.name} (${party.seats})`,
    data: points,
    backgroundColor: t.palette[i % t.palette.length],
    pointBorderColor: t.pageBg,
    pointBorderWidth: 1.5,
    pointRadius: 9,
    pointHoverRadius: 9,
  };
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 10, bottom: 10, left: 20, right: 20 } },
    plugins: {
      title: {
        display: true,
        text: "parliament-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 16 },
      },
      legend: {
        position: "bottom",
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          usePointStyle: true,
          pointStyle: "circle",
          padding: 16,
        },
      },
      tooltip: {
        callbacks: {
          title: () => "",
          label: (ctx) => ctx.dataset.label,
        },
      },
    },
    scales: {
      x: { display: false, min: -1.08, max: 1.08 },
      y: { display: false, min: -0.02, max: 1.02 },
    },
  },
});
