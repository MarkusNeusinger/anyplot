import Box from '@mui/material/Box';

import matrixData from 'src/data/paletteMatrices.json';
import { typography } from 'src/theme';

const MATRIX_LABELS: string[] = matrixData.labels;
const MATRIX_HEXES: string[] = matrixData.hexes;
const [DE_T_BAD, DE_T_WARN, DE_T_OK] = matrixData.thresholds;

function deltaECellBg(v: number): string {
  if (v <= 0) return 'transparent'; // diagonal
  if (v < DE_T_BAD) return 'rgba(174, 48, 48, 0.26)'; // <5 indistinguishable
  if (v < DE_T_WARN) return 'rgba(189, 130, 51, 0.22)'; // <10 weak
  if (v < DE_T_OK) return 'rgba(221, 204, 119, 0.18)'; // <15 acceptable
  return 'transparent'; // >=15 comfortable
}

export function DeltaEMatrix({
  title,
  matrix,
  breakdown,
}: {
  title: string;
  matrix: number[][];
  breakdown?: { label: string; m: number[][] }[];
}) {
  const dot = (hx: string, label: string) => (
    <Box
      sx={{
        width: 16,
        height: 16,
        borderRadius: '50%',
        bgcolor: hx,
        mx: 'auto',
        boxShadow: '0 0 0 1px var(--rule)',
      }}
      title={label}
    />
  );
  return (
    <Box sx={{ minWidth: 0 }}>
      <Box
        sx={{
          fontFamily: typography.mono,
          fontSize: '11px',
          color: 'var(--ink)',
          fontWeight: 600,
          mb: 1,
        }}
      >
        {title}
      </Box>
      <Box sx={{ overflowX: 'auto' }}>
        <Box
          component="table"
          sx={{
            width: '100%',
            tableLayout: 'fixed',
            borderCollapse: 'collapse',
            fontFamily: typography.mono,
            fontSize: '13px',
          }}
        >
          <Box component="thead">
            <Box component="tr">
              <Box component="th" sx={{ width: 24 }} />
              {MATRIX_HEXES.map((hx, j) => (
                <Box component="th" key={j} sx={{ p: '2px' }}>
                  {dot(hx, MATRIX_LABELS[j])}
                </Box>
              ))}
            </Box>
          </Box>
          <Box component="tbody">
            {matrix.map((row, i) => (
              <Box component="tr" key={i}>
                <Box component="th" sx={{ p: '2px' }}>
                  {dot(MATRIX_HEXES[i], MATRIX_LABELS[i])}
                </Box>
                {row.map((v, j) => {
                  const tip =
                    i === j
                      ? MATRIX_LABELS[i]
                      : breakdown
                        ? `${MATRIX_LABELS[i]} ↔ ${MATRIX_LABELS[j]} — ${breakdown.map(b => `${b.label} ${b.m[i][j].toFixed(1)}`).join(' · ')}`
                        : `${MATRIX_LABELS[i]} ↔ ${MATRIX_LABELS[j]} — ΔE ${v.toFixed(1)}`;
                  return (
                    <Box
                      component="td"
                      key={j}
                      title={tip}
                      sx={{
                        height: 30,
                        textAlign: 'center',
                        border: '1px solid var(--rule)',
                        bgcolor: deltaECellBg(v),
                        color:
                          i === j
                            ? 'var(--rule)'
                            : v < DE_T_WARN
                              ? 'var(--ink)'
                              : 'var(--ink-muted)',
                        fontWeight: v > 0 && v < DE_T_BAD ? 700 : 400,
                        cursor: 'help',
                      }}
                    >
                      {i === j ? '·' : v.toFixed(0)}
                    </Box>
                  );
                })}
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
