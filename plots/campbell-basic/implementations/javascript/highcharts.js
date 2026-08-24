// anyplot.ai
// campbell-basic: Campbell Diagram
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Natural frequency modes: base Hz at zero speed, Hz at max speed (linear
// gyroscopic trend — forward whirl stiffens, backward whirl softens, higher
// modes drift only slightly).
const MAX_SPEED = 6000; // RPM
const POINTS = 61; // 100 RPM steps

const modes = [
  { name: "1st Bending (Forward)", baseHz: 20, endHz: 27 },
  { name: "1st Bending (Backward)", baseHz: 20, endHz: 14 },
  { name: "2nd Bending", baseHz: 52, endHz: 57 },
  { name: "1st Torsional", baseHz: 88, endHz: 90 },
];

const modeFreq = (mode, speed) =>
  mode.baseHz + (mode.endHz - mode.baseHz) * (speed / MAX_SPEED);

const modeSeries = modes.map((mode) => ({
  name: mode.name,
  type: "line",
  data: Array.from({ length: POINTS }, (_, i) => {
    const speed = (i * MAX_SPEED) / (POINTS - 1);
    return [speed, modeFreq(mode, speed)];
  }),
  lineWidth: 3,
  marker: { enabled: false },
}));

// Engine order excitation lines: frequency = order * speed / 60 (RPM -> Hz)
const orders = [1, 2, 3];
const orderFreq = (order, speed) => (order * speed) / 60;

const orderSeries = orders.map((order) => ({
  name: `${order}x order`,
  type: "line",
  data: [
    [0, 0],
    [MAX_SPEED, orderFreq(order, MAX_SPEED)],
  ],
  color: t.ink,
  dashStyle: "Dash",
  lineWidth: 2,
  marker: { enabled: false },
  enableMouseTracking: false,
}));

// Critical speeds: where an engine order line crosses a natural frequency
// curve. Found numerically via sign change of (orderFreq - modeFreq) across
// a fine RPM sweep, then refined with linear interpolation.
const criticalSpeeds = [];
const SCAN_STEP = 5; // RPM

orders.forEach((order) => {
  modes.forEach((mode) => {
    let prevSpeed = 0;
    let prevDiff = orderFreq(order, 0) - modeFreq(mode, 0);
    for (let speed = SCAN_STEP; speed <= MAX_SPEED; speed += SCAN_STEP) {
      const diff = orderFreq(order, speed) - modeFreq(mode, speed);
      if (prevDiff === 0 || prevDiff * diff < 0) {
        const crossSpeed =
          prevSpeed + ((speed - prevSpeed) * -prevDiff) / (diff - prevDiff);
        criticalSpeeds.push([crossSpeed, orderFreq(order, crossSpeed)]);
      }
      prevSpeed = speed;
      prevDiff = diff;
    }
  });
});

const criticalSeries = {
  name: "Critical Speeds",
  type: "scatter",
  data: criticalSpeeds,
  color: t.palette[4], // matte red — semantic anchor for critical/error
  marker: { enabled: true, symbol: "diamond", radius: 7 },
};

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "campbell-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: {
      text: "Rotational Speed (RPM)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    min: 0,
    max: MAX_SPEED,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Natural Frequency (Hz)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    min: 0,
    max: 110,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false },
  },
  series: [...modeSeries, ...orderSeries, criticalSeries],
});
