// anyplot.ai
// chernoff-basic: Chernoff Faces for Multivariate Data
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 87/100 | Updated: 2026-10-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const HEADER_H = 122;
const FOOTER_H = 64;
const FACE_H_SHARE = 0.315; // base face half-height as a share of the cell height
const FACE_W_SHARE = 0.4; // cap on the base face half-height as a share of the cell width
// Facial features as shares of the base face half-height
const FACE_RX_SHARE = 0.806;
const EYE_R_SHARE = 0.125;
const EYE_DX_SHARE = 0.306;
const BROW_LEN_SHARE = 0.361;
const BROW_GAP_SHARE = 0.111;
const NOSE_LEN_SHARE = 0.306;
const MOUTH_HALF_W_SHARE = 0.361;
const MOUTH_CURVE_SHARE = 0.347;
// Features in mapping order; variable i drives feature i
const FEATURES = [
  "Face width",
  "Face height",
  "Eye size",
  "Eye spacing",
  "Eyebrow slant",
  "Nose length",
  "Mouth smile",
];
const NEUTRAL = 0.5; // value of a feature that no variable drives

// Columns: set these to your data's column names
const OBSERVATION = "Company"; // role: observation_id
const GROUP = "Sector"; // role: extra
const VARIABLES = [
  "Revenue growth (%)",
  "Profit margin (%)",
  "Liquidity ratio",
  "Market share (%)",
  "Debt-to-equity",
  "Innovation score",
  "Employee retention (%)",
]; // role: variable

// Data: replace this block with your own records, one object per row
const data = [
  {
    [OBSERVATION]: "Nova Systems",
    [GROUP]: "Technology",
    [VARIABLES[0]]: 28.4,
    [VARIABLES[1]]: 24.1,
    [VARIABLES[2]]: 2.15,
    [VARIABLES[3]]: 14.2,
    [VARIABLES[4]]: 0.32,
    [VARIABLES[5]]: 91,
    [VARIABLES[6]]: 93,
  },
  {
    [OBSERVATION]: "Quantum Byte",
    [GROUP]: "Technology",
    [VARIABLES[0]]: 31.8,
    [VARIABLES[1]]: 21.6,
    [VARIABLES[2]]: 1.92,
    [VARIABLES[3]]: 11.8,
    [VARIABLES[4]]: 0.24,
    [VARIABLES[5]]: 95,
    [VARIABLES[6]]: 89,
  },
  {
    [OBSERVATION]: "CloudPeak",
    [GROUP]: "Technology",
    [VARIABLES[0]]: 24.9,
    [VARIABLES[1]]: 26.8,
    [VARIABLES[2]]: 2.38,
    [VARIABLES[3]]: 18.5,
    [VARIABLES[4]]: 0.41,
    [VARIABLES[5]]: 84,
    [VARIABLES[6]]: 91,
  },
  {
    [OBSERVATION]: "Vertex Labs",
    [GROUP]: "Technology",
    [VARIABLES[0]]: 29.6,
    [VARIABLES[1]]: 19.4,
    [VARIABLES[2]]: 1.78,
    [VARIABLES[3]]: 9.6,
    [VARIABLES[4]]: 0.28,
    [VARIABLES[5]]: 88,
    [VARIABLES[6]]: 87,
  },
  {
    [OBSERVATION]: "Harborline Retail",
    [GROUP]: "Retail",
    [VARIABLES[0]]: 14.2,
    [VARIABLES[1]]: 11.5,
    [VARIABLES[2]]: 2.45,
    [VARIABLES[3]]: 24.6,
    [VARIABLES[4]]: 0.88,
    [VARIABLES[5]]: 46,
    [VARIABLES[6]]: 76,
  },
  {
    [OBSERVATION]: "Meadow Mart",
    [GROUP]: "Retail",
    [VARIABLES[0]]: 11.8,
    [VARIABLES[1]]: 9.8,
    [VARIABLES[2]]: 2.62,
    [VARIABLES[3]]: 21.4,
    [VARIABLES[4]]: 0.74,
    [VARIABLES[5]]: 39,
    [VARIABLES[6]]: 79,
  },
  {
    [OBSERVATION]: "Urban Goods",
    [GROUP]: "Retail",
    [VARIABLES[0]]: 16.5,
    [VARIABLES[1]]: 13.2,
    [VARIABLES[2]]: 2.18,
    [VARIABLES[3]]: 19.2,
    [VARIABLES[4]]: 0.96,
    [VARIABLES[5]]: 54,
    [VARIABLES[6]]: 73,
  },
  {
    [OBSERVATION]: "Riverside Shops",
    [GROUP]: "Retail",
    [VARIABLES[0]]: 12.9,
    [VARIABLES[1]]: 10.4,
    [VARIABLES[2]]: 2.51,
    [VARIABLES[3]]: 26.1,
    [VARIABLES[4]]: 0.82,
    [VARIABLES[5]]: 42,
    [VARIABLES[6]]: 77,
  },
  {
    [OBSERVATION]: "IronWorks Mfg",
    [GROUP]: "Manufacturing",
    [VARIABLES[0]]: 7.4,
    [VARIABLES[1]]: 15.6,
    [VARIABLES[2]]: 1.42,
    [VARIABLES[3]]: 17.8,
    [VARIABLES[4]]: 1.54,
    [VARIABLES[5]]: 64,
    [VARIABLES[6]]: 66,
  },
  {
    [OBSERVATION]: "Steelframe Co",
    [GROUP]: "Manufacturing",
    [VARIABLES[0]]: 9.1,
    [VARIABLES[1]]: 14.2,
    [VARIABLES[2]]: 1.55,
    [VARIABLES[3]]: 20.3,
    [VARIABLES[4]]: 1.38,
    [VARIABLES[5]]: 59,
    [VARIABLES[6]]: 69,
  },
  {
    [OBSERVATION]: "Forge Dynamics",
    [GROUP]: "Manufacturing",
    [VARIABLES[0]]: 6.2,
    [VARIABLES[1]]: 16.9,
    [VARIABLES[2]]: 1.34,
    [VARIABLES[3]]: 15.4,
    [VARIABLES[4]]: 1.68,
    [VARIABLES[5]]: 71,
    [VARIABLES[6]]: 63,
  },
  {
    [OBSERVATION]: "Anvil Industries",
    [GROUP]: "Manufacturing",
    [VARIABLES[0]]: 8.3,
    [VARIABLES[1]]: 13.5,
    [VARIABLES[2]]: 1.48,
    [VARIABLES[3]]: 22.0,
    [VARIABLES[4]]: 1.46,
    [VARIABLES[5]]: 61,
    [VARIABLES[6]]: 67,
  },
];

