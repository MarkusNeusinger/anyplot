// anyplot.ai
// parliament-basic: Parliament Seat Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const parties = [
  { name: "Party A", seats: 58 },
  { name: "Party B", seats: 46 },
  { name: "Party C", seats: 38 },
  { name: "Party D", seats: 30 },
  { name: "Party E", seats: 18 },
  { name: "Party F", seats: 10 },
];
const totalSeats = parties.reduce((sum, party) => sum + party.seats, 0);

// --- Hemicycle seat layout ---------------------------------------------------
// Concentric arcs (rows) grow outward from an inner radius; each row's seat
// capacity scales with its arc length. Capacities are rescaled (largest
// remainder method) to sum to exactly `totalSeats`, then every seat position
// is sorted by angle left-to-right so parties form the classic contiguous
// wedges of a parliament diagram.
const INNER_RADIUS = 140;
const ROW_GAP = 34;
const SEAT_SPACING = 34;

const rawCapacities = [];
let rowRadius = INNER_RADIUS;
while (rawCapacities.reduce((a, b) => a + b, 0) < totalSeats) {
  rawCapacities.push(Math.max(1, Math.floor((Math.PI * rowRadius) / SEAT_SPACING)));
  rowRadius += ROW_GAP;
}
const capacitySum = rawCapacities.reduce((a, b) => a + b, 0);
const scaledCapacities = rawCapacities.map((c) => (c / capacitySum) * totalSeats);
const rowSeatCounts = scaledCapacities.map(Math.floor);
const remainder = totalSeats - rowSeatCounts.reduce((a, b) => a + b, 0);
const byFraction = scaledCapacities
  .map((value, i) => ({ i, frac: value - Math.floor(value) }))
  .sort((a, b) => b.frac - a.frac);
for (let k = 0; k < remainder; k++) rowSeatCounts[byFraction[k].i] += 1;

const seatPoints = [];
let maxRadius = INNER_RADIUS;
rowSeatCounts.forEach((count, row) => {
  const radius = INNER_RADIUS + row * ROW_GAP;
  maxRadius = Math.max(maxRadius, radius);
  for (let j = 0; j < count; j++) {
    const angle = Math.PI - (Math.PI * (j + 0.5)) / count;
    seatPoints.push({ angle, x: radius * Math.cos(angle), y: radius * Math.sin(angle) });
  }
});
seatPoints.sort((a, b) => b.angle - a.angle); // left (180°) -> right (0°)

let cursor = 0;
const series = parties.map((party, i) => {
  const data = seatPoints.slice(cursor, cursor + party.seats).map((p) => ({ x: p.x, y: p.y }));
  cursor += party.seats;
  return { name: `${party.name} (${party.seats})`, color: t.palette[i], data };
});

// --- Chart -------------------------------------------------------------------
const pad = 24;
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "parliament-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    min: -(maxRadius + pad),
    max: maxRadius + pad,
    visible: false,
  },
  yAxis: {
    min: -pad,
    max: maxRadius + pad,
    title: { text: null },
    visible: false,
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
    symbolRadius: 6,
  },
  tooltip: {
    headerFormat: "",
    pointFormatter: function () {
      return `<span style="color:${this.series.color}">●</span> ${this.series.name}`;
    },
  },
  plotOptions: {
    series: {
      animation: false,
      marker: { radius: 17, lineWidth: 0 },
      states: { hover: { enabled: false } },
    },
  },
  series,
});
