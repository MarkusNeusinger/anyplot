// anyplot.ai
// climograph-walter-lieth: Walter-Lieth Climate Diagram
// Library: highcharts 13.1.1 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Semantic colors follow the meteorological convention of Walter-Lieth
// diagrams: blue for precipitation and the humid period, red for temperature
// and the arid period. The two pastel fills are fixed tints of those colors,
// so they read the same on the light and the dark page.
const PRECIP_COLOR = t.palette[2]; // Imprint blue
const TEMP_COLOR = t.palette[4]; // Imprint matte red
const PRECIP_TINT = Highcharts.color(PRECIP_COLOR).tweenTo(Highcharts.color("#FFFFFF"), 0.5);
const ARID_TINT = Highcharts.color(TEMP_COLOR).tweenTo(Highcharts.color("#FFFFFF"), 0.5);

// Columns: set these to your data's column names
const MONTH = "Month"; // role: month
const TEMPERATURE = "Temperature (°C)"; // role: temperature
const PRECIPITATION = "Precipitation (mm)"; // role: precipitation
const STATION = "Station"; // role: station_name
const ELEVATION = "Elevation (m a.s.l.)"; // role: elevation

// Data: replace this block with your own records, one object per month
// Seville (Aeropuerto) climate normals 1991–2020, a Mediterranean station
// with a pronounced summer arid period.
const data = [
  { [MONTH]: "Jan", [TEMPERATURE]: 10.3, [PRECIPITATION]: 66, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "Feb", [TEMPERATURE]: 12.0, [PRECIPITATION]: 61, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "Mar", [TEMPERATURE]: 14.5, [PRECIPITATION]: 49, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "Apr", [TEMPERATURE]: 16.5, [PRECIPITATION]: 53, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "May", [TEMPERATURE]: 20.3, [PRECIPITATION]: 34, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "Jun", [TEMPERATURE]: 25.0, [PRECIPITATION]: 11, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "Jul", [TEMPERATURE]: 28.2, [PRECIPITATION]: 1, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "Aug", [TEMPERATURE]: 28.4, [PRECIPITATION]: 5, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "Sep", [TEMPERATURE]: 25.3, [PRECIPITATION]: 21, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "Oct", [TEMPERATURE]: 20.2, [PRECIPITATION]: 70, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "Nov", [TEMPERATURE]: 14.7, [PRECIPITATION]: 68, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
  { [MONTH]: "Dec", [TEMPERATURE]: 11.2, [PRECIPITATION]: 72, [STATION]: "Seville (Aeropuerto)", [ELEVATION]: 34 },
];

// Plot: reads only data and the constants above
const months = data.map((d) => d[MONTH]);
const temp = data.map((d) => d[TEMPERATURE]);
const precip = data.map((d) => d[PRECIPITATION]);
const n = data.length;
const annualMeanTemp = temp.reduce((sum, v) => sum + v, 0) / n;
const annualPrecipTotal = precip.reduce((sum, v) => sum + v, 0);

// Walter-Lieth scaling: 10 °C ≡ 20 mm, so the precipitation axis spans twice
// the temperature axis and both zeros share one baseline.
const tempMin = Math.min(0, Math.floor(Math.min(...temp) / 10) * 10);
const precipMax = Math.ceil(Math.max(...precip, 2 * Math.max(...temp)) / 20) * 20;
const tempTicks = Array.from({ length: (precipMax / 2 - tempMin) / 10 + 1 }, (_, k) => tempMin + 10 * k);

// The temperature line is straight between monthly means, so the fills can
// follow it exactly. The year is a cycle: at the outer bar edges the line
// ends at the December–January midpoint.
const yearEdge = (temp[n - 1] + temp[0]) / 2;
const tempLine = [
  { x: -0.5, y: yearEdge, marker: { enabled: false } },
  ...temp.map((y, x) => ({ x, y })),
  { x: n - 0.5, y: yearEdge, marker: { enabled: false } },
];

// The fills between the temperature line (as 2T in mm) and the bar tops are
// three stacked areas over the same x positions: a transparent base up to the
// lower of the two, then the humid band (P > 2T) and the arid band (2T > P).
// The positions are each bar's edges and centre plus every point where the
// line crosses the bar top, so a band switches exactly at a crossing. A tiny
// inset at the inner bar edges lets the bar top step there.
const EDGE_INSET = 1e-3;
const fillBase = [];
const fillHumid = [];
const fillArid = [];
precip.forEach((p, i) => {
  const knots = [
    [i - 0.5 + (i > 0 ? EDGE_INSET : 0), temp[(i + n - 1) % n] + temp[i]],
    [i, 2 * temp[i]],
    [i + 0.5 - (i < n - 1 ? EDGE_INSET : 0), temp[i] + temp[(i + 1) % n]],
  ];
  knots
    .flatMap(([x, v], k) => {
      const [x0, v0] = knots[Math.max(k - 1, 0)];
      const crosses = (v0 - p) * (v - p) < 0;
      return crosses ? [[x0 + ((p - v0) / (v - v0)) * (x - x0), p], [x, v]] : [[x, v]];
    })
    .forEach(([x, v]) => {
      fillBase.push([x, Math.min(p, v)]);
      fillHumid.push([x, Math.max(p - v, 0)]);
      fillArid.push([x, Math.max(v - p, 0)]);
    });
});

const titleText = "Seville Climate · climograph-walter-lieth · javascript · highcharts · anyplot.ai";
const titleFs = Math.max(14, Math.round((22 * 67) / titleText.length));
const fillSeries = { type: "area", yAxis: 1, lineWidth: 0, enableMouseTracking: false, zIndex: 1 };

Highcharts.chart("container", {
  palette: { colorScheme: t.theme },
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    marginTop: 100,
    marginBottom: 110,
    marginLeft: 90,
    marginRight: 100,
    events: {
      // Frost months (mean below 0 °C) as blocks just beneath the baseline.
      // Seville has none, so nothing is drawn for this station.
      render: function () {
        if (this.frostGroup) this.frostGroup.destroy();
        this.frostGroup = this.renderer.g("frost").attr({ zIndex: 4 }).add();
        const xa = this.xAxis[0];
        temp.forEach((v, i) => {
          if (v >= 0) return;
          const x0 = xa.toPixels(i - 0.5);
          this.renderer
            .rect(x0, this.plotTop + this.plotHeight, xa.toPixels(i + 0.5) - x0, 8)
            .attr({ fill: PRECIP_COLOR })
            .add(this.frostGroup);
        });
      },
    },
  },
  credits: { enabled: false },

  title: {
    text: titleText,
    align: "left",
    x: 80,
    style: { color: t.ink, fontSize: `${titleFs}px`, fontWeight: "600" },
  },

  subtitle: {
    text: `${data[0][STATION]}  ·  ${data[0][ELEVATION]} m a.s.l.  ·  T̄: ${annualMeanTemp.toFixed(1)} °C  ·  P: ${Math.round(annualPrecipTotal)} mm/yr`,
    align: "left",
    x: 80,
    y: 44,
    style: { color: t.inkSoft, fontSize: "14px" },
  },

  xAxis: {
    categories: months,
    min: 0,
    max: n - 1,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },

  // The axis lines carry the series colours; text stays in the theme ink.
  yAxis: [
    {
      title: { text: TEMPERATURE, style: { color: t.inkSoft, fontSize: "16px" } },
      labels: { format: "{value} °C", style: { color: t.inkSoft, fontSize: "14px" } },
      tickPositions: tempTicks,
      lineColor: TEMP_COLOR,
      lineWidth: 2,
      gridLineColor: t.grid,
      gridLineWidth: 1,
    },
    {
      title: { text: PRECIPITATION, style: { color: t.inkSoft, fontSize: "16px" } },
      labels: {
        formatter: function () {
          return this.value < 0 ? "" : `${this.value} mm`;
        },
        style: { color: t.inkSoft, fontSize: "14px" },
      },
      tickPositions: tempTicks.map((v) => 2 * v),
      opposite: true,
      reversedStacks: false,
      lineColor: PRECIP_COLOR,
      lineWidth: 2,
      gridLineWidth: 0,
    },
  ],

  legend: {
    enabled: true,
    align: "center",
    verticalAlign: "bottom",
    layout: "horizontal",
    itemDistance: 28,
    itemStyle: { color: t.inkSoft, fontSize: "14px", fontWeight: "400" },
    itemHoverStyle: { color: t.ink },
    symbolWidth: 28,
    symbolHeight: 14,
    symbolRadius: 2,
  },

  tooltip: { shared: true },

  plotOptions: {
    series: { animation: false },
    column: {
      pointPadding: 0,
      groupPadding: 0,
      borderWidth: 1,
      borderColor: t.pageBg,
    },
    area: {
      stacking: "normal",
      fillOpacity: 1,
      marker: { enabled: false },
      states: { hover: { enabled: false } },
    },
  },

  series: [
    {
      type: "column",
      name: "Precipitation",
      data: precip,
      color: PRECIP_TINT,
      yAxis: 1,
      zIndex: 0,
      legendIndex: 1,
      tooltip: { valueSuffix: " mm" },
    },
    { ...fillSeries, name: "Below both curves", data: fillBase, fillOpacity: 0, showInLegend: false },
    { ...fillSeries, name: "Humid period (P > 2T)", data: fillHumid, color: PRECIP_COLOR, legendIndex: 2 },
    { ...fillSeries, name: "Arid period (2T > P)", data: fillArid, color: ARID_TINT, legendIndex: 3 },
    {
      type: "line",
      name: "Temperature",
      data: tempLine,
      color: TEMP_COLOR,
      lineWidth: 3,
      yAxis: 0,
      zIndex: 3,
      legendIndex: 0,
      marker: { enabled: true, radius: 5, symbol: "circle", fillColor: TEMP_COLOR, lineWidth: 0 },
      tooltip: { valueSuffix: " °C" },
    },
  ],
});
