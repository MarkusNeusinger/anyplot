// anyplot.ai
// swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-08

const t = window.ANYPLOT_TOKENS;

// --- Data ---
const rawPatients = [
  { id: "PT-01", duration: 52, group: "A", ongoing: true,  events: [{t:8,type:"PR"},{t:18,type:"CR"}] },
  { id: "PT-02", duration: 48, group: "A", ongoing: false, events: [{t:6,type:"PR"},{t:36,type:"PD"}] },
  { id: "PT-03", duration: 45, group: "A", ongoing: true,  events: [{t:10,type:"PR"}] },
  { id: "PT-04", duration: 41, group: "A", ongoing: false, events: [{t:8,type:"PR"},{t:16,type:"CR"},{t:38,type:"AE"}] },
  { id: "PT-05", duration: 38, group: "A", ongoing: false, events: [{t:12,type:"PR"},{t:30,type:"PD"}] },
  { id: "PT-06", duration: 35, group: "A", ongoing: false, events: [{t:6,type:"AE"},{t:20,type:"PR"}] },
  { id: "PT-07", duration: 28, group: "A", ongoing: false, events: [{t:10,type:"PD"}] },
  { id: "PT-08", duration: 24, group: "A", ongoing: false, events: [{t:8,type:"PR"},{t:20,type:"PD"}] },
  { id: "PT-09", duration: 20, group: "A", ongoing: false, events: [{t:6,type:"AE"},{t:14,type:"PD"}] },
  { id: "PT-10", duration: 18, group: "A", ongoing: false, events: [{t:4,type:"PD"}] },
  { id: "PT-11", duration: 14, group: "A", ongoing: false, events: [{t:8,type:"AE"},{t:12,type:"PD"}] },
  { id: "PT-12", duration: 10, group: "A", ongoing: false, events: [{t:6,type:"PD"}] },
  { id: "PT-13", duration: 50, group: "B", ongoing: true,  events: [{t:6,type:"PR"},{t:14,type:"CR"}] },
  { id: "PT-14", duration: 46, group: "B", ongoing: true,  events: [{t:8,type:"PR"},{t:22,type:"CR"}] },
  { id: "PT-15", duration: 43, group: "B", ongoing: false, events: [{t:10,type:"PR"},{t:20,type:"CR"},{t:40,type:"PD"}] },
  { id: "PT-16", duration: 39, group: "B", ongoing: false, events: [{t:8,type:"PR"},{t:32,type:"PD"}] },
  { id: "PT-17", duration: 36, group: "B", ongoing: false, events: [{t:6,type:"AE"},{t:16,type:"PR"}] },
  { id: "PT-18", duration: 32, group: "B", ongoing: false, events: [{t:10,type:"PR"},{t:26,type:"PD"}] },
  { id: "PT-19", duration: 26, group: "B", ongoing: false, events: [{t:6,type:"AE"}] },
  { id: "PT-20", duration: 22, group: "B", ongoing: false, events: [{t:8,type:"PR"},{t:18,type:"PD"}] },
  { id: "PT-21", duration: 18, group: "B", ongoing: false, events: [{t:4,type:"PD"}] },
  { id: "PT-22", duration: 16, group: "B", ongoing: false, events: [{t:6,type:"AE"},{t:12,type:"PD"}] },
  { id: "PT-23", duration: 12, group: "B", ongoing: false, events: [{t:4,type:"PR"},{t:10,type:"PD"}] },
  { id: "PT-24", duration: 8,  group: "B", ongoing: false, events: [{t:4,type:"PD"}] },
  { id: "PT-25", duration: 6,  group: "B", ongoing: false, events: [{t:4,type:"AE"}] },
];

// Sort descending by duration — longest patient at top of chart
const patients = rawPatients.sort((a, b) => b.duration - a.duration);
const labels = patients.map(p => p.id);
const n = patients.length;

// Bar data per arm (null for patients in the other arm — Chart.js skips nulls)
const armAData = patients.map(p => p.group === "A" ? p.duration : null);
const armBData = patients.map(p => p.group === "B" ? p.duration : null);

// Scatter event data — y2 is a hidden linear axis aligned to the categorical y-axis.
// Alignment formula: for categorical index i (0=top), y2 = n - 1 - i
// so index 0 (top bar) → y2 = n-1 (near y2 max = top), index n-1 (bottom) → y2 = 0.
const prPts = [], crPts = [], pdPts = [], aePts = [], ongoingPts = [];
patients.forEach((p, i) => {
  const y = n - 1 - i;
  if (p.ongoing) ongoingPts.push({ x: p.duration, y });
  p.events.forEach(e => {
    const pt = { x: e.t, y };
    if (e.type === "PR") prPts.push(pt);
    else if (e.type === "CR") crPts.push(pt);
    else if (e.type === "PD") pdPts.push(pt);
    else if (e.type === "AE") aePts.push(pt);
  });
});

