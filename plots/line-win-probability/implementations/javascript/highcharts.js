// anyplot.ai
// line-win-probability: Win Probability Chart
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-21

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME;

// Deterministic LCG for reproducible play-by-play data
function lcg(seed) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 0x100000000;
  };
}

const rand = lcg(42);

// Key scoring plays: [playNumber, wpDelta, shortLabel]
const keyPlays = [
  [18,  0.22, "Home TD"],
  [36, -0.20, "Away TD"],
  [55, -0.14, "Away FG"],
  [72,  0.21, "Home TD"],
  [89, -0.27, "Pick-six"],
  [113, 0.38, "Game-winning TD"],
];

// Build play-by-play win probability (120 plays, NFL AFC Wild Card)
const TOTAL_PLAYS = 120;
let wp = 0.50;
const seriesData = Array.from({ length: TOTAL_PLAYS + 1 }, (_, i) => ({ x: i, y: 0 }));

for (let i = 0; i <= TOTAL_PLAYS; i++) {
  seriesData[i].y = parseFloat((wp * 100).toFixed(1));
  if (i < TOTAL_PLAYS) {
    const play = keyPlays.find(p => p[0] === i);
    const eventDelta = play ? play[1] : 0;
    const noise = (rand() - 0.5) * 0.036;
    const meanRevert = (0.50 - wp) * 0.018;
    wp = Math.min(0.99, Math.max(0.01, wp + eventDelta + noise + meanRevert));
  }
}
// Home team wins: drive to 99%
seriesData[TOTAL_PLAYS].y = 99.2;

// Annotate key plays: marker at play+1 so wp has already updated
for (const [playNum, , label] of keyPlays) {
  const markerIdx = Math.min(playNum + 1, TOTAL_PLAYS);
  const point = seriesData[markerIdx];
  point.marker = {
    enabled: true,
    radius: 5,
    fillColor: t.ink,
    lineWidth: 2,
    lineColor: t.pageBg,
  };
  point.dataLabels = {
    enabled: true,
    useHTML: false,
    format: label,
    style: {
      color: t.inkSoft,
      fontSize: "12px",
      fontWeight: "normal",
      textOutline: "none",
    },
    y: point.y > 50 ? -16 : 18,
    align: "center",
  };
}

// Quarter boundary dotted lines (no label — x-axis formatter already shows Q2/Q3/Q4)
const quarterLines = [30, 60, 90].map((q) => ({
  value: q,
  color: t.grid,
  dashStyle: "dot",
  width: 1,
  zIndex: 2,
}));

Highcharts.chart("container", {
  chart: {
    type: "area",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    marginTop: 90,
    marginBottom: 72,
    marginLeft: 88,
    marginRight: 32,
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "line-win-probability · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Home 21 – Away 17  |  NFL AFC Wild Card",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: 0,
    max: TOTAL_PLAYS,
    tickPositions: [0, 30, 60, 90, 120],
    title: {
      text: "Play Number",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: {
      style: { color: t.inkSoft, fontSize: "13px" },
      formatter() {
        const map = { 0: "Start", 30: "Q2", 60: "Q3", 90: "Q4", 120: "Final" };
        return map[this.value] !== undefined ? map[this.value] : String(this.value);
      },
    },
    plotLines: quarterLines,
  },
  yAxis: {
    min: 0,
    max: 100,
    tickInterval: 25,
    title: {
      text: "Home Win Probability",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: {
      format: "{value}%",
      style: { color: t.inkSoft, fontSize: "13px" },
    },
    plotLines: [{
      value: 50,
      color: t.inkSoft,
      width: 1.5,
      zIndex: 5,
      label: {
        text: "50%",
        align: "right",
        x: -8,
        style: { color: t.inkSoft, fontSize: "12px" },
      },
    }],
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false },
    area: {
      threshold: 50,
      color: t.palette[0],          // Brand green — home team leading
      negativeColor: t.palette[4],  // Matte red — home team trailing
      fillOpacity: THEME === "dark" ? 0.32 : 0.38,
      lineWidth: 2.5,
      dataLabels: { enabled: false },
      marker: {
        enabled: false,
        states: { hover: { enabled: false } },
      },
    },
  },
  series: [{
    name: "Home Win Probability",
    data: seriesData,
  }],
});
