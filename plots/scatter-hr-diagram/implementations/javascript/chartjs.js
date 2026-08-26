// anyplot.ai
// scatter-hr-diagram: Hertzsprung-Russell Diagram
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 78/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (LCG + Box-Muller) ----------------------------------
const rng = (() => {
  let s = 88172645;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
})();
const gaussian = () => {
  const u1 = Math.max(rng(), 1e-6);
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
};

// --- Data: synthetic stellar populations across the HR diagram -------------
// Temperature (K) and luminosity (L☉) follow rough astrophysical scaling laws
// per region; luminosity is log-scaled, temperature axis is reversed (hot→cool).
const LOG_T_SUN = Math.log10(5778);

const mainSequence = Array.from({ length: 140 }, () => {
  const logT = 3.477 + rng() * (4.602 - 3.477);
  const logL = 4.0 * (logT - LOG_T_SUN) + gaussian() * 0.22;
  return { x: 10 ** logT, y: 10 ** logL };
});

const redGiants = Array.from({ length: 25 }, () => {
  const logT = 3.477 + rng() * (3.716 - 3.477);
  const logL = 1.0 + rng() * 2.0;
  return { x: 10 ** logT, y: 10 ** logL };
});

const whiteDwarfs = Array.from({ length: 20 }, () => {
  const logT = 3.903 + rng() * (4.602 - 3.903);
  const logL = -4.3 + rng() * 2.6;
  return { x: 10 ** logT, y: 10 ** logL };
});

const supergiants = Array.from({ length: 15 }, () => {
  const logT = 3.477 + rng() * (4.477 - 3.477);
  const logL = 4.0 + rng() * 2.0;
  return { x: 10 ** logT, y: 10 ** logL };
});

const sun = [{ x: 5778, y: 1 }];

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
// Regions are colored with semantic intent: main sequence keeps the mandatory
// brand green (also the "default" population); red giants use the matte-red
// anchor (the name says red); white dwarfs use blue (they are hot, blue-white
// stars); supergiants take the remaining canonical slot (lavender). Marker
// radius scales with each region's real relative stellar size.
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "main sequence",
        data: mainSequence,
        backgroundColor: t.palette[0],
        borderColor: t.pageBg,
        borderWidth: 1,
        radius: 5,
      },
      {
        label: "red giants",
        data: redGiants,
        backgroundColor: t.palette[4],
        borderColor: t.pageBg,
        borderWidth: 1,
        radius: 11,
      },
      {
        label: "supergiants",
        data: supergiants,
        backgroundColor: t.palette[1],
        borderColor: t.pageBg,
        borderWidth: 1,
        radius: 15,
      },
      {
        label: "white dwarfs",
        data: whiteDwarfs,
        backgroundColor: t.palette[2],
        borderColor: t.pageBg,
        borderWidth: 1,
        radius: 4,
      },
      {
        // "star" is a stroke-only asterisk shape in Chart.js (no fillable
        // area), so it needs a visible borderColor, not the page-background
        // edge used by the filled region markers above.
        label: "Sun",
        data: sun,
        backgroundColor: t.ink,
        borderColor: t.ink,
        borderWidth: 3,
        radius: 15,
        pointStyle: "star",
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "Hertzsprung-Russell Diagram · scatter-hr-diagram · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 18 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 }, usePointStyle: true },
      },
    },
    scales: {
      x: {
        type: "linear",
        reverse: true,
        min: 2000,
        max: 42000,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => `${value.toLocaleString()} K`,
        },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Surface Temperature — hot → cool",
          color: t.ink,
          font: { size: 18 },
        },
      },
      y: {
        type: "logarithmic",
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Luminosity (L☉, log scale)",
          color: t.ink,
          font: { size: 18 },
        },
      },
    },
  },
});
