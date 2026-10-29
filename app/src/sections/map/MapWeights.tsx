import { useState } from 'react';

import Box from '@mui/material/Box';
import Slider from '@mui/material/Slider';

import { MIN_SIM_BOUNDS } from 'src/hooks/useForceGraphSimulation';
import { TAG_CATEGORIES } from 'src/pages/MapPage.helpers';
import { colors, fontSize, typography } from 'src/theme';

interface MapWeightsProps {
  weights: Record<string, number>;
  setWeights: React.Dispatch<React.SetStateAction<Record<string, number>>>;
  minSim: number;
  setMinSim: (val: number) => void;
  resetWeights: () => void;
}

export function MapWeights({
  weights,
  setWeights,
  minSim,
  setMinSim,
  resetWeights,
}: MapWeightsProps) {
  const [weightsOpen, setWeightsOpen] = useState(false);

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
          // Bigger touch target on phones — `all: 'unset'` strips the
          // default button padding, so the bare text is only ~16 px
          // tall by default which is below the recommended 40 px.
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
                  minWidth: { xs: 78, sm: 100 },
                  fontFamily: typography.mono,
                  fontSize: fontSize.xs,
                }}
              >
                {cat}
              </Box>
              <Slider
                value={weights[cat]}
                onChange={(_, v) => setWeights(w => ({ ...w, [cat]: v as number }))}
                min={0}
                max={5}
                step={0.1}
                size="small"
                sx={{
                  flex: 1,
                  color: colors.primary,
                  // Compact knob & rail height so the rows can pack
                  // tighter on phones without the slider feeling cramped.
                  py: { xs: 0.25, sm: 0.5 },
                  '& .MuiSlider-rail': { opacity: 0.25 },
                }}
              />
              <Box
                component="span"
                sx={{
                  minWidth: 28,
                  textAlign: 'right',
                  fontFamily: typography.mono,
                  fontSize: fontSize.xs,
                  fontVariantNumeric: 'tabular-nums',
                  color: 'var(--ink)',
                }}
              >
                {weights[cat].toFixed(1)}
              </Box>
            </Box>
          ))}
          {/* Edge-threshold slider — controls KNN_MIN_SIM, the cutoff
              below which a candidate KNN edge is dropped. Lower = denser
              graph (more cross-cluster bridges); higher = sparser graph
              (cleaner clusters but more isolated outliers). */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: { xs: 1, sm: 1.5 },
              pt: { xs: 0.25, sm: 0.5 },
              borderTop: '1px dashed var(--rule)',
            }}
          >
            <Box
              component="span"
              sx={{
                minWidth: { xs: 78, sm: 100 },
                fontFamily: typography.mono,
                fontSize: fontSize.xs,
              }}
            >
              threshold
            </Box>
            <Slider
              value={minSim}
              onChange={(_, v) => setMinSim(v as number)}
              min={MIN_SIM_BOUNDS.min}
              max={MIN_SIM_BOUNDS.max}
              step={MIN_SIM_BOUNDS.step}
              size="small"
              sx={{
                flex: 1,
                color: colors.primary,
                py: { xs: 0.25, sm: 0.5 },
                '& .MuiSlider-rail': { opacity: 0.25 },
              }}
            />
            <Box
              component="span"
              sx={{
                minWidth: 32,
                textAlign: 'right',
                fontFamily: typography.mono,
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
