// anyplot.ai
// phase-diagram: Phase Diagram (State Space Plot)
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data: damped pendulum phase portrait -----------------------------------
// d(theta)/dt = omega
// d(omega)/dt = -2*zeta*omega0*omega - omega0^2*sin(theta)
// RK4 integration, fixed dt, fully deterministic. Each trajectory uses its own
// damping ratio to reveal contrasting qualitative behavior (slow lingering
// spiral vs quick collapse) rather than three copies of the same regime.
const omega0 = 1.5;
const dt = 0.02;

function derivatives(theta, omega, zeta) {
  return [omega, -2 * zeta * omega0 * omega - omega0 * omega0 * Math.sin(theta)];
}

// Run each trajectory for ~5 damping time-constants so lightly-damped
// (slow-converging) and heavily-damped (fast-converging) cases both settle
// near the equilibrium visually, instead of using one fixed step count that
// under-runs slow trajectories and over-runs fast ones. Clamped to the
// spec's 200-2000 point guidance.
function stepsFor(zeta) {
  const timeConstant = 1 / (zeta * omega0);
  return Math.min(2000, Math.max(200, Math.round((5 * timeConstant) / dt)));
}

function integrate(theta0, omegaState0, zeta) {
  let theta = theta0;
  let omega = omegaState0;
  const points = [{ x: theta, y: omega }];
  const steps = stepsFor(zeta);
  for (let i = 0; i < steps; i++) {
    const [k1t, k1o] = derivatives(theta, omega, zeta);
    const [k2t, k2o] = derivatives(theta + (dt / 2) * k1t, omega + (dt / 2) * k1o, zeta);
    const [k3t, k3o] = derivatives(theta + (dt / 2) * k2t, omega + (dt / 2) * k2o, zeta);
    const [k4t, k4o] = derivatives(theta + dt * k3t, omega + dt * k3o, zeta);
    theta += (dt / 6) * (k1t + 2 * k2t + 2 * k3t + k4t);
    omega += (dt / 6) * (k1o + 2 * k2o + 2 * k3o + k4o);
    points.push({ x: theta, y: omega });
  }
  return points;
}

const initialConditions = [
  { theta0: 2.6, omega0State: 0.0, zeta: 0.15, label: "θ₀ = 2.6 rad, ω₀ = 0, ζ = 0.15" },
  { theta0: -2.4, omega0State: 1.6, zeta: 0.05, label: "θ₀ = -2.4 rad, ω₀ = 1.6, ζ = 0.05" },
  { theta0: 1.0, omega0State: -2.0, zeta: 0.4, label: "θ₀ = 1.0 rad, ω₀ = -2.0, ζ = 0.4" },
];

const trajectories = initialConditions.map((ic, i) => ({
  color: t.palette[i],
  label: ic.label,
  points: integrate(ic.theta0, ic.omega0State, ic.zeta),
}));

// Convert a hex color to rgba() with a given alpha, so each trajectory's
// segments can fade in from faint (start) to fully opaque (equilibrium) as a
// time-direction cue, without changing hue between light/dark themes.
function withAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Datasets ------------------------------------------------------------
const trajectoryDatasets = trajectories.map((traj) => ({
  label: traj.label,
  data: traj.points,
  showLine: true,
  borderColor: traj.color,
  pointStyle: "line",
  borderWidth: 3,
  pointRadius: 0,
  tension: 0,
  segment: {
    // Fade each segment in from 25% to 100% opacity along the trajectory so
    // the flow direction toward the equilibrium is visible at a glance.
    borderColor: (ctx) => {
      const progress = ctx.p0DataIndex / (traj.points.length - 1);
      return withAlpha(traj.color, 0.25 + 0.75 * progress);
    },
  },
}));

const startDatasets = trajectories.map((traj) => ({
  label: "",
  data: [traj.points[0]],
  showLine: false,
  pointStyle: "circle",
  pointRadius: 8,
  backgroundColor: traj.color,
  borderColor: t.pageBg,
  borderWidth: 2,
}));

const equilibriumDataset = {
  label: "Equilibrium (θ=0, ω=0)",
  data: [{ x: 0, y: 0 }],
  showLine: false,
  pointStyle: "crossRot",
  pointRadius: 12,
  borderWidth: 3,
  backgroundColor: t.ink,
  borderColor: t.ink,
};

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [...trajectoryDatasets, ...startDatasets, equilibriumDataset],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "phase-diagram · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          usePointStyle: true,
          filter: (item) => item.text !== "",
        },
      },
    },
    scales: {
      x: {
        min: -3.2,
        max: 3.2,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Position θ (rad)", color: t.ink, font: { size: 16 } },
      },
      y: {
        min: -3.2,
        max: 3.2,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Angular velocity dθ/dt (rad/s)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
