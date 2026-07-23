// anyplot.ai
// heatmap-calendar: Basic Calendar Heatmap
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-07-23

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

const MONTH_ABBR = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

function busiestWeek(series) {
  let bestStart = 0;
  let bestSum = -1;
  for (let start = 0; start <= series.length - 7; start++) {
    const sum = series
      .slice(start, start + 7)
      .reduce((acc, [, value]) => acc + value, 0);
    if (sum > bestSum) {
      bestSum = sum;
      bestStart = start;
    }
  }
  const week = series.slice(bestStart, bestStart + 7);
  const dates = new Set(week.map(([dateStr]) => dateStr));
  const fmt = (dateStr) => {
    const d = new Date(dateStr + "T00:00:00Z");
    return `${MONTH_ABBR[d.getUTCMonth()]} ${d.getUTCDate()}`;
  };
  return { dates, label: `${fmt(week[0][0])} – ${fmt(week[6][0])}` };
}

const years = [2023, 2024];
const seriesData = years.map((year) => commitSeries(year));
const maxValue = Math.max(...seriesData.flat().map((d) => d[1]));
const busiestWeeks = seriesData.map((series) => busiestWeek(series));
const highlightedData = seriesData.map((series, i) =>
  series.map(([dateStr, value]) =>
    busiestWeeks[i].dates.has(dateStr)
      ? { value: [dateStr, value], itemStyle: { borderColor: t.amber, borderWidth: 2 } }
      : [dateStr, value],
  ),
);

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
    ...years.map((year, i) => ({
      text: `Busiest week: ${busiestWeeks[i].label}`,
      right: 60,
      top: calendarTop + i * (calendarHeight + calendarGap) - 42,
      textAlign: "right",
      textStyle: { color: t.amber, fontSize: 13, fontWeight: 500 },
    })),
    {
      text: "Commits per day",
      left: "center",
      bottom: 34,
      textStyle: { color: t.inkSoft, fontSize: 12, fontWeight: 400 },
    },
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
    data: highlightedData[i],
  })),
});
