// anyplot.ai
// phase-diagram: Phase Diagram (State Space Plot)
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data: damped pendulum phase portrait -----------------------------------
// d(theta)/dt = omega
// d(omega)/dt = -2*zeta*omega0*omega - omega0^2*sin(theta)
// RK4 integration, fixed dt, fully deterministic.
const omega0 = 1.5;
const zeta = 0.15;
const dt = 0.02;
const steps = 550;

function derivatives(theta, omega) {
  return [omega, -2 * zeta * omega0 * omega - omega0 * omega0 * Math.sin(theta)];
}

function integrate(theta0, omega0State) {
  let theta = theta0;
  let omega = omega0State;
  const points = [{ x: theta, y: omega }];
  for (let i = 0; i < steps; i++) {
    const [k1t, k1o] = derivatives(theta, omega);
    const [k2t, k2o] = derivatives(theta + (dt / 2) * k1t, omega + (dt / 2) * k1o);
    const [k3t, k3o] = derivatives(theta + (dt / 2) * k2t, omega + (dt / 2) * k2o);
    const [k4t, k4o] = derivatives(theta + dt * k3t, omega + dt * k3o);
    theta += (dt / 6) * (k1t + 2 * k2t + 2 * k3t + k4t);
    omega += (dt / 6) * (k1o + 2 * k2o + 2 * k3o + k4o);
    points.push({ x: theta, y: omega });
  }
  return points;
}

const initialConditions = [
  { theta0: 2.6, omega0State: 0.0, label: "θ₀ = 2.6 rad, ω₀ = 0" },
  { theta0: -2.0, omega0State: 1.2, label: "θ₀ = -2.0 rad, ω₀ = 1.2" },
  { theta0: 0.8, omega0State: -1.8, label: "θ₀ = 0.8 rad, ω₀ = -1.8" },
];

const trajectories = initialConditions.map((ic, i) => ({
  color: t.palette[i],
  label: ic.label,
  points: integrate(ic.theta0, ic.omega0State),
}));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Datasets ------------------------------------------------------------
const trajectoryDatasets = trajectories.map((traj) => ({
  label: traj.label,
  data: traj.points,
  showLine: true,
  borderColor: traj.color,
  borderWidth: 3,
  pointRadius: 0,
  tension: 0,
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
