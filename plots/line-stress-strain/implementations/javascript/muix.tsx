// anyplot.ai
// line-stress-strain: Engineering Stress-Strain Curve
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-21

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Piecewise stress-strain models -----------------------------------------

const E_STEEL = 200000; // Young's modulus, mild steel (MPa)
const E_AL    = 69000;  // Young's modulus, Al 6061-T6 (MPa)

function steelCurve(eps) {
  const epsY = 250 / E_STEEL; // elastic limit ≈ 0.00125
  if (eps <= epsY)   return E_STEEL * eps;
  if (eps <= 0.010) {                           // Lüders yield plateau
    const f = (eps - epsY) / (0.010 - epsY);
    return 250 + 7 * Math.sin(f * Math.PI);
  }
  if (eps <= 0.200) {                           // strain hardening
    const f = (eps - 0.010) / 0.190;
    return 250 + 165 * Math.pow(f, 0.40);
  }
  if (eps <= 0.250) {                           // necking
    const f = (eps - 0.200) / 0.050;
    return 415 - 130 * Math.pow(f, 0.60);
  }
  return null;
}

function alCurve(eps) {
  if (eps > 0.120) return null;
  if (eps <= 0.003) return E_AL * eps;          // elastic (σ → ~207 MPa)
  if (eps <= 0.006) {                            // elastic-plastic transition
    const f = (eps - 0.003) / 0.003;
    return 207 + 69 * Math.sin(f * Math.PI / 2);
  }
  if (eps <= 0.085) {                            // strain hardening
    const f = (eps - 0.006) / 0.079;
    return 276 + 34 * Math.pow(f, 0.55);
  }
  const f = (eps - 0.085) / 0.035;              // necking to fracture
  return 310 - 90 * Math.pow(f, 0.65);
}

// 0.2% offset line for mild steel — elastic slope shifted 0.002 to the right
function offsetLine(eps) {
  if (eps < 0.002) return null;
  const s = E_STEEL * (eps - 0.002);
  return s <= 258 ? s : null; // stop just past the yield intersection
}

// --- Dataset: 240 uniform samples on ε ∈ [0, 0.250] ------------------------

const N = 240;
const dataset = Array.from({ length: N }, (_, i) => {
  const eps = (i / (N - 1)) * 0.250;
  return {
    strain:   eps,
    steel:    steelCurve(eps),
    aluminum: alCurve(eps),
    offset:   offsetLine(eps),
  };
});

// --- Title (scale font size for 71-char string vs 67-char baseline) ----------

const TITLE = "Steel vs Aluminum · line-stress-strain · javascript · muix · anyplot.ai";
const titleFontSize = Math.max(17, Math.round(22 * 67 / TITLE.length));

// --- Component ---------------------------------------------------------------

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const TITLE_H = 58;

  return (
    <Box
      sx={{
        width: W,
        height: H,
        display: "flex",
        flexDirection: "column",
        bgcolor: t.pageBg,
      }}
    >
      <Box sx={{ textAlign: "center", pt: 2, pb: 0.5 }}>
        <Typography sx={{ color: t.ink, fontWeight: 500, fontSize: titleFontSize }}>
          {TITLE}
        </Typography>
      </Box>

      <LineChart
        width={W}
        height={H - TITLE_H}
        skipAnimation
        dataset={dataset}
        xAxis={[{
          dataKey:        "strain",
          scaleType:      "linear",
          label:          "Engineering Strain ε (dimensionless)",
          min:            0,
          max:            0.262,
          tickNumber:     7,
          valueFormatter: (v) => v.toFixed(3),
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle:     { fontSize: 16, fill: t.ink, fontWeight: "500" },
        }]}
        yAxis={[{
          label:          "Engineering Stress (MPa)",
          min:            0,
          max:            460,
          tickNumber:     10,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle:     { fontSize: 16, fill: t.ink, fontWeight: "500" },
        }]}
        series={[
          {
            dataKey:      "steel",
            label:        "Mild Steel",
            showMark:     false,
            connectNulls: false,
            color:        t.palette[0],
          },
          {
            dataKey:      "aluminum",
            label:        "Al 6061-T6",
            showMark:     false,
            connectNulls: false,
            color:        t.palette[2],
          },
          {
            dataKey:      "offset",
            label:        "0.2% Offset Line",
            showMark:     false,
            connectNulls: false,
            color:        t.inkSoft,
          },
        ]}
        slotProps={{
          legend: {
            direction:      "column",
            position:       { vertical: "top", horizontal: "right" },
            itemMarkWidth:  20,
            itemMarkHeight: 4,
            padding:        { top: 20, right: 20 },
            labelStyle:     { fontSize: 14, fill: t.inkSoft },
          },
        }}
        margin={{ left: 90, right: 80, top: 30, bottom: 80 }}
      >
        <ChartsReferenceLine
          y={415}
          label="UTS = 415 MPa"
          labelAlign="end"
          lineStyle={{ strokeDasharray: "6 3", stroke: t.palette[0], strokeWidth: 1, opacity: 0.7 }}
          labelStyle={{ fill: t.palette[0], fontSize: 13 }}
        />
        <ChartsReferenceLine
          y={310}
          label="UTS = 310 MPa"
          labelAlign="end"
          lineStyle={{ strokeDasharray: "6 3", stroke: t.palette[2], strokeWidth: 1, opacity: 0.7 }}
          labelStyle={{ fill: t.palette[2], fontSize: 13 }}
        />
        <ChartsReferenceLine
          y={250}
          label="σʸ = 250 MPa"
          labelAlign="end"
          lineStyle={{ strokeDasharray: "4 4", stroke: t.palette[0], strokeWidth: 1, opacity: 0.5 }}
          labelStyle={{ fill: t.palette[0], fontSize: 12, opacity: 0.8 }}
        />
      </LineChart>
    </Box>
  );
}
