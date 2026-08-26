// anyplot.ai
// mohr-circle: Mohr's Circle for Stress Analysis
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-08-26

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data: 2D stress state on a steel shaft under combined bending + torsion (MPa) ---
const sigmaX = 120;
const sigmaY = 40;
const tauXY = 55;

const center = (sigmaX + sigmaY) / 2;
const radius = Math.sqrt(((sigmaX - sigmaY) / 2) ** 2 + tauXY ** 2);
const sigma1 = center + radius;
const sigma2 = center - radius;
const tauMax = radius;
const twoThetaPRad = Math.atan2(tauXY, (sigmaX - sigmaY) / 2);
const twoThetaPDeg = (twoThetaPRad * 180) / Math.PI;

// Circle outline, traced parametrically around the center
const STEPS = 200;
const circlePoints = [];
for (let i = 0; i <= STEPS; i++) {
  const angle = (2 * Math.PI * i) / STEPS;
  circlePoints.push([center + radius * Math.cos(angle), radius * Math.sin(angle)]);
}

const pointA = [sigmaX, tauXY];
const pointB = [sigmaY, -tauXY];

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    events: {
      load: function () {
        // Force equal pixel-per-unit scale on both axes so the circle renders
        // as a true circle instead of stretching to the plot area's aspect ratio.
        const chart = this;
        const xAxis = chart.xAxis[0];
        const yAxis = chart.yAxis[0];
        const scale = Math.min(chart.plotWidth / (xAxis.max - xAxis.min), chart.plotHeight / (yAxis.max - yAxis.min));
        const xMid = (xAxis.max + xAxis.min) / 2;
        const yMid = (yAxis.max + yAxis.min) / 2;
        xAxis.setExtremes(xMid - chart.plotWidth / (2 * scale), xMid + chart.plotWidth / (2 * scale), false);
        yAxis.setExtremes(yMid - chart.plotHeight / (2 * scale), yMid + chart.plotHeight / (2 * scale), false);
        chart.redraw();

        // Angle arc for the principal-plane rotation 2θp, swept from the
        // positive-σ direction (toward σ1) to the radius line center → A.
        const cx = xAxis.toPixels(center);
        const cy = yAxis.toPixels(0);
        const ax = xAxis.toPixels(pointA[0]);
        const ay = yAxis.toPixels(pointA[1]);
        const arcR = Math.min(chart.plotWidth, chart.plotHeight) * 0.14;
        // Highcharts renderer.arc angles: 0 rad = 3 o'clock (right), increasing clockwise.
        const angleToA = Math.atan2(ay - cy, ax - cx);
        const startAngle = Math.min(0, angleToA);
        const endAngle = Math.max(0, angleToA);
        chart.renderer
          .arc(cx, cy, arcR, 0, startAngle, endAngle)
          .attr({ stroke: t.inkSoft, "stroke-width": 1.5, fill: "none", dashstyle: "Dash" })
          .add();
        const midAngle = (startAngle + endAngle) / 2;
        const labelR = arcR + 26;
        chart.renderer
          .text(`2θp = ${twoThetaPDeg.toFixed(1)}°`, cx + labelR * Math.cos(midAngle), cy + labelR * Math.sin(midAngle))
          .attr({ align: "center" })
          .css({ color: t.inkSoft, fontSize: "14px" })
          .add();
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "mohr-circle · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Steel shaft under combined bending and torsion",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: { text: "Normal Stress σ (MPa)", style: { color: t.inkSoft, fontSize: "16px" } },
    min: center - radius * 1.3,
    max: center + radius * 1.3,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      { value: 0, color: t.inkSoft, width: 1, zIndex: 2 },
      { value: center, color: t.inkSoft, width: 1, dashStyle: "ShortDash", zIndex: 2 },
    ],
  },
  yAxis: {
    title: { text: "Shear Stress τ (MPa)", style: { color: t.inkSoft, fontSize: "16px" } },
    min: -radius * 1.3,
    max: radius * 1.3,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [{ value: 0, color: t.inkSoft, width: 1, zIndex: 2 }],
  },
  legend: { enabled: false },
  tooltip: {
    pointFormat: "σ = {point.x:.1f} MPa<br/>τ = {point.y:.1f} MPa",
  },
  plotOptions: {
    series: { animation: false },
  },
  series: [
    {
      name: "Mohr's Circle",
      type: "line",
      data: circlePoints,
      color: t.palette[0],
      lineWidth: 3,
      marker: { enabled: false },
      enableMouseTracking: false,
    },
    {
      name: "Diameter (A-B)",
      type: "line",
      data: [pointA, pointB],
      color: t.inkSoft,
      dashStyle: "ShortDash",
      lineWidth: 1.5,
      marker: { enabled: false },
      enableMouseTracking: false,
    },
    {
      name: "Stress Points",
      type: "scatter",
      color: t.palette[1],
      marker: { symbol: "circle", radius: 6, lineWidth: 1, lineColor: t.pageBg },
      dataLabels: {
        enabled: true,
        style: { color: t.ink, fontSize: "14px", textOutline: "none" },
        formatter: function () {
          return this.point.label;
        },
      },
      data: [
        { x: pointA[0], y: pointA[1], label: `A(${sigmaX}, ${tauXY})`, dataLabels: { align: "left", x: 10, y: -8 } },
        { x: pointB[0], y: pointB[1], label: `B(${sigmaY}, -${tauXY})`, dataLabels: { align: "right", x: -10, y: 18 } },
      ],
    },
    {
      name: "Principal Stresses",
      type: "scatter",
      color: t.palette[2],
      marker: { symbol: "diamond", radius: 7, lineWidth: 1, lineColor: t.pageBg },
      dataLabels: {
        enabled: true,
        style: { color: t.ink, fontSize: "14px", textOutline: "none" },
        formatter: function () {
          return this.point.label;
        },
      },
      data: [
        { x: sigma1, y: 0, label: `σ1 = ${sigma1.toFixed(1)}`, dataLabels: { align: "center", y: -16 } },
        { x: sigma2, y: 0, label: `σ2 = ${sigma2.toFixed(1)}`, dataLabels: { align: "center", y: -16 } },
      ],
    },
    {
      name: "Max Shear Stress",
      type: "scatter",
      color: t.palette[3],
      marker: { symbol: "triangle", radius: 7, lineWidth: 1, lineColor: t.pageBg },
      dataLabels: {
        enabled: true,
        style: { color: t.ink, fontSize: "14px", textOutline: "none" },
        formatter: function () {
          return this.point.label;
        },
      },
      data: [
        { x: center, y: tauMax, label: `τmax = ${tauMax.toFixed(1)}`, dataLabels: { align: "center", y: -14 } },
        { x: center, y: -tauMax, label: `-τmax`, dataLabels: { align: "center", y: 24 } },
      ],
    },
    {
      name: "Center",
      type: "scatter",
      color: t.ink,
      marker: { symbol: "circle", radius: 4 },
      enableMouseTracking: false,
      showInLegend: false,
      dataLabels: { enabled: false },
      data: [{ x: center, y: 0 }],
    },
  ],
});
