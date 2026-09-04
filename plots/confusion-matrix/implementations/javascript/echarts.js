// anyplot.ai
// confusion-matrix: Confusion Matrix Heatmap
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-04

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// A pet-photo classifier's confusion matrix on a 500-image held-out test set.
// Rows = true label, columns = predicted label.
const classNames = ["Cat", "Dog", "Bird", "Rabbit", "Fish"];
const matrix = [
  [104, 8, 4, 3, 1], // Cat
  [10, 112, 3, 4, 1], // Dog
  [5, 4, 76, 3, 2], // Bird
  [4, 5, 2, 57, 2], // Rabbit
  [2, 1, 3, 2, 82], // Fish
];

const heatmapData = [];
matrix.forEach((row, rowIdx) => {
  const rowTotal = row.reduce((sum, v) => sum + v, 0);
  row.forEach((value, colIdx) => {
    const pct = (value / rowTotal) * 100;
    heatmapData.push({
      value: [colIdx, rowIdx, value],
      label: { formatter: `${value}\n${pct.toFixed(0)}%` },
      itemStyle:
        colIdx === rowIdx
          ? { borderColor: t.ink, borderWidth: 3 }
          : { borderColor: t.pageBg, borderWidth: 2 },
    });
  });
});

// --- Title (length-scaled fontsize) -----------------------------------------
const title = "Pet Photo Classifier · confusion-matrix · javascript · echarts · anyplot.ai";
const titleFontSize = Math.max(15, Math.round(22 * Math.min(1, 67 / title.length)));

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  grid: { left: 140, right: 60, top: 130, bottom: 190 },
  xAxis: {
    type: "category",
    data: classNames,
    name: "Predicted Label",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    position: "top",
    axisLabel: { color: t.inkSoft, fontSize: 16 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitArea: { show: false },
  },
  yAxis: {
    type: "category",
    data: classNames,
    inverse: true,
    name: "True Label",
    nameLocation: "middle",
    nameGap: 90,
    nameTextStyle: { color: t.ink, fontSize: 18 },
    axisLabel: { color: t.inkSoft, fontSize: 16 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitArea: { show: false },
  },
  visualMap: {
    min: 0,
    max: 112,
    calculable: true,
    orient: "horizontal",
    left: "center",
    bottom: 20,
    inRange: { color: t.seq },
    textStyle: { color: t.inkSoft, fontSize: 14 },
  },
  series: [
    {
      type: "heatmap",
      data: heatmapData,
      label: {
        show: true,
        color: "#FFFDF6",
        textBorderColor: "#1A1A17",
        textBorderWidth: 3,
        fontSize: 15,
        fontWeight: 600,
        lineHeight: 20,
      },
      emphasis: {
        itemStyle: { shadowBlur: 0 },
      },
    },
  ],
});
