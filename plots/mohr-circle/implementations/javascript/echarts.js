// anyplot.ai
// mohr-circle: Mohr's Circle for Stress Analysis
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-26
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width: W, height: H } = window.ANYPLOT_SIZE;

// --- Data: bridge girder under combined bending + shear (MPa) ---------------
const sigmaX = 55;
const sigmaY = -15;
const tauXY = 30;

const center = (sigmaX + sigmaY) / 2;
const radius = Math.sqrt(((sigmaX - sigmaY) / 2) ** 2 + tauXY ** 2);
const sigma1 = center + radius;
const sigma2 = center - radius;
const tauMax = radius;
const theta2p = (Math.atan2(tauXY, sigmaX - center) * 180) / Math.PI;

// Mohr's circle outline (parametric)
const circlePoints = [];
for (let deg = 0; deg <= 360; deg++) {
  const rad = (deg * Math.PI) / 180;
  circlePoints.push([center + radius * Math.cos(rad), radius * Math.sin(rad)]);
}

// Principal-angle arc, from the reference points to the σ1 axis
const arcRadius = radius * 0.4;
const arcSteps = 40;
const arcPoints = [];
for (let i = 0; i <= arcSteps; i++) {
  const deg = (theta2p * i) / arcSteps;
  const rad = (deg * Math.PI) / 180;
  arcPoints.push([center + arcRadius * Math.cos(rad), arcRadius * Math.sin(rad)]);
}
const arcMidRad = ((theta2p / 2) * Math.PI) / 180;
const arcLabelPos = [center + arcRadius * 1.9 * Math.cos(arcMidRad), arcRadius * 1.9 * Math.sin(arcMidRad)];

// Equal padding on both axes keeps the circle a true circle: the σ-span
// (2×radius) and τ-span (2×radius) are identical by construction, and the
// grid box below is forced square, so equal source-unit spans map 1:1.
const pad = radius * 0.65;

// Imprint palette — semantic role assignment for Mohr's circle
const CLR_GEOM = t.palette[0]; // brand green — circle geometry, center, angle arc
const CLR_INPUT = t.palette[4]; // matte red (semantic: applied stress) — points A, B
const CLR_DERIVED = t.palette[2]; // blue — derived principal stresses / tau_max

