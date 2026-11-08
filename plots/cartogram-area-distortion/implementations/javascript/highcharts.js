// anyplot.ai
// cartogram-area-distortion: Cartogram with Area Distortion by Data Value
// Library: highcharts 13.1.1 | JavaScript 22.23.4
// Quality: 85/100 | Updated: 2026-11-08

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// All 50 US states and DC on a tile grid map (col = west→east, row =
// north→south, the common statebins layout). Every state owns one equal-area
// tile, and the tiles of neighbouring states touch; the circle drawn inside
// each tile has area ∝ population, so its size against the tile is the area
// distortion. Fill encodes a GDP-per-capita tier. population in millions
// (2023 est.), gdpPerCapita in thousand USD, landArea in thousand sq mi.
const states = [
  { name: "AK", col: 0, row: 0, population: 0.7, gdpPerCapita: 80, landArea: 571 },
  { name: "ME", col: 10, row: 0, population: 1.4, gdpPerCapita: 56, landArea: 30.8 },
  { name: "WI", col: 5, row: 1, population: 5.9, gdpPerCapita: 65, landArea: 54.2 },
  { name: "VT", col: 9, row: 1, population: 0.6, gdpPerCapita: 57, landArea: 9.2 },
  { name: "NH", col: 10, row: 1, population: 1.4, gdpPerCapita: 71, landArea: 9.0 },
  { name: "WA", col: 0, row: 2, population: 7.9, gdpPerCapita: 87, landArea: 66.5 },
  { name: "ID", col: 1, row: 2, population: 2.0, gdpPerCapita: 52, landArea: 82.6 },
  { name: "MT", col: 2, row: 2, population: 1.1, gdpPerCapita: 62, landArea: 145.5 },
  { name: "ND", col: 3, row: 2, population: 0.8, gdpPerCapita: 78, landArea: 69.0 },
  { name: "MN", col: 4, row: 2, population: 5.7, gdpPerCapita: 77, landArea: 79.6 },
  { name: "IL", col: 5, row: 2, population: 12.6, gdpPerCapita: 79, landArea: 55.5 },
  { name: "MI", col: 6, row: 2, population: 10.0, gdpPerCapita: 60, landArea: 56.5 },
  { name: "NY", col: 8, row: 2, population: 19.6, gdpPerCapita: 96, landArea: 47.1 },
  { name: "MA", col: 9, row: 2, population: 7.0, gdpPerCapita: 91, landArea: 7.8 },
  { name: "OR", col: 0, row: 3, population: 4.2, gdpPerCapita: 71, landArea: 96.0 },
  { name: "NV", col: 1, row: 3, population: 3.2, gdpPerCapita: 66, landArea: 109.8 },
  { name: "WY", col: 2, row: 3, population: 0.6, gdpPerCapita: 74, landArea: 97.1 },
  { name: "SD", col: 3, row: 3, population: 0.9, gdpPerCapita: 68, landArea: 75.8 },
  { name: "IA", col: 4, row: 3, population: 3.2, gdpPerCapita: 65, landArea: 55.9 },
  { name: "IN", col: 5, row: 3, population: 6.8, gdpPerCapita: 63, landArea: 35.8 },
  { name: "OH", col: 6, row: 3, population: 11.8, gdpPerCapita: 64, landArea: 40.9 },
  { name: "PA", col: 7, row: 3, population: 13.0, gdpPerCapita: 65, landArea: 44.7 },
  { name: "NJ", col: 8, row: 3, population: 9.3, gdpPerCapita: 74, landArea: 7.4 },
  { name: "CT", col: 9, row: 3, population: 3.6, gdpPerCapita: 82, landArea: 4.8 },
  { name: "RI", col: 10, row: 3, population: 1.1, gdpPerCapita: 61, landArea: 1.0 },
  { name: "CA", col: 0, row: 4, population: 39.0, gdpPerCapita: 91, landArea: 155.8 },
  { name: "UT", col: 1, row: 4, population: 3.4, gdpPerCapita: 70, landArea: 82.2 },
  { name: "CO", col: 2, row: 4, population: 5.9, gdpPerCapita: 75, landArea: 103.6 },
  { name: "NE", col: 3, row: 4, population: 2.0, gdpPerCapita: 72, landArea: 76.8 },
  { name: "MO", col: 4, row: 4, population: 6.2, gdpPerCapita: 60, landArea: 68.7 },
  { name: "KY", col: 5, row: 4, population: 4.5, gdpPerCapita: 53, landArea: 39.5 },
  { name: "WV", col: 6, row: 4, population: 1.8, gdpPerCapita: 51, landArea: 24.0 },
  { name: "VA", col: 7, row: 4, population: 8.7, gdpPerCapita: 69, landArea: 39.5 },
  { name: "MD", col: 8, row: 4, population: 6.2, gdpPerCapita: 70, landArea: 9.7 },
  { name: "DE", col: 9, row: 4, population: 1.0, gdpPerCapita: 78, landArea: 1.9 },
  { name: "AZ", col: 1, row: 5, population: 7.4, gdpPerCapita: 55, landArea: 113.6 },
  { name: "NM", col: 2, row: 5, population: 2.1, gdpPerCapita: 55, landArea: 121.3 },
  { name: "KS", col: 3, row: 5, population: 2.9, gdpPerCapita: 65, landArea: 81.8 },
  { name: "AR", col: 4, row: 5, population: 3.0, gdpPerCapita: 50, landArea: 52.0 },
  { name: "TN", col: 5, row: 5, population: 7.1, gdpPerCapita: 60, landArea: 41.2 },
  { name: "NC", col: 6, row: 5, population: 10.8, gdpPerCapita: 63, landArea: 48.6 },
  { name: "SC", col: 7, row: 5, population: 5.4, gdpPerCapita: 52, landArea: 30.1 },
  { name: "DC", col: 8, row: 5, population: 0.7, gdpPerCapita: 220, landArea: 0.06 },
  { name: "OK", col: 3, row: 6, population: 4.0, gdpPerCapita: 58, landArea: 68.6 },
  { name: "LA", col: 4, row: 6, population: 4.6, gdpPerCapita: 58, landArea: 43.2 },
  { name: "MS", col: 5, row: 6, population: 2.9, gdpPerCapita: 44, landArea: 46.9 },
  { name: "AL", col: 6, row: 6, population: 5.1, gdpPerCapita: 51, landArea: 50.6 },
  { name: "GA", col: 7, row: 6, population: 11.0, gdpPerCapita: 64, landArea: 57.5 },
  { name: "HI", col: 0, row: 7, population: 1.4, gdpPerCapita: 63, landArea: 6.4 },
  { name: "TX", col: 3, row: 7, population: 30.5, gdpPerCapita: 74, landArea: 261.2 },
  { name: "FL", col: 8, row: 7, population: 22.6, gdpPerCapita: 60, landArea: 53.6 },
];

