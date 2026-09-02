// anyplot.ai
// mosaic-categorical: Mosaic Plot for Categorical Association Analysis
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const W = window.ANYPLOT_SIZE.width;
const H = window.ANYPLOT_SIZE.height;

// --- Data (in-memory, deterministic) ----------------------------------------
// Contingency table: performance rating counts by department.
const departments = ["Engineering", "Sales", "Marketing", "Support"];
const ratings = ["Exceeds", "Meets", "Below"];
const counts = [
  [42, 58, 10], // Engineering
  [35, 70, 25], // Sales
  [20, 45, 15], // Marketing
  [15, 38, 12], // Support
];

const colTotals = counts.map((row) => row.reduce((a, b) => a + b, 0));
const grandTotal = colTotals.reduce((a, b) => a + b, 0);

// --- Layout (custom drawing area — Highcharts core has no mosaic series) ----
const marginLeft = 70;
const marginRight = 200;
const marginTop = 96;
const marginBottom = 76;
const plotWidth = W - marginLeft - marginRight;
const plotHeight = H - marginTop - marginBottom;
const colGap = 6;
const rowGap = 3;

const availableWidth = plotWidth - (departments.length - 1) * colGap;
let cursorX = marginLeft;
const colX = [];
const colWidth = [];
departments.forEach((_, i) => {
  const w = (colTotals[i] / grandTotal) * availableWidth;
  colX.push(cursorX);
  colWidth.push(w);
  cursorX += w + colGap;
});

function textColorFor(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.6 ? "#1A1A17" : "#FFFFFF";
}

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    spacing: [0, 0, 0, 0],
    events: {
      load() {
        const r = this.renderer;

        // Percentage gridlines + axis title (shared conditional-share scale)
        [0, 25, 50, 75, 100].forEach((pct) => {
          const y = marginTop + plotHeight * (1 - pct / 100);
          r.path(["M", marginLeft, y, "L", marginLeft + plotWidth, y])
            .attr({ stroke: t.grid, "stroke-width": 1 })
            .add();
          r.text(`${pct}%`, marginLeft - 12, y + 5)
            .attr({ align: "right" })
            .css({ color: t.inkSoft, fontSize: "14px" })
            .add();
        });
        r.text("Rating share within department", 24, marginTop + plotHeight / 2)
          .attr({ align: "center", rotation: -90 })
          .css({ color: t.inkSoft, fontSize: "16px" })
          .add();

        // Mosaic rectangles: column width ∝ department share, row height ∝ rating share
        departments.forEach((dept, i) => {
          const availableHeight = plotHeight - (ratings.length - 1) * rowGap;
          let cursorY = marginTop;
          ratings.forEach((rating, j) => {
            const cellHeight = (counts[i][j] / colTotals[i]) * availableHeight;
            const fill = t.palette[j];
            r.rect(colX[i], cursorY, colWidth[i], cellHeight, 2)
              .attr({ fill, stroke: t.pageBg, "stroke-width": 2 })
              .add();

            if (colWidth[i] > 46 && cellHeight > 28) {
              r.text(String(counts[i][j]), colX[i] + colWidth[i] / 2, cursorY + cellHeight / 2 + 5)
                .attr({ align: "center" })
                .css({ color: textColorFor(fill), fontSize: "14px", fontWeight: "600" })
                .add();
            }
            cursorY += cellHeight + rowGap;
          });

          // Column label (first categorical variable)
          r.text(dept, colX[i] + colWidth[i] / 2, marginTop + plotHeight + 26)
            .attr({ align: "center" })
            .css({ color: t.inkSoft, fontSize: "14px" })
            .add();
        });
        r.text("Department  ·  column width ∝ headcount", marginLeft + plotWidth / 2, H - 14)
          .attr({ align: "center" })
          .css({ color: t.inkSoft, fontSize: "16px" })
          .add();

        // Legend (second categorical variable)
        const legendX = marginLeft + plotWidth + 28;
        ratings.forEach((rating, j) => {
          const legendY = marginTop + j * 30;
          r.rect(legendX, legendY, 16, 16, 2).attr({ fill: t.palette[j] }).add();
          r.text(rating, legendX + 24, legendY + 13)
            .css({ color: t.inkSoft, fontSize: "14px" })
            .add();
        });
        r.text("Performance rating", legendX, marginTop - 24)
          .css({ color: t.inkSoft, fontSize: "14px", fontWeight: "600" })
          .add();
      },
    },
  },
  credits: { enabled: false },
  title: {
    text: "mosaic-categorical · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: { visible: false },
  yAxis: { visible: false },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: { series: { animation: false } },
  series: [],
});
