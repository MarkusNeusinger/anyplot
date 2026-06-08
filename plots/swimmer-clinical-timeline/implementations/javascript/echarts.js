// anyplot.ai
// swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 86/100 | Created: 2026-06-08

const t = window.ANYPLOT_TOKENS;

// Imprint palette — data colors stable across light/dark; only chrome tokens flip
const ARM_A_COLOR   = t.palette[0];  // #009E73 — Arm A (brand green, first series)
const ARM_B_COLOR   = t.palette[1];  // #C475FD — Arm B (lavender)
const PARTIAL_COLOR = t.palette[3];  // #BD8233 — ochre: partial response
const CR_COLOR      = t.palette[2];  // #4467A3 — blue: complete response
const PD_COLOR      = t.palette[4];  // #AE3030 — matte red: progressive disease (semantic bad/loss)
const ONGOING_COLOR = t.inkSoft;     // theme-adaptive neutral: ongoing patients

// 25 simulated Phase II oncology patients, sorted longest → shortest duration
const patients = [
  { id: "PT-001", arm: "A", duration: 52, ongoing: true,  events: [{time:  8, type: "PR"}, {time: 20, type: "CR"}] },
  { id: "PT-024", arm: "B", duration: 50, ongoing: true,  events: [{time: 16, type: "CR"}] },
  { id: "PT-002", arm: "A", duration: 48, ongoing: true,  events: [{time:  6, type: "PR"}] },
  { id: "PT-014", arm: "B", duration: 46, ongoing: true,  events: [{time: 10, type: "PR"}, {time: 24, type: "CR"}] },
  { id: "PT-003", arm: "A", duration: 44, ongoing: true,  events: [{time: 12, type: "CR"}] },
  { id: "PT-015", arm: "B", duration: 42, ongoing: true,  events: [{time:  8, type: "PR"}] },
  { id: "PT-004", arm: "A", duration: 40, ongoing: false, events: [{time:  8, type: "PR"}] },
  { id: "PT-005", arm: "A", duration: 38, ongoing: true,  events: [{time: 10, type: "CR"}] },
  { id: "PT-006", arm: "A", duration: 36, ongoing: false, events: [{time: 36, type: "PD"}] },
  { id: "PT-025", arm: "B", duration: 35, ongoing: false, events: [{time: 12, type: "PR"}] },
  { id: "PT-016", arm: "B", duration: 34, ongoing: false, events: [{time: 14, type: "CR"}] },
  { id: "PT-007", arm: "A", duration: 32, ongoing: false, events: [{time:  6, type: "PR"}, {time: 32, type: "PD"}] },
  { id: "PT-017", arm: "B", duration: 30, ongoing: false, events: [{time:  6, type: "PR"}, {time: 30, type: "PD"}] },
  { id: "PT-008", arm: "A", duration: 28, ongoing: false, events: [{time: 28, type: "PD"}] },
  { id: "PT-018", arm: "B", duration: 26, ongoing: false, events: [{time: 26, type: "PD"}] },
  { id: "PT-009", arm: "A", duration: 24, ongoing: false, events: [{time:  8, type: "PR"}] },
  { id: "PT-019", arm: "B", duration: 22, ongoing: false, events: [{time:  8, type: "PR"}, {time: 22, type: "PD"}] },
  { id: "PT-010", arm: "A", duration: 20, ongoing: false, events: [{time: 20, type: "PD"}] },
  { id: "PT-020", arm: "B", duration: 18, ongoing: false, events: [{time: 18, type: "PD"}] },
  { id: "PT-011", arm: "A", duration: 16, ongoing: false, events: [{time: 16, type: "PD"}] },
  { id: "PT-021", arm: "B", duration: 14, ongoing: false, events: [{time: 14, type: "PD"}] },
  { id: "PT-012", arm: "A", duration: 12, ongoing: false, events: [{time: 12, type: "PD"}] },
  { id: "PT-022", arm: "B", duration: 10, ongoing: false, events: [{time: 10, type: "PD"}] },
  { id: "PT-013", arm: "A", duration:  8, ongoing: false, events: [{time:  8, type: "PD"}] },
  { id: "PT-023", arm: "B", duration:  6, ongoing: false, events: [{time:  6, type: "PD"}] },
];

