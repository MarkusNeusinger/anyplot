// anyplot.ai
// curve-oc: Operating Characteristic (OC) Curve
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-20
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const AQL = 0.02; // acceptable quality level of the contract, where the producer's risk is read
const LTPD = 0.1; // lot tolerance percent defective, where the consumer's risk is read

// Columns: set these to your data's column names
const FRACTION_DEFECTIVE = "Fraction defective"; // role: fraction_defective
const ACCEPTANCE = "Probability of acceptance"; // role: probability_acceptance
const PLAN = "Sampling plan"; // role: sample_plan

// Data: replace this block with your own records, one object per plan and fraction defective
// Three single-sample acceptance plans (sample size n, acceptance number c) over 0–15 % defective:
// P(accept) = P(X <= c) for X ~ Binomial(n, p), at 200 values of p
const data = (() => {
  const plans = [
    { n: 50, c: 1 },
    { n: 100, c: 2 },
    { n: 200, c: 4 },
  ];
  const steps = 200;
  const pMax = 0.15;
  return plans.flatMap(({ n, c }) =>
    Array.from({ length: steps }, (_, i) => {
      const p = (i * pMax) / (steps - 1);
      let accept = 0;
      let choose = 1;
      for (let k = 0; k <= c; k += 1) {
        accept += choose * p ** k * (1 - p) ** (n - k);
        choose = (choose * (n - k)) / (k + 1);
      }
      return { [FRACTION_DEFECTIVE]: p, [ACCEPTANCE]: Math.min(1, Math.max(0, accept)), [PLAN]: `n = ${n}, c = ${c}` };
    }),
  );
})();

// Plot: reads only data and the constants above
// One curve per plan in order of first appearance, on the shared sorted fraction-defective grid
const plans = [...new Set(data.map((d) => d[PLAN]))];
const fractions = [...new Set(data.map((d) => d[FRACTION_DEFECTIVE]))].sort((a, b) => a - b);
const acceptanceAt = new Map(data.map((d) => [`${d[PLAN]}|${d[FRACTION_DEFECTIVE]}`, d[ACCEPTANCE]]));
const curves = plans.map((plan, i) => {
  const rows = data.filter((d) => d[PLAN] === plan).sort((a, b) => a[FRACTION_DEFECTIVE] - b[FRACTION_DEFECTIVE]);
  // Acceptance probability at AQL and at LTPD, interpolated between the neighbouring computed points
  const [atAql, atLtpd] = [AQL, LTPD].map((q) => {
    const k = rows.findIndex((d) => d[FRACTION_DEFECTIVE] >= q);
    if (k < 1) return k === 0 ? rows[0][ACCEPTANCE] : null;
    const [a, b] = [rows[k - 1], rows[k]];
    return a[ACCEPTANCE] + ((q - a[FRACTION_DEFECTIVE]) / (b[FRACTION_DEFECTIVE] - a[FRACTION_DEFECTIVE])) * (b[ACCEPTANCE] - a[ACCEPTANCE]);
  });
  return { plan, color: t.palette[i], atAql, atLtpd };
});
// Risk marks go on the plan that leaves the consumer the largest risk at LTPD, the weakest protection
const covered = curves.filter((c) => c.atAql !== null && c.atLtpd !== null);
const riskPlan = covered.reduce<(typeof curves)[number] | null>((best, c) => (best === null || c.atLtpd! > best.atLtpd! ? c : best), null);
const xMax = fractions[fractions.length - 1];
const percent = (v: number) => `${parseFloat((v * 100).toFixed(1))} %`;

const TITLE = "Incoming Inspection · curve-oc · javascript · muix · anyplot.ai";
const subtitle = riskPlan
  ? `${plans.length} single-sample plans · producer's and consumer's risk read off ${riskPlan.plan}, the plan with the largest consumer's risk at LTPD`
  : `${plans.length} single-sample plans`;
const HEADER_H = 88;
const LEGEND_H = 44;

function RiskMarks() {
  const xScale = useXScale();
  const yScale = useYScale();
  if (!riskPlan) return null;
  const xa = xScale(AQL)!;
  const xl = xScale(LTPD)!;
  const ya = yScale(riskPlan.atAql!)!;
  const yl = yScale(riskPlan.atLtpd!)!;
  return (
    <g>
      {/* Producer's risk: the gap between certain acceptance and the curve at AQL */}
      <line x1={xa} y1={yScale(1)} x2={xa} y2={ya} stroke={riskPlan.color} strokeWidth={5} strokeLinecap="round" />
      {/* Consumer's risk: the curve's height at LTPD */}
      <line x1={xl} y1={yScale(0)} x2={xl} y2={yl} stroke={riskPlan.color} strokeWidth={5} strokeLinecap="round" />
      {[
        { x: xa, y: ya, text: `Producer's risk α = ${percent(1 - riskPlan.atAql!)}`, ty: (yScale(1)! + ya) / 2 },
        { x: xl, y: yl, text: `Consumer's risk β = ${percent(riskPlan.atLtpd!)}`, ty: yl - 28 },
      ].map((m) => (
        <g key={m.text}>
          <circle cx={m.x} cy={m.y} r={7} fill={riskPlan.color} stroke={t.pageBg} strokeWidth={2} />
          <text x={m.x + 14} y={m.ty} dominantBaseline="middle" fill={t.ink} fontSize={15} fontWeight={600}>
            {m.text}
          </text>
        </g>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{subtitle}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        margin={{ top: 16, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: fractions,
            scaleType: "linear",
            min: 0,
            max: xMax,
            label: FRACTION_DEFECTIVE,
            valueFormatter: (v: number) => percent(v),
            tickNumber: 8,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: 1,
            label: ACCEPTANCE,
            valueFormatter: (v: number) => percent(v),
            width: 80,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={curves.map((c, i) => ({
          id: `plan-${i}`,
          label: c.plan,
          color: c.color,
          data: fractions.map((x) => acceptanceAt.get(`${c.plan}|${x}`) ?? null),
          curve: "monotoneX" as const,
          showMark: false,
        }))}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink, gap: "28px" },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        {[
          { x: AQL, name: "AQL" },
          { x: LTPD, name: "LTPD" },
        ].map((r) => (
          <ChartsReferenceLine
            key={r.name}
            x={r.x}
            label={`${r.name} ${percent(r.x)}`}
            labelAlign="start"
            lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
            labelStyle={{ fill: t.inkSoft, fontSize: 15, fontWeight: 600 }}
          />
        ))}
        <RiskMarks />
      </LineChart>
    </Box>
  );
}
