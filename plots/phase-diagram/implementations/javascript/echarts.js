// anyplot.ai
// phase-diagram: Phase Diagram (State Space Plot)
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Linear damped oscillator: theta'' + 2*zeta*omega*theta' + omega^2*theta = 0.
// This linearized model captures the phase-plane structure common to many damped
// systems (spring-mass-damper, RLC circuit, weakly-driven pendulum). Three initial
// conditions all spiral into the same fixed point (theta=0, dtheta/dt=0), revealing
// the shared basin of attraction of the damped system.
const OMEGA = 2.2; // natural frequency (rad/s)
const ZETA = 0.12; // damping ratio (underdamped -> spiral, not overdamped decay)
const DT = 0.02;
const STEPS = 480;

function derivative(theta, omega_) {
  return [omega_, -2 * ZETA * OMEGA * omega_ - OMEGA * OMEGA * theta];
}

function integrate(theta0, omega0) {
  const points = [[theta0, omega0]];
  let theta = theta0;
  let omega_ = omega0;
  for (let i = 0; i < STEPS; i++) {
    const k1 = derivative(theta, omega_);
    const k2 = derivative(theta + (DT / 2) * k1[0], omega_ + (DT / 2) * k1[1]);
    const k3 = derivative(theta + (DT / 2) * k2[0], omega_ + (DT / 2) * k2[1]);
    const k4 = derivative(theta + DT * k3[0], omega_ + DT * k3[1]);
    theta += (DT / 6) * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]);
    omega_ += (DT / 6) * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]);
    points.push([theta, omega_]);
  }
  return points;
}

const trajectories = [
  { name: "θ₀ = 2.5 rad, ω₀ = 0", points: integrate(2.5, 0) },
  { name: "θ₀ = -1.5 rad, ω₀ = 2.0 rad/s", points: integrate(-1.5, 2.0) },
  { name: "θ₀ = 0.3 rad, ω₀ = -3.0 rad/s", points: integrate(0.3, -3.0) },
];

const allPoints = trajectories.flatMap((traj) => traj.points);
const thetaBound = Math.ceil(Math.max(...allPoints.map((p) => Math.abs(p[0]))) * 1.15 * 10) / 10;
const omegaBound = Math.ceil(Math.max(...allPoints.map((p) => Math.abs(p[1]))) * 1.15 * 10) / 10;

// Pick the quadrant corner farthest from every trajectory point, so the
// "Equilibrium" callout label never lands on top of the converging spirals.
const labelCandidates = [
  [0.62 * thetaBound, 0.62 * omegaBound],
  [-0.62 * thetaBound, 0.62 * omegaBound],
  [-0.62 * thetaBound, -0.62 * omegaBound],
  [0.62 * thetaBound, -0.62 * omegaBound],
];
const [labelX, labelY] = labelCandidates.reduce((best, candidate) => {
  const minDist = (pt) => Math.min(...allPoints.map((p) => Math.hypot(p[0] - pt[0], p[1] - pt[1])));
  return minDist(candidate) > minDist(best) ? candidate : best;
});

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "phase-diagram · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    bottom: 10,
    textStyle: { color: t.inkSoft, fontSize: 14 },
  },
  grid: { left: 90, right: 60, top: 90, bottom: 110, containLabel: true },
  xAxis: {
    type: "value",
    name: "Angular displacement θ (rad)",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: -thetaBound,
    max: thetaBound,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Angular velocity dθ/dt (rad/s)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: -omegaBound,
    max: omegaBound,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    ...trajectories.map((traj, i) => ({
      name: traj.name,
      type: "line",
      data: traj.points,
      showSymbol: false,
      smooth: false,
      lineStyle: { width: 3, color: t.palette[i] },
      markPoint: {
        symbol: "circle",
        symbolSize: 16,
        itemStyle: { color: t.palette[i], borderColor: t.pageBg, borderWidth: 2 },
        label: { show: false },
        data: [{ coord: traj.points[0], name: "start" }],
      },
      // nullclines theta=0 / dtheta/dt=0 -- attached once, to the first trajectory
      markLine:
        i === 0
          ? {
              symbol: "none",
              silent: true,
              lineStyle: { type: "dashed", width: 1.5, color: t.inkSoft, opacity: 0.4 },
              label: { show: false },
              data: [{ xAxis: 0 }, { yAxis: 0 }],
            }
          : undefined,
    })),
    {
      name: "Equilibrium (fixed point)",
      type: "scatter",
      data: [[0, 0]],
      symbol: "diamond",
      symbolSize: 18,
      itemStyle: { color: t.ink, borderColor: t.pageBg, borderWidth: 2 },
      label: { show: false },
      z: 10,
    },
    // Leader line from the true fixed point to the callout label, placed in
    // whichever corner sits farthest from the converging trajectories.
    {
      type: "line",
      data: [
        [0, 0],
        [labelX, labelY],
      ],
      showSymbol: false,
      silent: true,
      lineStyle: { type: "dashed", width: 1.5, color: t.inkSoft, opacity: 0.6 },
      z: 9,
    },
    {
      type: "scatter",
      data: [[labelX, labelY]],
      symbol: "circle",
      symbolSize: 6,
      itemStyle: { color: t.ink },
      label: {
        show: true,
        formatter: "Equilibrium\n(θ=0, dθ/dt=0)",
        position: [labelX >= 0 ? 10 : -10, labelY >= 0 ? -10 : 10],
        align: labelX >= 0 ? "left" : "right",
        verticalAlign: labelY >= 0 ? "bottom" : "top",
        color: t.ink,
        fontSize: 14,
      },
      z: 10,
    },
  ],
});
