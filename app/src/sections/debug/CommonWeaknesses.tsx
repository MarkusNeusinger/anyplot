import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { fontSize, semanticColors, typography } from 'src/theme';

export interface WeaknessData {
  text: string;
  count: number;
}

export function CommonWeaknesses({ weaknesses }: { weaknesses: WeaknessData[] }) {
  if (weaknesses.length === 0) return null;
  const maxWeakness = Math.max(...weaknesses.map(w => w.count), 1);

  return (
    <>
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>common weaknesses</em>} />
      </Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, alignItems: 'baseline' }}>
        {weaknesses.map(w => {
          const ratio = w.count / maxWeakness;
          const size =
            ratio >= 0.8
              ? fontSize.md
              : ratio >= 0.5
                ? fontSize.sm
                : ratio >= 0.25
                  ? fontSize.xs
                  : fontSize.xxs;
          const weight = ratio >= 0.5 ? 600 : 400;
          const opacity = ratio >= 0.8 ? 1 : ratio >= 0.5 ? 0.85 : ratio >= 0.25 ? 0.7 : 0.55;
          return (
            <Box
              key={w.text}
              sx={{
                fontFamily: typography.fontFamily,
                fontSize: size,
                fontWeight: weight,
                color: 'var(--ink-soft)',
                opacity,
                px: 0.75,
                py: 0.25,
                borderRadius: 0.5,
                bgcolor: 'var(--bg-surface)',
                border: '1px solid var(--rule)',
              }}
            >
              {w.text}
              <Box
                component="span"
                sx={{ fontSize: fontSize.micro, color: semanticColors.mutedText, ml: 0.5 }}
              >
                {w.count}
              </Box>
            </Box>
          );
        })}
      </Box>
    </>
  );
}
