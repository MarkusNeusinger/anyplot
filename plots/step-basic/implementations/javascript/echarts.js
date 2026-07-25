// anyplot.ai
// step-basic: Basic Step Plot
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Thermostat setpoint schedule: the setpoint is set at each hour and holds
// constant until the next scheduled change — a textbook step function.
const hours = Array.from({ length: 25 }, (_, i) => i); // 00:00 .. 24:00

const scheduledSetpoint = (hour) => {
  if (hour < 6) return 17; // night setback
  if (hour < 9) return 21; // morning occupied
  if (hour < 16) return 19; // daytime away (energy saving)
  if (hour < 22) return 22; // evening occupied
  return 17; // night setback
};

const categories = hours.map((h) => `${String(h).padStart(2, "0")}:00`);
const setpoints = hours.map(scheduledSetpoint);

// Markers only at the hours where the setpoint actually changes.
const seriesData = setpoints.map((value, i) => {
  const isChange = i === 0 || value !== setpoints[i - 1];
  return { value, symbol: "circle", symbolSize: isChange ? 14 : 0 };
});

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "step-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  tooltip: { trigger: "axis" },
  grid: { left: 110, right: 60, top: 110, bottom: 90 },
  xAxis: {
    type: "category",
    data: categories,
    name: "Time of Day",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      interval: (index) => index % 3 === 0,
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Setpoint Temperature (°C)",
    nameLocation: "middle",
    nameGap: 65,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 15,
    max: 24,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "line",
      step: "end",
      data: seriesData,
      lineStyle: { width: 3.5, color: t.palette[0] },
      itemStyle: { color: t.palette[0] },
      areaStyle: { color: t.palette[0], opacity: 0.08 },
    },
  ],
});
