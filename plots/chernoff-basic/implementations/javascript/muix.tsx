// anyplot.ai
// chernoff-basic: Chernoff Faces for Multivariate Data
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-02
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const HEADER_H = 122;
const FOOTER_H = 64;
const FACE_RX = 58;
const FACE_RY = 72;
const EYE_R = 9;
const EYE_DX = 22;
const BROW_LEN = 26;
const NOSE_LEN = 22;
const MOUTH_HALF_W = 26;
const MOUTH_CURVE_MAX = 25;

// Columns: set these to your data's column names
const OBSERVATION = "Company"; // role: label
const GROUP = "Sector"; // role: group
const VAR_FACE_W = "Revenue growth (%)"; // role: variable_1
const VAR_FACE_H = "Profit margin (%)"; // role: variable_2
const VAR_EYE_R = "Liquidity ratio"; // role: variable_3
const VAR_EYE_DX = "Market share (%)"; // role: variable_4
const VAR_BROW = "Debt-to-equity"; // role: variable_5
const VAR_NOSE = "Innovation score"; // role: variable_6
const VAR_MOUTH = "Employee retention (%)"; // role: variable_7

// Data: replace this block with your own records, one object per row
const data = [
  {
    [OBSERVATION]: "Nova Systems",
    [GROUP]: "Technology",
    [VAR_FACE_W]: 28.4,
    [VAR_FACE_H]: 24.1,
    [VAR_EYE_R]: 2.15,
    [VAR_EYE_DX]: 14.2,
    [VAR_BROW]: 0.32,
    [VAR_NOSE]: 91,
    [VAR_MOUTH]: 93,
  },
  {
    [OBSERVATION]: "Quantum Byte",
    [GROUP]: "Technology",
    [VAR_FACE_W]: 31.8,
    [VAR_FACE_H]: 21.6,
    [VAR_EYE_R]: 1.92,
    [VAR_EYE_DX]: 11.8,
    [VAR_BROW]: 0.24,
    [VAR_NOSE]: 95,
    [VAR_MOUTH]: 89,
  },
  {
    [OBSERVATION]: "CloudPeak",
    [GROUP]: "Technology",
    [VAR_FACE_W]: 24.9,
    [VAR_FACE_H]: 26.8,
    [VAR_EYE_R]: 2.38,
    [VAR_EYE_DX]: 18.5,
    [VAR_BROW]: 0.41,
    [VAR_NOSE]: 84,
    [VAR_MOUTH]: 91,
  },
  {
    [OBSERVATION]: "Vertex Labs",
    [GROUP]: "Technology",
    [VAR_FACE_W]: 29.6,
    [VAR_FACE_H]: 19.4,
    [VAR_EYE_R]: 1.78,
    [VAR_EYE_DX]: 9.6,
    [VAR_BROW]: 0.28,
    [VAR_NOSE]: 88,
    [VAR_MOUTH]: 87,
  },
  {
    [OBSERVATION]: "Harborline Retail",
    [GROUP]: "Retail",
    [VAR_FACE_W]: 14.2,
    [VAR_FACE_H]: 11.5,
    [VAR_EYE_R]: 2.45,
    [VAR_EYE_DX]: 24.6,
    [VAR_BROW]: 0.88,
    [VAR_NOSE]: 46,
    [VAR_MOUTH]: 76,
  },
  {
    [OBSERVATION]: "Meadow Mart",
    [GROUP]: "Retail",
    [VAR_FACE_W]: 11.8,
    [VAR_FACE_H]: 9.8,
    [VAR_EYE_R]: 2.62,
    [VAR_EYE_DX]: 21.4,
    [VAR_BROW]: 0.74,
    [VAR_NOSE]: 39,
    [VAR_MOUTH]: 79,
  },
  {
    [OBSERVATION]: "Urban Goods",
    [GROUP]: "Retail",
    [VAR_FACE_W]: 16.5,
    [VAR_FACE_H]: 13.2,
    [VAR_EYE_R]: 2.18,
    [VAR_EYE_DX]: 19.2,
    [VAR_BROW]: 0.96,
    [VAR_NOSE]: 54,
    [VAR_MOUTH]: 73,
  },
  {
    [OBSERVATION]: "Riverside Shops",
    [GROUP]: "Retail",
    [VAR_FACE_W]: 12.9,
    [VAR_FACE_H]: 10.4,
    [VAR_EYE_R]: 2.51,
    [VAR_EYE_DX]: 26.1,
    [VAR_BROW]: 0.82,
    [VAR_NOSE]: 42,
    [VAR_MOUTH]: 77,
  },
  {
    [OBSERVATION]: "IronWorks Mfg",
    [GROUP]: "Manufacturing",
    [VAR_FACE_W]: 7.4,
    [VAR_FACE_H]: 15.6,
    [VAR_EYE_R]: 1.42,
    [VAR_EYE_DX]: 17.8,
    [VAR_BROW]: 1.54,
    [VAR_NOSE]: 64,
    [VAR_MOUTH]: 66,
  },
  {
    [OBSERVATION]: "Steelframe Co",
    [GROUP]: "Manufacturing",
    [VAR_FACE_W]: 9.1,
    [VAR_FACE_H]: 14.2,
    [VAR_EYE_R]: 1.55,
    [VAR_EYE_DX]: 20.3,
    [VAR_BROW]: 1.38,
    [VAR_NOSE]: 59,
    [VAR_MOUTH]: 69,
  },
  {
    [OBSERVATION]: "Forge Dynamics",
    [GROUP]: "Manufacturing",
    [VAR_FACE_W]: 6.2,
    [VAR_FACE_H]: 16.9,
    [VAR_EYE_R]: 1.34,
    [VAR_EYE_DX]: 15.4,
    [VAR_BROW]: 1.68,
    [VAR_NOSE]: 71,
    [VAR_MOUTH]: 63,
  },
  {
    [OBSERVATION]: "Anvil Industries",
    [GROUP]: "Manufacturing",
    [VAR_FACE_W]: 8.3,
    [VAR_FACE_H]: 13.5,
    [VAR_EYE_R]: 1.48,
    [VAR_EYE_DX]: 22.0,
    [VAR_BROW]: 1.46,
    [VAR_NOSE]: 61,
    [VAR_MOUTH]: 67,
  },
];

