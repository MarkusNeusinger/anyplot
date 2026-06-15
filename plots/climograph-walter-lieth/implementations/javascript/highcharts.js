// anyplot.ai
// climograph-walter-lieth: Walter-Lieth Climate Diagram
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 75/100 | Created: 2026-06-15

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data: Seville climate normals (1991–2020) ------------------------------
// Classic Mediterranean station with pronounced summer arid period
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const temperature   = [10.3, 12.0, 14.5, 16.5, 20.3, 25.0, 28.2, 28.4, 25.3, 20.2, 14.7, 11.2];
const precipitation = [66,   61,   49,   53,   34,   11,    1,    5,   21,   70,   68,   72];

const stationName       = "Seville (Aeropuerto)";
const elevation         = 34;
const annualMeanTemp    = 18.9;
const annualPrecipTotal = 511;

// Walter-Lieth scaling: 10 °C ≡ 20 mm (right axis max = 2 × left axis max)
// Left axis: –5 to 40 °C  →  Right axis: –10 to 80 mm
// Humid  period: precipitation bar above the temp line (P > T*2)
// Arid   period: temp line above precipitation bar (T*2 > P)

// Color tokens
const PRECIP_COLOR = t.palette[2];  // "#4467A3" — Imprint blue for precipitation
const TEMP_COLOR   = t.palette[4];  // "#AE3030" — Imprint matte-red for temperature

// Title auto-scaling
const titleText = "Seville Climate · climograph-walter-lieth · javascript · highcharts · anyplot.ai";
const titleFs   = Math.max(14, Math.round(22 * 67 / titleText.length));

// --- Chart ------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    marginTop: 100,
    marginBottom: 65,
    marginLeft: 80,
    marginRight: 90,
  },
  credits: { enabled: false },

  title: {
    text: titleText,
    align: "left",
    x: 80,
    style: { color: t.ink, fontSize: `${titleFs}px`, fontWeight: "600" },
  },

  subtitle: {
    text: `${stationName}  ·  ${elevation} m a.s.l.  ·  T̄: ${annualMeanTemp}°C  ·  P: ${annualPrecipTotal} mm/yr`,
    align: "left",
    x: 80,
    y: 44,
    style: { color: t.inkSoft, fontSize: "14px" },
  },

  xAxis: {
    categories: months,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    crosshair: false,
  },

  yAxis: [
    // Left: Temperature (°C)
    {
      id: "temp",
      title: {
        text: "Temperature (°C)",
        style: { color: TEMP_COLOR, fontSize: "16px" },
      },
      labels: {
        format: "{value} °C",
        style: { color: TEMP_COLOR, fontSize: "14px" },
      },
      tickPositions: [0, 10, 20, 30, 40],
      min: 0,
      max: 40,
      lineColor: TEMP_COLOR,
      lineWidth: 1,
      gridLineColor: t.grid,
      gridLineWidth: 1,
    },
    // Right: Precipitation (mm) — 2:1 scale relative to temperature axis
    {
      id: "precip",
      title: {
        text: "Precipitation (mm)",
        style: { color: PRECIP_COLOR, fontSize: "16px" },
      },
      labels: {
        format: "{value} mm",
        style: { color: PRECIP_COLOR, fontSize: "14px" },
      },
      tickPositions: [0, 20, 40, 60, 80],
      min: 0,
      max: 80,
      opposite: true,
      lineColor: PRECIP_COLOR,
      lineWidth: 1,
      gridLineWidth: 0,
    },
  ],

  legend: {
    enabled: true,
    align: "right",
    verticalAlign: "top",
    layout: "vertical",
    x: -10,
    y: 110,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
    symbolWidth: 28,
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    borderWidth: 1,
    padding: 10,
  },

  plotOptions: {
    series: { animation: false },
    column: {
      borderWidth: 0,
      groupPadding: 0.05,
      pointPadding: 0.02,
      opacity: 0.85,
    },
    spline: {
      lineWidth: 3,
      marker: {
        enabled: true,
        radius: 4,
        symbol: "circle",
        lineWidth: 1.5,
        lineColor: "transparent",
      },
    },
  },

  series: [
    {
      type: "column",
      name: "Precipitation",
      data: precipitation,
      color: PRECIP_COLOR,
      yAxis: 1,
      zIndex: 1,
    },
    {
      type: "spline",
      name: "Temperature",
      data: temperature,
      color: TEMP_COLOR,
      yAxis: 0,
      zIndex: 3,
      marker: {
        fillColor: TEMP_COLOR,
        lineColor: "transparent",
      },
    },
  ],
});