// Square grid box centered in the mount so xAxis/yAxis spans render 1:1
const gridSide = Math.min(W, H) - 260;
const gridLeft = (W - gridSide) / 2 + 10;
const gridTop = (H - gridSide) / 2 + 20;

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  color: t.palette,
  title: {
    text: "mohr-circle · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: gridLeft, top: gridTop, width: gridSide, height: gridSide },
  xAxis: {
    type: "value",
    name: "Normal Stress σ (MPa)",
    nameLocation: "middle",
    nameGap: 42,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: sigma2 - pad,
    max: sigma1 + pad,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (v) => Math.round(v) },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Shear Stress τ (MPa)",
    nameLocation: "middle",
    nameGap: 56,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: -tauMax - pad,
    max: tauMax + pad,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (v) => Math.round(v) },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  series: [
    {
      // Mohr's circle outline, plus the two reference lines through the center
      type: "line",
      data: circlePoints,
      symbol: "none",
      lineStyle: { color: CLR_GEOM, width: 2.5 },
      z: 3,
      markLine: {
        symbol: "none",
        silent: true,
        label: { show: false },
        data: [
          { yAxis: 0, lineStyle: { color: t.inkSoft, width: 1, type: "solid" } },
          { xAxis: center, lineStyle: { color: t.inkSoft, width: 1, type: "dashed", opacity: 0.6 } },
        ],
      },
    },
    {
      // Diameter line connecting stress points A and B
      type: "line",
      data: [
        [sigmaX, tauXY],
        [sigmaY, -tauXY],
      ],
      symbol: "none",
      lineStyle: { color: CLR_INPUT, width: 1.5, type: "dashed", opacity: 0.55 },
      z: 2,
    },
    {
      // Principal-plane angle arc 2θp
      type: "line",
      data: arcPoints,
      symbol: "none",
      lineStyle: { color: CLR_GEOM, width: 2 },
      z: 4,
    },
    {
      // Angle label, offset past the arc tip — symbol kept tiny rather than
      // "none" because a "none" symbol also suppresses its data-item label
      type: "scatter",
      symbol: "circle",
      symbolSize: 2,
      itemStyle: { color: CLR_GEOM },
      data: [
        {
          value: arcLabelPos,
          label: {
            show: true,
            formatter: `2θp = ${theta2p.toFixed(1)}°`,
            color: CLR_GEOM,
            fontSize: 14,
            fontWeight: "bold",
          },
        },
      ],
      z: 4,
    },
    {
      // Stress points A(σx, τxy) and B(σy, −τxy)
      type: "scatter",
      symbolSize: 16,
      itemStyle: { color: CLR_INPUT, borderColor: t.pageBg, borderWidth: 2 },
      data: [
        {
          value: [sigmaX, tauXY],
          label: {
            show: true,
            formatter: `A (${sigmaX}, ${tauXY})`,
            position: "top",
            offset: [18, -6],
            color: CLR_INPUT,
            fontSize: 15,
            fontWeight: "bold",
          },
        },
        {
          value: [sigmaY, -tauXY],
          label: {
            show: true,
            formatter: `B (${sigmaY}, ${-tauXY})`,
            position: "bottom",
            offset: [-18, 6],
            color: CLR_INPUT,
            fontSize: 15,
            fontWeight: "bold",
          },
        },
      ],
      z: 5,
    },
    {
      // Principal stresses σ1, σ2 — diamond markers for derived quantities
      type: "scatter",
      symbol: "diamond",
      itemStyle: { color: CLR_DERIVED, borderColor: t.pageBg, borderWidth: 2 },
      data: [
        {
          value: [sigma2, 0],
          symbolSize: 18,
          label: {
            show: true,
            formatter: `σ₂ = ${sigma2.toFixed(1)} MPa`,
            position: "left",
            distance: 20,
            color: CLR_DERIVED,
            fontSize: 14,
            fontWeight: "bold",
          },
        },
        {
          // σ1 is the critical engineering result — emphasized with a larger marker + callout
          value: [sigma1, 0],
          symbolSize: 24,
          label: {
            show: true,
            formatter: `σ₁ = ${sigma1.toFixed(1)} MPa`,
            position: "right",
            distance: 20,
            color: CLR_DERIVED,
            fontSize: 15,
            fontWeight: "bold",
            backgroundColor: t.elevatedBg,
            borderColor: CLR_DERIVED,
            borderWidth: 1.2,
            borderRadius: 4,
            padding: [4, 8],
          },
        },
      ],
      z: 6,
    },
    {
      // Maximum shear stress τ_max at top and bottom of the circle
      type: "scatter",
      symbol: "diamond",
      symbolSize: 18,
      itemStyle: { color: CLR_DERIVED, borderColor: t.pageBg, borderWidth: 2 },
      data: [
        {
          value: [center, tauMax],
          label: {
            show: true,
            formatter: `τ_max = ${tauMax.toFixed(1)} MPa`,
            position: "top",
            distance: 16,
            color: CLR_DERIVED,
            fontSize: 14,
            fontWeight: "bold",
          },
        },
        {
          value: [center, -tauMax],
          label: {
            show: true,
            formatter: `−τ_max = −${tauMax.toFixed(1)} MPa`,
            position: "bottom",
            distance: 16,
            color: CLR_DERIVED,
            fontSize: 14,
            fontWeight: "bold",
          },
        },
      ],
      z: 6,
    },
    {
      // Circle center C
      type: "scatter",
      symbol: "circle",
      symbolSize: 10,
      itemStyle: { color: CLR_GEOM, borderColor: t.pageBg, borderWidth: 1.5 },
      data: [
        {
          value: [center, 0],
          label: {
            show: true,
            formatter: `C (${center.toFixed(0)}, 0)`,
            position: "bottom",
            offset: [20, 4],
            color: CLR_GEOM,
            fontSize: 13,
            fontWeight: "bold",
          },
        },
      ],
      z: 6,
    },
  ],
});