const patientIds = patients.map(p => p.id);

// Build scatter data arrays by event type (y = patient array index → category axis)
const prData = [], crData = [], pdData = [], ongoingData = [];
patients.forEach((p, i) => {
  p.events.forEach(ev => {
    if (ev.type === "PR") prData.push([ev.time, i]);
    if (ev.type === "CR") crData.push([ev.time, i]);
    if (ev.type === "PD") pdData.push([ev.time, i]);
  });
  if (p.ongoing) ongoingData.push([p.duration + 1.5, i]);
});

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "swimmer-clinical-timeline · javascript · echarts · anyplot.ai",
    left: "center",
    top: 22,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" }
  },
  legend: {
    bottom: 16,
    left: "center",
    textStyle: { color: t.inkSoft, fontSize: 13 },
    itemGap: 22,
    itemWidth: 20,
    itemHeight: 12,
    data: [
      { name: "Arm A (n=13)", icon: "rect" },
      { name: "Arm B (n=12)", icon: "rect" },
      { name: "Partial Response", icon: "triangle" },
      { name: "Complete Response", icon: "diamond" },
      { name: "Progressive Disease", icon: "path://M0,8L-7,-4L7,-4Z" },
      { name: "Ongoing", icon: "arrow" },
    ]
  },
  grid: {
    left: 16,
    right: 50,
    top: 86,
    bottom: 90,
    containLabel: true
  },
  xAxis: {
    type: "value",
    min: 0,
    max: 56,
    interval: 8,
    name: "Time on Study (Weeks)",
    nameLocation: "middle",
    nameGap: 44,
    nameTextStyle: { color: t.inkSoft, fontSize: 15 },
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } }
  },
  yAxis: {
    type: "category",
    data: patientIds,
    inverse: true,
    axisLabel: { color: t.inkSoft, fontSize: 12 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false }
  },
  series: [
    // Legend proxy series for treatment arms (empty data — legend appearance only)
    {
      name: "Arm A (n=13)",
      type: "scatter",
      symbol: "rect",
      symbolSize: [20, 10],
      data: [],
      itemStyle: { color: ARM_A_COLOR }
    },
    {
      name: "Arm B (n=12)",
      type: "scatter",
      symbol: "rect",
      symbolSize: [20, 10],
      data: [],
      itemStyle: { color: ARM_B_COLOR }
    },
    // Duration bars — per-item arm color via itemStyle
    {
      name: "_bars",
      type: "bar",
      barMaxWidth: 16,
      data: patients.map(p => ({
        value: p.duration,
        itemStyle: {
          color: p.arm === "A" ? ARM_A_COLOR : ARM_B_COLOR,
          borderRadius: [0, 2, 2, 0]
        }
      }))
    },
    // Partial Response (PR) — upward triangle, ochre
    {
      name: "Partial Response",
      type: "scatter",
      symbol: "triangle",
      symbolSize: 13,
      data: prData,
      itemStyle: { color: PARTIAL_COLOR },
      z: 4
    },
    // Complete Response (CR) — diamond, blue
    {
      name: "Complete Response",
      type: "scatter",
      symbol: "diamond",
      symbolSize: 15,
      data: crData,
      itemStyle: { color: CR_COLOR },
      z: 4
    },
    // Progressive Disease (PD) — downward triangle, matte red (semantic bad/disease)
    {
      name: "Progressive Disease",
      type: "scatter",
      symbol: "triangle",
      symbolRotate: 180,
      symbolSize: 13,
      data: pdData,
      itemStyle: { color: PD_COLOR },
      z: 4
    },
    // Ongoing — rightward arrow past bar end (symbolRotate 270 = down→right for ECharts arrow)
    {
      name: "Ongoing",
      type: "scatter",
      symbol: "arrow",
      symbolRotate: 270,
      symbolSize: 13,
      data: ongoingData,
      itemStyle: { color: ONGOING_COLOR },
      z: 4
    }
  ]
});