// --- Layout ------------------------------------------------------------------
// Fixed top and bottom margins make the plot height known before the render,
// so the side margins can give every grid cell the same width and height:
// square tiles that touch their neighbours, and a circle scale that fits them.
const cols = Math.max(...states.map((s) => s.col)) + 1;
const rows = Math.max(...states.map((s) => s.row)) + 1;
const MARGIN_TOP = 86;
const MARGIN_BOTTOM = 52;
const cell = (window.ANYPLOT_SIZE.height - MARGIN_TOP - MARGIN_BOTTOM) / rows;
const marginSide = (window.ANYPLOT_SIZE.width - cell * cols) / 2;

// Area ∝ value → radius ∝ sqrt(value), with no additive minimum, so a state
// with twice the population covers twice the area. The most populous state's
// circle nearly fills its tile.
const maxPopulation = Math.max(...states.map((s) => s.population));
const MAX_RADIUS = cell * 0.47;
const LABEL_INSIDE_RADIUS = 15; // smaller circles carry their label below them

// The undistorted reference: an inset of the same grid in the empty south-east
// corner where each state's square has area ∝ its land area, so the reader
// sees how big each state is on a normal map next to how big it is by people.
const INSET_CELL = 32;
const INSET_RIGHT = window.ANYPLOT_SIZE.width - 16;
const INSET_BOTTOM = window.ANYPLOT_SIZE.height - MARGIN_BOTTOM;
const insetLeft = INSET_RIGHT - INSET_CELL * cols;
const insetTop = INSET_BOTTOM - INSET_CELL * rows;
const maxLandArea = Math.max(...states.map((s) => s.landArea));

// The core bundle has no colorAxis module, so the GDP-per-capita tiers are
// three ordinary series: ordered steps of imprint_seq (low → high), each with
// a native legend entry. Labels inside a circle take the ink that contrasts
// with its fill (dark on green 5.1:1, white on teal 4.5:1 and blue 5.7:1).
const tiers = [
  { name: "GDP per capita < $60k", below: 60, color: t.seq[0], label: "#1A1A17" },
  {
    name: "GDP per capita $60–74k",
    below: 75,
    color: Highcharts.color(t.seq[0]).tweenTo(Highcharts.color(t.seq[1]), 0.5),
    label: "#FFFFFF",
  },
  { name: "GDP per capita ≥ $75k", below: Infinity, color: t.seq[1], label: "#FFFFFF" },
];

