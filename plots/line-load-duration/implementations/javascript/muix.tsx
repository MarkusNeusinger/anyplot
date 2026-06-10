// anyplot.ai
// line-load-duration: Load Duration Curve for Energy Systems
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-10
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// --- Data (deterministic, no RNG) -------------------------------------------
// 8,760 hours sorted descending: peak ≈ 1200 MW → base ≈ 400 MW
const N_HOURS = 8760;
const hours = Array.from({ length: N_HOURS }, (_, i) => i);

// Power-law decay gives realistic LDC shape (steep peak drop, flat base tail)
const loadMW = hours.map(h => 400 + 800 * Math.pow(1 - h / (N_HOURS - 1), 0.65));

// Decompose into three stacked bands
const baseData  = hours.map(() => 400);                                       // base: constant 400 MW floor
const interData = hours.map(h => Math.min(Math.max(loadMW[h] - 400, 0), 400)); // 400–800 MW band
const peakData  = hours.map(h => Math.max(loadMW[h] - 800, 0));               // >800 MW peak only

// Total annual energy consumption (MWh → TWh)
const totalEnergyTWh = (loadMW.reduce((s, v) => s + v, 0) / 1e6).toFixed(2);

// Title: 48 chars < 67 baseline — default 22 px, no scaling needed
const TITLE = "line-load-duration · javascript · muix · anyplot.ai";

// --- Component (default-exported; harness mounts it with no props) -----------
export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  // Fixed-height header (title) and footer (energy annotation); chart fills the rest
  const HEADER_H = 50;
  const FOOTER_H = 28;
  const PAD_TOP  = 20;
  const PAD_BOT  = 12;
  const PAD_H    = 48; // left + right padding on wrapper
  const chartW   = W - PAD_H;
  const chartH   = H - PAD_TOP - HEADER_H - FOOTER_H - PAD_BOT;

  return (
    <div style={{
      width: W,
      height: H,
      backgroundColor: t.pageBg,
      display: "flex",
      flexDirection: "column",
      padding: `${PAD_TOP}px 24px ${PAD_BOT}px`,
      boxSizing: "border-box",
      fontFamily: "sans-serif",
    }}>
      {/* Chart title */}
      <div style={{
        color: t.ink,
        fontSize: 22,
        fontWeight: 600,
        lineHeight: "30px",
        marginBottom: 8,
        flexShrink: 0,
      }}>
        {TITLE}
      </div>

      {/* Stacked-area line chart — three bands sum to the load duration curve */}
      <LineChart
        width={chartW}
        height={chartH}
        skipAnimation
        colors={[t.palette[0], t.palette[1], t.palette[2]]}
        xAxis={[{
          data: hours,
          label: "Hours in a Year (sorted by descending load)",
          min: 0,
          max: N_HOURS - 1,
          tickInterval: [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000],
        }]}
        yAxis={[{
          label: "Power Demand (MW)",
          min: 0,
          max: 1280,
        }]}
        series={[
          {
            data: baseData,
            area: true,
            stack: "load",
            label: "Base Load (< 400 MW)",
            showMark: false,
            curve: "linear",
          },
          {
            data: interData,
            area: true,
            stack: "load",
            label: "Intermediate Load (400–800 MW)",
            showMark: false,
            curve: "linear",
          },
          {
            data: peakData,
            area: true,
            stack: "load",
            label: "Peak Load (> 800 MW)",
            showMark: false,
            curve: "linear",
          },
        ]}
        sx={{
          "& .MuiLineElement-root": { strokeWidth: 0 },
          "& .MuiAreaElement-root": { fillOpacity: 0.85 },
        }}
        slotProps={{
          legend: {
            position: { vertical: "top", horizontal: "right" },
          },
        }}
      >
        {/* Horizontal dashed lines at capacity tier boundaries */}
        <ChartsReferenceLine
          y={400}
          label="Base capacity: 400 MW"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "8 4", strokeWidth: 1.5 }}
          labelStyle={{ fontSize: 12, fill: t.inkSoft }}
          labelAlign="end"
        />
        <ChartsReferenceLine
          y={800}
          label="Intermediate capacity: 800 MW"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "8 4", strokeWidth: 1.5 }}
          labelStyle={{ fontSize: 12, fill: t.inkSoft }}
          labelAlign="end"
        />
      </LineChart>

      {/* Total energy annotation */}
      <div style={{
        color: t.inkSoft,
        fontSize: 14,
        textAlign: "center",
        marginTop: 4,
        flexShrink: 0,
        fontFamily: "sans-serif",
      }}>
        Total annual energy consumption: {totalEnergyTWh} TWh
      </div>
    </div>
  );
}