// Plot: reads only data and the constants above
const groups = Array.from(new Set(data.map((d) => String(d[GROUP]))));
const metricCols = [
  VAR_FACE_W,
  VAR_FACE_H,
  VAR_EYE_R,
  VAR_EYE_DX,
  VAR_BROW,
  VAR_NOSE,
  VAR_MOUTH,
];

const metricExtents = Object.fromEntries(
  metricCols.map((col) => {
    const vals = data.map((d) => Number(d[col]));
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    return [col, { min, span: max - min || 1 }];
  }),
);

const maxPerGroup = Math.max(
  ...groups.map((g) => data.filter((d) => String(d[GROUP]) === g).length),
);
const numCols = Math.max(1, maxPerGroup);
const numRows = Math.max(1, groups.length);

const groupCounts = new Map<string, number>();
const faces = data.map((d) => {
  const groupName = String(d[GROUP]);
  const rowIdx = groups.indexOf(groupName);
  const colIdx = groupCounts.get(groupName) ?? 0;
  groupCounts.set(groupName, colIdx + 1);

  const norm = Object.fromEntries(
    metricCols.map((col) => {
      const ext = metricExtents[col];
      const v = (Number(d[col]) - ext.min) / ext.span;
      return [col, Math.min(1, Math.max(0, v))];
    }),
  );

  return {
    name: String(d[OBSERVATION]),
    group: groupName,
    row: rowIdx,
    col: colIdx,
    color: t.palette[rowIdx],
    norm,
  };
});

const TITLE = "chernoff-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${faces.length} ${OBSERVATION.toLowerCase()} profiles across ${groups.length} ${GROUP.toLowerCase()}s · ${metricCols.length} normalized variables [0, 1] mapped to facial features`;

const featureKeyLine1 = `Face width → ${VAR_FACE_W} · Face height → ${VAR_FACE_H} · Eye size → ${VAR_EYE_R} · Eye spacing → ${VAR_EYE_DX}`;
const featureKeyLine2 = `Eyebrow slant → ${VAR_BROW} · Nose length → ${VAR_NOSE} · Mouth smile → ${VAR_MOUTH}`;

function FaceGridLayer() {
  const xs = useXScale("col");
  const ys = useYScale("row");
  if (!xs || !ys) return null;

  return (
    <g>
      {faces.map((face) => {
        const cx = xs(face.col + 0.5);
        const cy = ys(face.row + 0.45);
        if (cx === undefined || cy === undefined) return null;

        const m = face.norm;
        const rx = FACE_RX * (0.72 + 0.54 * m[VAR_FACE_W]);
        const ry = FACE_RY * (0.74 + 0.48 * m[VAR_FACE_H]);
        const eyeR = EYE_R * (0.62 + 0.78 * m[VAR_EYE_R]);
        const eyeDx = EYE_DX * (0.72 + 0.58 * m[VAR_EYE_DX]);
        const browAngle = -10 + 38 * m[VAR_BROW];
        const noseLen = NOSE_LEN * (0.62 + 0.78 * m[VAR_NOSE]);
        const mouthCurve = (m[VAR_MOUTH] - 0.5) * 2 * MOUTH_CURVE_MAX;

        const eyeY = cy - ry * 0.14;
        const browY = eyeY - eyeR - 8;
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
              x1={cx - eyeDx - BROW_LEN / 2}
              y1={browY}
              x2={cx - eyeDx + BROW_LEN / 2}
              y2={browY}
              stroke={t.ink}
              strokeWidth={3}
              strokeLinecap="round"
              transform={`rotate(${browAngle} ${cx - eyeDx} ${browY})`}
            />
            <line
              x1={cx + eyeDx - BROW_LEN / 2}
              y1={browY}
              x2={cx + eyeDx + BROW_LEN / 2}
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
              d={`M ${cx - MOUTH_HALF_W} ${mouthY} Q ${cx} ${mouthY + mouthCurve} ${cx + MOUTH_HALF_W} ${mouthY}`}
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
                  height: 14,
                  borderRadius: 3,
                  background: t.palette[i],
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