// Plot: reads only data and the constants above
const groups = Array.from(new Set(data.map((d) => String(d[GROUP]))));
const mappedVariables = VARIABLES.slice(0, FEATURES.length);

const extents = mappedVariables.map((col) => {
  const vals = data.map((d) => Number(d[col]));
  const min = Math.min(...vals);
  return { min, span: Math.max(...vals) - min || 1 };
});

const numCols = Math.max(
  ...groups.map((g) => data.filter((d) => String(d[GROUP]) === g).length),
);
const numRows = groups.length;

const groupCounts = new Map<string, number>();
const faces = data.map((d) => {
  const groupName = String(d[GROUP]);
  const rowIdx = groups.indexOf(groupName);
  const colIdx = groupCounts.get(groupName) ?? 0;
  groupCounts.set(groupName, colIdx + 1);

  return {
    name: String(d[OBSERVATION]),
    row: rowIdx,
    col: colIdx,
    color: t.palette[rowIdx],
    // One value in [0, 1] per feature: min-max normalised, or neutral when unmapped
    f: FEATURES.map((_, i) =>
      i < mappedVariables.length
        ? (Number(d[mappedVariables[i]]) - extents[i].min) / extents[i].span
        : NEUTRAL,
    ),
  };
});

const featureKey = mappedVariables.map((v, i) => `${FEATURES[i]} → ${v}`);
const keySplit = Math.ceil(featureKey.length / 2);
const featureKeyLine1 = featureKey.slice(0, keySplit).join(" · ");
const featureKeyLine2 = featureKey.slice(keySplit).join(" · ");

const TITLE = "chernoff-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${faces.length} faces (${OBSERVATION}) · ${groups.length} groups (${GROUP}) · ${mappedVariables.length} variables normalized to [0, 1] and mapped to facial features`;

