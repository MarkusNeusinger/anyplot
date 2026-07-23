// anyplot.ai
// heatmap-calendar: Basic Calendar Heatmap
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-07-23

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily open-source commit counts across two calendar years, generated with a
// small fixed-seed LCG (weekday-biased, with a handful of streak/rest cycles).
let seed = 42;
function nextRand() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}

function datesInYear(year) {
  const dates = [];
  const start = new Date(Date.UTC(year, 0, 1));
  const end = new Date(Date.UTC(year, 11, 31));
  for (let d = start; d <= end; d.setUTCDate(d.getUTCDate() + 1)) {
    dates.push(d.toISOString().slice(0, 10));
  }
  return dates;
}

function commitSeries(year) {
  return datesInYear(year).map((dateStr) => {
    const dow = new Date(dateStr + "T00:00:00Z").getUTCDay(); // 0=Sun..6=Sat
    const weekdayBias = dow === 0 || dow === 6 ? 1.5 : 6;
    const streak = Math.sin(new Date(dateStr).getTime() / 6.5e8) > 0.3 ? 3 : 0;
    const value = Math.round(weekdayBias * nextRand() + streak * nextRand());
    return [dateStr, value];
  });
}

const years = [2023, 2024];
const seriesData = years.map((year) => commitSeries(year));
const maxValue = Math.max(...seriesData.flat().map((d) => d[1]));

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
const calendarTop = 130;
const calendarHeight = 260;
const calendarGap = 70;

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: [
    {
      text: "heatmap-calendar · javascript · echarts · anyplot.ai",
      left: "center",
      top: 20,
      textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
    },
    ...years.map((year, i) => ({
      text: String(year),
      left: 90,
      top: calendarTop + i * (calendarHeight + calendarGap) - 42,
      textStyle: { color: t.ink, fontSize: 18, fontWeight: 600 },
    })),
  ],
  visualMap: {
    min: 0,
    max: maxValue,
    calculable: true,
    orient: "horizontal",
    left: "center",
    bottom: 10,
    inRange: { color: t.seq },
    textStyle: { color: t.inkSoft, fontSize: 13 },
  },
  calendar: years.map((year, i) => ({
    top: calendarTop + i * (calendarHeight + calendarGap),
    left: 90,
    right: 60,
    cellSize: [24, calendarHeight / 7],
    range: String(year),
    splitLine: { lineStyle: { color: t.grid, width: 1 } },
    itemStyle: { borderColor: t.pageBg, borderWidth: 3 },
    dayLabel: {
      firstDay: 1,
      nameMap: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
      color: t.inkSoft,
      fontSize: 13,
    },
    monthLabel: { color: t.inkSoft, fontSize: 14 },
    yearLabel: { show: false },
  })),
  series: years.map((year, i) => ({
    type: "heatmap",
    coordinateSystem: "calendar",
    calendarIndex: i,
    data: seriesData[i],
  })),
});