const series = tiers.map((tier, i) => ({
  name: tier.name,
  color: tier.color,
  data: states
    .filter((s) => s.gdpPerCapita < tier.below && (i === 0 || s.gdpPerCapita >= tiers[i - 1].below))
    .map((s) => {
      const radius = MAX_RADIUS * Math.sqrt(s.population / maxPopulation);
      const inside = radius >= LABEL_INSIDE_RADIUS;
      return {
        name: s.name,
        x: s.col,
        y: s.row,
        marker: { radius },
        custom: { population: s.population, gdpPerCapita: s.gdpPerCapita, landArea: s.landArea },
        dataLabels: inside
          ? { verticalAlign: "middle", style: { color: tier.label } }
          : { verticalAlign: "top", distance: radius + 3, style: { color: t.ink } },
      };
    }),
}));

// Legend entry for the equal-area tiles, which the SVG renderer draws below.
series.push({
  name: "Equal-area tile, one per state",
  color: t.grid,
  marker: { symbol: "square", radius: 8, fillColor: t.grid, lineWidth: 0 },
  enableMouseTracking: false,
  data: [],
});

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  palette: { colorScheme: t.theme },
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    marginTop: MARGIN_TOP,
    marginBottom: MARGIN_BOTTOM,
    marginLeft: marginSide,
    marginRight: marginSide,
    style: { fontFamily: "inherit" },
    events: {
      // One equal-area tile per state, exactly one grid cell in size, so the
      // tiles of neighbouring states share their edges: the baseline each
      // population-scaled circle is measured against. A page-coloured hairline
      // keeps the individual tiles readable. The land-area inset follows in the
      // same group. Redrawn on every render because the pixel positions follow
      // the axes.
      render: function () {
        if (this.tileGroup) this.tileGroup.destroy();
        const r = this.renderer;
        this.tileGroup = r.g("reference-tiles").attr({ zIndex: 1 }).add();
        const xa = this.xAxis[0];
        const ya = this.yAxis[0];
        states.forEach((s) => {
          const x0 = xa.toPixels(s.col - 0.5);
          const y0 = ya.toPixels(s.row - 0.5);
          r.rect(x0, y0, xa.toPixels(s.col + 0.5) - x0, ya.toPixels(s.row + 0.5) - y0)
            .attr({ fill: t.grid, stroke: t.pageBg, "stroke-width": 1.5 })
            .add(this.tileGroup);
        });

        // Inset: square side ∝ sqrt(land area), centred in its cell, so the
        // square areas compare like the states on an ordinary map.
        r.text("Undistorted: square area ∝ land area", insetLeft, insetTop - 10)
          .css({ color: t.inkSoft, fontSize: "13px", fontWeight: "600" })
          .add(this.tileGroup);
        states.forEach((s) => {
          const side = INSET_CELL * 0.96 * Math.sqrt(s.landArea / maxLandArea);
          const cx = insetLeft + (s.col + 0.5) * INSET_CELL;
          const cy = insetTop + (s.row + 0.5) * INSET_CELL;
          r.rect(cx - INSET_CELL / 2, cy - INSET_CELL / 2, INSET_CELL, INSET_CELL)
            .attr({ fill: t.grid, stroke: t.pageBg, "stroke-width": 1 })
            .add(this.tileGroup);
          r.rect(cx - side / 2, cy - side / 2, side, side)
            .attr({ fill: t.inkSoft })
            .add(this.tileGroup);
        });
      },
    },
  },
  credits: { enabled: false },
  title: {
    text: "cartogram-area-distortion · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "US states and DC resized by population against a contiguous equal-area tile grid",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  caption: {
    text: "Circle area ∝ population (millions, 2023) · fill = GDP-per-capita tier · inset = the same grid sized by land area, the undistorted geography · tile position follows rough state geography",
    align: "center",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: -0.5,
    max: cols - 0.5,
    visible: false,
  },
  yAxis: {
    min: -0.5,
    max: rows - 0.5,
    startOnTick: false,
    endOnTick: false,
    reversed: true,
    visible: false,
  },
  // The legend floats over the empty tiles north of the Great Plains, inside
  // the grid's own footprint.
  legend: {
    enabled: true,
    floating: true,
    layout: "vertical",
    align: "left",
    verticalAlign: "top",
    x: marginSide + cell,
    y: MARGIN_TOP + 4,
    itemMarginBottom: 6,
    itemStyle: { color: t.inkSoft, fontSize: "14px", fontWeight: "400" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      // The series radius sizes the legend dots; every point sets its own.
      marker: { symbol: "circle", radius: 7, lineWidth: 0 },
      dataLabels: {
        enabled: true,
        format: "{point.name}",
        align: "center",
        style: { fontSize: "13px", fontWeight: "600", textOutline: "none" },
      },
    },
  },
  tooltip: {
    pointFormat:
      "Population: {point.custom.population}M<br/>GDP per capita: ${point.custom.gdpPerCapita}k<br/>Land area: {point.custom.landArea}k sq mi",
  },
  series,
});
