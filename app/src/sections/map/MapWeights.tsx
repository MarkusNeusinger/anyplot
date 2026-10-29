import type React from 'react';

import Box from '@mui/material/Box';
import Slider from '@mui/material/Slider';

import { MIN_SIM_BOUNDS } from 'src/hooks/useForceGraphSimulation';
import { TAG_CATEGORIES } from 'src/sections/map/MapPage.helpers';
import { colors, fontSize, typography } from 'src/theme';

export function MapWeights({
  weightsOpen,
  setWeightsOpen,
  weights,
  setWeights,
  minSim,
  setMinSim,
  resetWeights,
}: {
  weightsOpen: boolean;
  setWeightsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  weights: Record<string, number>;
  setWeights: React.Dispatch<React.SetStateAction<Record<string, number>>>;
  minSim: number;
  setMinSim: (val: number) => void;
  resetWeights: () => void;
}) {
  return (
    <Box
      sx={{
        position: 'absolute',
        bottom: { xs: 8, sm: 16 },
        left: { xs: 16, sm: 32, md: 64, lg: 96 },
        zIndex: 2,
        display: 'flex',
        flexDirection: 'column-reverse',
        alignItems: 'flex-start',
        gap: 1,
        fontFamily: typography.mono,
        fontSize: fontSize.xs,
        color: 'var(--ink-soft)',
      }}
    >
      <Box
        component="button"
        onClick={() => setWeightsOpen(o => !o)}
        sx={{
          all: 'unset',
          cursor: 'pointer',
          padding: { xs: '6px 4px', sm: '0' },
          fontFamily: typography.mono,
          fontSize: fontSize.xs,
          color: weightsOpen ? 'var(--ink)' : 'var(--ink-soft)',
          '&:hover': { color: colors.primary },
          userSelect: 'none',
        }}
      >
        {weightsOpen ? 'weights ▾' : 'weights ▸'}
      </Box>
      {weightsOpen && (
        <Box
          sx={{
            p: { xs: 1.25, sm: 2 },
            minWidth: { xs: 220, sm: 280 },
            border: '1px solid var(--rule)',
            borderRadius: '4px',
            bgcolor: 'var(--bg-surface)',
            display: 'flex',
            flexDirection: 'column',
            gap: { xs: 0.6, sm: 1.25 },
          }}
        >
          {TAG_CATEGORIES.map(cat => (
            <Box
              key={cat}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: { xs: 1, sm: 1.5 },
              }}
            >
              <Box
                component="span"
                sx={{
                  width: { xs: 45, sm: 55 },
                  flexShrink: 0,
                  fontSize: { xs: '0.65rem', sm: fontSize.xs },
                }}
              >
                {cat}
              </Box>
              <Slider
                size="small"
                min={0}
                max={5}
                step={0.1}
                value={weights[cat] ?? 1}
                onChange={(_, v) => setWeights(w => ({ ...w, [cat]: v as number }))}
                sx={{
                  flex: 1,
                  color: 'var(--ink-soft)',
                  py: { xs: 1, sm: 1.5 },
                  '& .MuiSlider-thumb': {
                    width: { xs: 12, sm: 14 },
                    height: { xs: 12, sm: 14 },
                    backgroundColor: 'var(--bg-surface)',
                    border: '2px solid currentColor',
                  },
                }}
              />
              <Box
                component="span"
                sx={{
                  width: 24,
                  textAlign: 'right',
                  fontSize: fontSize.xs,
                  fontVariantNumeric: 'tabular-nums',
                  color: 'var(--ink)',
                }}
              >
                {(weights[cat] ?? 1).toFixed(1)}
              </Box>
            </Box>
          ))}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: { xs: 1, sm: 1.5 },
              mt: { xs: 0, sm: 0.5 },
              pt: { xs: 0.6, sm: 1.25 },
              borderTop: '1px solid var(--rule)',
            }}
          >
            <Box
              component="span"
              sx={{
                width: { xs: 45, sm: 55 },
                flexShrink: 0,
                fontSize: { xs: '0.65rem', sm: fontSize.xs },
              }}
            >
              min_sim
            </Box>
            <Slider
              size="small"
              min={MIN_SIM_BOUNDS.min}
              max={MIN_SIM_BOUNDS.max}
              step={0.01}
              value={minSim}
              onChange={(_, v) => setMinSim(v as number)}
              sx={{
                flex: 1,
                color: 'var(--ink-soft)',
                py: { xs: 1, sm: 1.5 },
                '& .MuiSlider-thumb': {
                  width: { xs: 12, sm: 14 },
                  height: { xs: 12, sm: 14 },
                  backgroundColor: 'var(--bg-surface)',
                  border: '2px solid currentColor',
                },
              }}
            />
            <Box
              component="span"
              sx={{
                width: 24,
                textAlign: 'right',
                fontSize: fontSize.xs,
                fontVariantNumeric: 'tabular-nums',
                color: 'var(--ink)',
              }}
            >
              {minSim.toFixed(2)}
            </Box>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: { xs: 0, sm: 0.5 } }}>
            <Box
              component="button"
              onClick={resetWeights}
              sx={{
                all: 'unset',
                cursor: 'pointer',
                fontFamily: typography.mono,
                fontSize: fontSize.xs,
                color: 'var(--ink-soft)',
                '&:hover': { color: colors.primary },
              }}
            >
              reset
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
}
