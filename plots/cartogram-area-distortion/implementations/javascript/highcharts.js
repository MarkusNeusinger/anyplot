// anyplot.ai
// cartogram-area-distortion: Cartogram with Area Distortion by Data Value
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-20

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// All 50 US states and DC on a tile grid map (col = west→east, row =
// north→south, the common statebins layout). Every state owns one equal-area
// tile, and the tiles of neighbouring states touch; the circle drawn inside
// each tile has area ∝ population, so its size against the tile is the area
// distortion. Fill encodes a GDP-per-capita tier. population in millions
// (2023 est.), gdpPerCapita in thousand USD.
const states = [
  { name: "AK", col: 0, row: 0, population: 0.7, gdpPerCapita: 80 },
  { name: "ME", col: 10, row: 0, population: 1.4, gdpPerCapita: 56 },
  { name: "WI", col: 5, row: 1, population: 5.9, gdpPerCapita: 65 },
  { name: "VT", col: 9, row: 1, population: 0.6, gdpPerCapita: 57 },
  { name: "NH", col: 10, row: 1, population: 1.4, gdpPerCapita: 71 },
  { name: "WA", col: 0, row: 2, population: 7.9, gdpPerCapita: 87 },
  { name: "ID", col: 1, row: 2, population: 2.0, gdpPerCapita: 52 },
  { name: "MT", col: 2, row: 2, population: 1.1, gdpPerCapita: 62 },
  { name: "ND", col: 3, row: 2, population: 0.8, gdpPerCapita: 78 },
  { name: "MN", col: 4, row: 2, population: 5.7, gdpPerCapita: 77 },
  { name: "IL", col: 5, row: 2, population: 12.6, gdpPerCapita: 79 },
  { name: "MI", col: 6, row: 2, population: 10.0, gdpPerCapita: 60 },
  { name: "NY", col: 8, row: 2, population: 19.6, gdpPerCapita: 96 },
  { name: "MA", col: 9, row: 2, population: 7.0, gdpPerCapita: 91 },
  { name: "OR", col: 0, row: 3, population: 4.2, gdpPerCapita: 71 },
  { name: "NV", col: 1, row: 3, population: 3.2, gdpPerCapita: 66 },
  { name: "WY", col: 2, row: 3, population: 0.6, gdpPerCapita: 74 },
  { name: "SD", col: 3, row: 3, population: 0.9, gdpPerCapita: 68 },
  { name: "IA", col: 4, row: 3, population: 3.2, gdpPerCapita: 65 },
  { name: "IN", col: 5, row: 3, population: 6.8, gdpPerCapita: 63 },
  { name: "OH", col: 6, row: 3, population: 11.8, gdpPerCapita: 64 },
  { name: "PA", col: 7, row: 3, population: 13.0, gdpPerCapita: 65 },
  { name: "NJ", col: 8, row: 3, population: 9.3, gdpPerCapita: 74 },
  { name: "CT", col: 9, row: 3, population: 3.6, gdpPerCapita: 82 },
  { name: "RI", col: 10, row: 3, population: 1.1, gdpPerCapita: 61 },
  { name: "CA", col: 0, row: 4, population: 39.0, gdpPerCapita: 91 },
  { name: "UT", col: 1, row: 4, population: 3.4, gdpPerCapita: 70 },
  { name: "CO", col: 2, row: 4, population: 5.9, gdpPerCapita: 75 },
  { name: "NE", col: 3, row: 4, population: 2.0, gdpPerCapita: 72 },
  { name: "MO", col: 4, row: 4, population: 6.2, gdpPerCapita: 60 },
  { name: "KY", col: 5, row: 4, population: 4.5, gdpPerCapita: 53 },
  { name: "WV", col: 6, row: 4, population: 1.8, gdpPerCapita: 51 },
  { name: "VA", col: 7, row: 4, population: 8.7, gdpPerCapita: 69 },
  { name: "MD", col: 8, row: 4, population: 6.2, gdpPerCapita: 70 },
  { name: "DE", col: 9, row: 4, population: 1.0, gdpPerCapita: 78 },
  { name: "AZ", col: 1, row: 5, population: 7.4, gdpPerCapita: 55 },
  { name: "NM", col: 2, row: 5, population: 2.1, gdpPerCapita: 55 },
  { name: "KS", col: 3, row: 5, population: 2.9, gdpPerCapita: 65 },
  { name: "AR", col: 4, row: 5, population: 3.0, gdpPerCapita: 50 },
  { name: "TN", col: 5, row: 5, population: 7.1, gdpPerCapita: 60 },
  { name: "NC", col: 6, row: 5, population: 10.8, gdpPerCapita: 63 },
  { name: "SC", col: 7, row: 5, population: 5.4, gdpPerCapita: 52 },
  { name: "DC", col: 8, row: 5, population: 0.7, gdpPerCapita: 220 },
  { name: "OK", col: 3, row: 6, population: 4.0, gdpPerCapita: 58 },
  { name: "LA", col: 4, row: 6, population: 4.6, gdpPerCapita: 58 },
  { name: "MS", col: 5, row: 6, population: 2.9, gdpPerCapita: 44 },
  { name: "AL", col: 6, row: 6, population: 5.1, gdpPerCapita: 51 },
  { name: "GA", col: 7, row: 6, population: 11.0, gdpPerCapita: 64 },
  { name: "HI", col: 0, row: 7, population: 1.4, gdpPerCapita: 63 },
  { name: "TX", col: 3, row: 7, population: 30.5, gdpPerCapita: 74 },
  { name: "FL", col: 8, row: 7, population: 22.6, gdpPerCapita: 60 },
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
        custom: { population: s.population, gdpPerCapita: s.gdpPerCapita },
        dataLabels: inside
          ? { verticalAlign: "middle", style: { color: tier.label } }
          : { verticalAlign: "top", distance: radius + 3, style: { color: t.ink } },
      };
    }),
}));

// Legend entry for the reference tiles, which the SVG renderer draws below.
series.push({
  name: "Equal-area reference tile, one per state",
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
      // tiles of neighbouring states share their edges: the undistorted
      // baseline each population-scaled circle is measured against. A
      // page-coloured hairline keeps the individual tiles readable. Redrawn on
      // every render because the pixel positions follow the axes.
      render: function () {
        if (this.tileGroup) this.tileGroup.destroy();
        this.tileGroup = this.renderer.g("reference-tiles").attr({ zIndex: 1 }).add();
        const xa = this.xAxis[0];
        const ya = this.yAxis[0];
        states.forEach((s) => {
          const x0 = xa.toPixels(s.col - 0.5);
          const y0 = ya.toPixels(s.row - 0.5);
          this.renderer
            .rect(x0, y0, xa.toPixels(s.col + 0.5) - x0, ya.toPixels(s.row + 0.5) - y0)
            .attr({ fill: t.grid, stroke: t.pageBg, "stroke-width": 1.5 })
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
    text: "Circle area ∝ population (millions, 2023) · fill = GDP-per-capita tier · grey tile = undistorted reference, the same size for every state · tile position follows rough state geography",
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
      "Population: {point.custom.population}M<br/>GDP per capita: ${point.custom.gdpPerCapita}k",
  },
  series,
});
