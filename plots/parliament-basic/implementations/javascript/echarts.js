// anyplot.ai
// parliament-basic: Parliament Seat Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Faculty Senate composition by academic division — a semicircular "seat
// chart" reads identically whether the body is a legislature or, as here, a
// university senate, so we pick the non-political application from the spec.
const divisions = [
  { name: "Sciences", seats: 34 },
  { name: "Engineering", seats: 26 },
  { name: "Business", seats: 24 },
  { name: "Social Sciences", seats: 30 },
  { name: "Humanities", seats: 22 },
  { name: "Health Sciences", seats: 44 },
];
const totalSeats = divisions.reduce((sum, d) => sum + d.seats, 0);

// --- Seat layout: concentric arcs, equal-density row algorithm --------------
const outerRadius = 100;
const innerRadius = 40;
const numRows = Math.min(12, Math.max(4, Math.round(Math.sqrt(totalSeats) / 2)));
const rowSpacing = (outerRadius - innerRadius) / (numRows - 1);

// Row weight is proportional to arc length (∝ radius) at fixed 180° span, so
// seats-per-row scales with radius and dot spacing stays roughly constant.
const rowRadii = Array.from({ length: numRows }, (_, i) => innerRadius + i * rowSpacing);
const weightSum = rowRadii.reduce((sum, r) => sum + r, 0);
const seatsPerRow = rowRadii.map((r) => Math.round((totalSeats * r) / weightSum));
seatsPerRow[seatsPerRow.length - 1] += totalSeats - seatsPerRow.reduce((sum, n) => sum + n, 0);

const seatPositions = [];
rowRadii.forEach((radius, rowIndex) => {
  const count = seatsPerRow[rowIndex];
  for (let j = 0; j < count; j += 1) {
    const angleDeg = count === 1 ? 90 : 180 - (j * 180) / (count - 1);
    const angleRad = (angleDeg * Math.PI) / 180;
    seatPositions.push({
      x: radius * Math.cos(angleRad),
      y: radius * Math.sin(angleRad),
      angle: angleDeg,
    });
  }
});
// Left-to-right fill: sort by angle (180°=left … 0°=right), then hand out
// contiguous blocks to each division in list order.
seatPositions.sort((a, b) => b.angle - a.angle);

let cursor = 0;
const seriesData = divisions.map((division, i) => {
  const block = seatPositions.slice(cursor, cursor + division.seats);
  cursor += division.seats;
  return {
    name: `${division.name} (${division.seats})`,
    type: "scatter",
    data: block.map((p) => [p.x, p.y]),
    itemStyle: { color: t.palette[i], borderColor: t.pageBg, borderWidth: 1 },
  };
});

// --- Coordinate system: preserve 1:1 aspect so seats stay circular ----------
const dotDiameter = rowSpacing * 0.8;
const pad = dotDiameter / 2;
const xRange = 2 * (outerRadius + pad);
const yRange = outerRadius + 2 * pad;

const topReserved = 70;
const bottomReserved = 110;
const sideReserved = 80;
const availableW = size.width - 2 * sideReserved;
const availableH = size.height - topReserved - bottomReserved;
const scale = Math.min(availableW / xRange, availableH / yRange);
const gridWidth = scale * xRange;
const gridHeight = scale * yRange;
const gridLeft = sideReserved + (availableW - gridWidth) / 2;
const gridTop = topReserved + (availableH - gridHeight) / 2;

// --- Title (length-scaled per anyplot title-fontsize rule) ------------------
const titleText = "Faculty Senate Composition · parliament-basic · javascript · echarts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / titleText.length));

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: titleText,
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  legend: {
    bottom: 24,
    left: "center",
    itemWidth: 16,
    itemHeight: 16,
    textStyle: { color: t.inkSoft, fontSize: 15 },
    itemGap: 20,
  },
  grid: { left: gridLeft, top: gridTop, width: gridWidth, height: gridHeight },
  xAxis: {
    type: "value",
    min: -(outerRadius + pad),
    max: outerRadius + pad,
    show: false,
  },
  yAxis: {
    type: "value",
    min: -pad,
    max: outerRadius + pad,
    show: false,
  },
  series: seriesData.map((s) => ({
    ...s,
    symbolSize: dotDiameter * scale,
  })),
});
