// anyplot.ai
// venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 91/100 | Created: 2026-06-25

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// Symmetric 3-circle Venn: equilateral triangle, side 300 px, radius 230 px
// All coordinates in CSS px within the 1600×900 landscape mount
const circles = [
  { cx: 650, cy: 340, r: 230, color: t.palette[0] }, // A: Overhyped      — brand green
  { cx: 950, cy: 340, r: 230, color: t.palette[2] }, // B: Actually Useful — blue
  { cx: 800, cy: 600, r: 230, color: t.palette[1] }, // C: Secretly Loved  — lavender
];

// Category labels outside each circle's outer edge
const catLabels = [
  { text: 'Overhyped',       x: 395,  y: 183, align: 'center' },
  { text: 'Actually Useful', x: 1205, y: 183, align: 'center' },
  { text: 'Secretly Loved',  x: 800,  y: 862, align: 'center' },
];

// Items placed in zones — positions verified inside correct set regions
const items = [
  // A only (Overhyped, not useful, not loved)
  { label: 'NFTs',         x: 460,  y: 270 },
  { label: 'Web3',         x: 460,  y: 298 },
  { label: 'Metaverse',    x: 456,  y: 326 },
  // B only (Useful, not hyped, not loved)
  { label: 'Spreadsheets', x: 1140, y: 270 },
  { label: 'Git',          x: 1140, y: 298 },
  { label: 'Terminal',     x: 1140, y: 326 },
  // C only (Secretly loved, neither hyped nor practical)
  { label: 'Fax Machines', x: 800,  y: 790 },
  { label: 'MySpace',      x: 800,  y: 817 },
  // AB (Overhyped AND Useful)
  { label: 'AI Chatbots',   x: 800, y: 230 },
  { label: 'Cloud Storage', x: 800, y: 258 },
  // AC (Overhyped AND Secretly Loved)
  { label: 'Vinyl Records', x: 677, y: 495 },
  { label: 'Life Hacks',    x: 676, y: 522 },
  // BC (Useful AND Secretly Loved)
  { label: 'Wikipedia',    x: 923, y: 495 },
  { label: 'RSS Feeds',    x: 924, y: 522 },
  // ABC (all three) — bold/larger to signal multi-zone status
  { label: 'Podcasts',     x: 800, y: 435, abc: true },
  { label: 'Sourdough',    x: 800, y: 462, abc: true },
];

Highcharts.chart('container', {
  chart: {
    backgroundColor: 'transparent',
    plotBackgroundColor: 'transparent',
    plotBorderWidth: 0,
    plotShadow: false,
    animation: false,
    margin: [72, 20, 20, 20],
    style: { fontFamily: 'inherit' },
    events: {
      render: function () {
        if (this._venn) {
          this._venn.forEach(function (el) { el.destroy(); });
        }
        this._venn = [];
        var r = this.renderer;

        // Semi-transparent filled circles (A then B then C — C appears topmost in overlaps)
        circles.forEach(function (c) {
          this._venn.push(
            r.circle(c.cx, c.cy, c.r)
              .attr({
                fill: c.color,
                'fill-opacity': 0.18,
                stroke: c.color,
                'stroke-width': 2.5,
                'stroke-opacity': 0.6,
                zIndex: 2,
              })
              .add()
          );
        }, this);

        // Bold category labels outside each circle
        catLabels.forEach(function (lb) {
          this._venn.push(
            r.text(lb.text, lb.x, lb.y)
              .attr({ align: lb.align, zIndex: 6 })
              .css({ color: t.ink, fontSize: '18px', fontWeight: '700', fontFamily: 'Georgia, serif' })
              .add()
          );
        }, this);

        // Item labels — text-only placement (no dot markers)
        items.forEach(function (item) {
          var isABC = item.abc;
          this._venn.push(
            r.text(item.label, item.x, item.y)
              .attr({ align: 'center', zIndex: 5 })
              .css({
                color: t.ink,
                fontSize: isABC ? '16px' : '14px',
                fontWeight: isABC ? '700' : '400',
              })
              .add()
          );
        }, this);
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: 'venn-labeled-items · javascript · highcharts · anyplot.ai',
    style: { color: t.ink, fontSize: '22px', fontWeight: '600' },
    margin: 8,
  },
  subtitle: {
    text: 'A Cultural Taxonomy of Technology Trends',
    style: { color: t.inkSoft, fontSize: '14px', fontStyle: 'italic' },
  },
  xAxis: { visible: false },
  yAxis: { visible: false },
  legend: { enabled: false },
  plotOptions: { series: { animation: false } },
  series: [],
  tooltip: { enabled: false },
});
