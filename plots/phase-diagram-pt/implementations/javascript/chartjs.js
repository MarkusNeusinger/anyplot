// anyplot.ai
// phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 86/100 | Created: 2026-06-08

const t = window.ANYPLOT_TOKENS;

// CO2 phase diagram constants (pressures in atm, temperatures in K)
const R     = 8.314;
const T_tp  = 216.55, P_tp  = 5.18;   // triple point
const T_cp  = 304.13, P_cp  = 72.8;   // critical point
const H_sub = 25200;                   // J/mol — sublimation enthalpy
const H_vap = 16500;                   // J/mol — effective vaporization enthalpy
const dPdT  = 108;                     // atm/K  — CO2 fusion curve slope (positive)

// Sublimation curve (solid ↔ gas): 150 K → triple point
const sublimation = [];
for (let T = 150; T <= T_tp; T += 1.5) {
  sublimation.push({ x: T, y: P_tp * Math.exp((H_sub / R) * (1 / T_tp - 1 / T)) });
}
sublimation.push({ x: T_tp, y: P_tp });

// Vaporization curve (liquid ↔ gas): triple point → critical point
const vaporization = [{ x: T_tp, y: P_tp }];
for (let T = T_tp + 2; T <= T_cp; T += 2) {
  vaporization.push({ x: T, y: P_tp * Math.exp((H_vap / R) * (1 / T_tp - 1 / T)) });
}
vaporization.push({ x: T_cp, y: P_cp });

// Fusion curve (solid ↔ liquid): steep positive slope for CO2
const fusion = [];
for (let i = 0; i <= 24; i++) {
  const P = P_tp + i * 21;
  fusion.push({ x: T_tp + (P - P_tp) / dPdT, y: P });
}

// Mount canvas
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Plugin: draw phase-region labels directly on the canvas
const regionPlugin = {
  id: "phaseRegions",
  afterDraw({ ctx, scales: { x, y } }) {
    const regions = [
      { lines: ["SOLID"],                T: 176,  P: 100   },
      { lines: ["LIQUID"],               T: 248,  P: 32    },
      { lines: ["GAS"],                  T: 278,  P: 0.05  },
      { lines: ["SUPER-", "CRITICAL"],   T: 322,  P: 260   },
    ];
    ctx.save();
    ctx.font = "bold 20px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.globalAlpha = 0.5;
    ctx.fillStyle = t.inkSoft;
    const lineH = 26;
    for (const { lines, T, P } of regions) {
      const px = x.getPixelForValue(T);
      const py = y.getPixelForValue(P);
      const offset = (lines.length - 1) * lineH / 2;
      lines.forEach((line, i) => ctx.fillText(line, px, py - offset + i * lineH));
    }
    ctx.restore();
  },
};

const title = "CO₂ Phase Diagram · phase-diagram-pt · javascript · chartjs · anyplot.ai";
const titleSize = Math.max(16, Math.round(22 * 67 / title.length));

new Chart(canvas, {
  type: "scatter",
  plugins: [regionPlugin],
  data: {
    datasets: [
      {
        label: "Solid–Gas (Sublimation)",
        data: sublimation,
        borderColor: t.palette[0],
        backgroundColor: "transparent",
        showLine: true,
        borderWidth: 3.5,
        pointRadius: 0,
      },
      {
        label: "Liquid–Gas (Vaporization)",
        data: vaporization,
        borderColor: t.palette[1],
        backgroundColor: "transparent",
        showLine: true,
        borderWidth: 3.5,
        pointRadius: 0,
      },
      {
        label: "Solid–Liquid (Fusion)",
        data: fusion,
        borderColor: t.palette[2],
        backgroundColor: "transparent",
        showLine: true,
        borderWidth: 3.5,
        pointRadius: 0,
      },
      {
        label: `Triple Point  ${T_tp} K, ${P_tp} atm`,
        data: [{ x: T_tp, y: P_tp }],
        backgroundColor: t.palette[3],
        borderColor: t.ink,
        borderWidth: 2,
        pointRadius: 13,
        pointHoverRadius: 15,
        pointStyle: "star",
        showLine: false,
      },
      {
        label: `Critical Point  ${T_cp} K, ${P_cp} atm`,
        data: [{ x: T_cp, y: P_cp }],
        backgroundColor: t.palette[4],
        borderColor: t.ink,
        borderWidth: 2,
        pointRadius: 13,
        pointHoverRadius: 15,
        pointStyle: "rectRot",
        showLine: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 10, right: 40, bottom: 10, left: 10 } },
    plugins: {
      title: {
        display: true,
        text: title,
        color: t.ink,
        font: { size: titleSize, weight: "500" },
        padding: { top: 10, bottom: 22 },
      },
      legend: {
        position: "bottom",
        labels: {
          color: t.inkSoft,
          font: { size: 15 },
          usePointStyle: true,
          padding: 24,
          boxWidth: 20,
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 140,
        max: 340,
        title: {
          display: true,
          text: "Temperature (K)",
          color: t.ink,
          font: { size: 18 },
          padding: { top: 10 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 20,
        },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
      },
      y: {
        type: "logarithmic",
        min: 0.005,
        max: 700,
        title: {
          display: true,
          text: "Pressure (atm)",
          color: t.ink,
          font: { size: 18 },
          padding: { bottom: 10 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback(value) {
            const pow = Math.round(Math.log10(value));
            const expected = Math.pow(10, pow);
            if (Math.abs(value - expected) / expected < 0.002) {
              return expected < 1 ? expected.toFixed(-pow) : String(Math.round(expected));
            }
            return "";
          },
        },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
      },
    },
  },
});