// --- Mount ---
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [
      {
        type: "bar",
        label: "Arm A — Experimental",
        data: armAData,
        backgroundColor: t.palette[0] + "99",
        borderColor: t.palette[0],
        borderWidth: 1.5,
        borderRadius: 4,
        yAxisID: "y",
        xAxisID: "x",
        barPercentage: 0.55,
        categoryPercentage: 0.9,
      },
      {
        type: "bar",
        label: "Arm B — Control",
        data: armBData,
        backgroundColor: t.palette[1] + "99",
        borderColor: t.palette[1],
        borderWidth: 1.5,
        borderRadius: 4,
        yAxisID: "y",
        xAxisID: "x",
        barPercentage: 0.55,
        categoryPercentage: 0.9,
      },
      {
        type: "scatter",
        label: "Partial Response (▲)",
        data: prPts,
        yAxisID: "y2",
        xAxisID: "x",
        backgroundColor: t.palette[2],
        borderColor: t.pageBg,
        borderWidth: 1.5,
        pointStyle: "triangle",
        pointRadius: 7,
        pointHoverRadius: 9,
      },
      {
        type: "scatter",
        label: "Complete Response (★)",
        data: crPts,
        yAxisID: "y2",
        xAxisID: "x",
        backgroundColor: t.palette[3],
        borderColor: t.pageBg,
        borderWidth: 1.5,
        pointStyle: "star",
        pointRadius: 9,
        pointHoverRadius: 11,
      },
      {
        type: "scatter",
        label: "Progressive Disease (◆)",
        data: pdPts,
        yAxisID: "y2",
        xAxisID: "x",
        backgroundColor: t.palette[4],
        borderColor: t.pageBg,
        borderWidth: 1.5,
        pointStyle: "rectRot",
        pointRadius: 7,
        pointHoverRadius: 9,
      },
      {
        type: "scatter",
        label: "Adverse Event (●)",
        data: aePts,
        yAxisID: "y2",
        xAxisID: "x",
        backgroundColor: t.palette[5],
        borderColor: t.pageBg,
        borderWidth: 1.5,
        pointStyle: "circle",
        pointRadius: 6,
        pointHoverRadius: 8,
      },
      {
        type: "scatter",
        label: "Ongoing at Cutoff (→)",
        data: ongoingPts,
        yAxisID: "y2",
        xAxisID: "x",
        backgroundColor: t.ink,
        borderColor: t.pageBg,
        borderWidth: 1,
        pointStyle: "triangle",
        rotation: 90,
        pointRadius: 8,
        pointHoverRadius: 10,
      },
    ],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "swimmer-clinical-timeline · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "600" },
        padding: { top: 12, bottom: 20 },
      },
      legend: {
        display: true,
        position: "bottom",
        labels: {
          color: t.inkSoft,
          font: { size: 13 },
          padding: 20,
          usePointStyle: true,
          pointStyleWidth: 16,
        },
      },
    },
    layout: {
      padding: { top: 10, right: 50, bottom: 10, left: 10 },
    },
    scales: {
      x: {
        type: "linear",
        position: "bottom",
        min: 0,
        max: 60,
        title: {
          display: true,
          text: "Time on Study (Weeks)",
          color: t.ink,
          font: { size: 15, weight: "500" },
          padding: { top: 10 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          stepSize: 10,
        },
        grid: { color: t.grid },
        border: { color: t.grid },
      },
      y: {
        type: "category",
        position: "left",
        title: {
          display: true,
          text: "Patient ID",
          color: t.ink,
          font: { size: 15, weight: "500" },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 11 },
        },
        grid: { display: false },
        border: { display: false },
      },
      // Hidden linear axis aligned to the categorical y-axis for scatter event markers.
      // Range [-0.5, n-0.5] maps cleanly: index 0 (top bar) → y2 = n-1, index n-1 → y2 = 0.
      y2: {
        type: "linear",
        display: false,
        min: -0.5,
        max: n - 0.5,
      },
    },
  },
  plugins: [
    {
      id: "bgfill",
      beforeDraw(chart) {
        const ctx = chart.canvas.getContext("2d");
        ctx.save();
        ctx.fillStyle = t.pageBg;
        ctx.fillRect(0, 0, chart.width, chart.height);
        ctx.restore();
      },
    },
  ],
});