function FaceGridLayer() {
  const xs = useXScale("col");
  const ys = useYScale("row");
  const { width: areaW, height: areaH } = useDrawingArea();
  const unit = Math.min(
    (areaH / numRows) * FACE_H_SHARE,
    (areaW / numCols) * FACE_W_SHARE,
  );

  return (
    <g>
      {faces.map((face) => {
        const cx = xs(face.col + 0.5);
        const cy = ys(face.row + 0.45);
        const f = face.f;
        const rx = unit * FACE_RX_SHARE * (0.72 + 0.54 * f[0]);
        const ry = unit * (0.74 + 0.48 * f[1]);
        const eyeR = unit * EYE_R_SHARE * (0.62 + 0.78 * f[2]);
        const eyeDx = unit * EYE_DX_SHARE * (0.72 + 0.58 * f[3]);
        const browAngle = -10 + 38 * f[4];
        const noseLen = unit * NOSE_LEN_SHARE * (0.62 + 0.78 * f[5]);
        const mouthCurve = (f[6] - 0.5) * 2 * unit * MOUTH_CURVE_SHARE;
        const browLen = unit * BROW_LEN_SHARE;
        const mouthHalfW = unit * MOUTH_HALF_W_SHARE;

        const eyeY = cy - ry * 0.14;
        const browY = eyeY - eyeR - unit * BROW_GAP_SHARE;
        const noseY0 = cy + ry * 0.04;
        const noseY1 = noseY0 + noseLen;
        const mouthY = cy + ry * 0.48;

        return (
          <g key={face.name}>
            <ellipse
              cx={cx}
              cy={cy}
              rx={rx}
              ry={ry}
              fill={t.elevatedBg}
              stroke={face.color}
              strokeWidth={3.5}
            />
            <circle cx={cx - eyeDx} cy={eyeY} r={eyeR} fill={t.ink} />
            <circle cx={cx + eyeDx} cy={eyeY} r={eyeR} fill={t.ink} />
            <line
              x1={cx - eyeDx - browLen / 2}
              y1={browY}
              x2={cx - eyeDx + browLen / 2}
              y2={browY}
              stroke={t.ink}
              strokeWidth={3}
              strokeLinecap="round"
              transform={`rotate(${browAngle} ${cx - eyeDx} ${browY})`}
            />
            <line
              x1={cx + eyeDx - browLen / 2}
              y1={browY}
              x2={cx + eyeDx + browLen / 2}
              y2={browY}
              stroke={t.ink}
              strokeWidth={3}
              strokeLinecap="round"
              transform={`rotate(${-browAngle} ${cx + eyeDx} ${browY})`}
            />
            <path
              d={`M ${cx} ${noseY0} L ${cx} ${noseY1} L ${cx + 5} ${noseY1 + 3}`}
              fill="none"
              stroke={t.inkSoft}
              strokeWidth={2.5}
              strokeLinecap="round"
            />
            <path
              d={`M ${cx - mouthHalfW} ${mouthY} Q ${cx} ${mouthY + mouthCurve} ${cx + mouthHalfW} ${mouthY}`}
              fill="none"
              stroke={t.ink}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <text
              x={cx}
              y={cy + ry + 24}
              textAnchor="middle"
              fontSize={14}
              fontWeight={600}
              fill={t.ink}
            >
              {face.name}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - HEADER_H - FOOTER_H;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          paddingTop: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
        <div
          style={{
            display: "flex",
            gap: 28,
            alignItems: "center",
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          {groups.map((g, i) => (
            <div
              key={g}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <span
                style={{
                  width: 14,
                  height: 16,
                  borderRadius: "50%",
                  border: `3px solid ${t.palette[i]}`,
                  background: t.elevatedBg,
                  display: "inline-block",
                }}
              />
              <span style={{ color: t.ink, fontWeight: 500 }}>{g}</span>
            </div>
          ))}
        </div>
      </div>

      <ChartsContainer
        width={width}
        height={chartHeight}
        series={[]}
        margin={{ top: 10, right: 48, bottom: 18, left: 48 }}
        xAxis={[
          {
            id: "col",
            scaleType: "linear",
            min: 0,
            max: numCols,
            height: 0,
          },
        ]}
        yAxis={[
          {
            id: "row",
            scaleType: "linear",
            min: 0,
            max: numRows,
            reverse: true,
            width: 0,
          },
        ]}
        skipAnimation
      >
        <FaceGridLayer />
      </ChartsContainer>

      <div
        style={{
          height: FOOTER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
          fontSize: 14,
          color: t.inkSoft,
        }}
      >
        <div>{featureKeyLine1}</div>
        <div>{featureKeyLine2}</div>
      </div>
    </div>
  );
}
