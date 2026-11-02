import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';

import { SectionHeader } from 'src/components/SectionHeader';
import { specPath } from 'src/routes/paths';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

export interface ProblemSpec {
  id: string;
  title: string;
  issue: string;
  value: string | null;
}

export function ProblemAreas({
  lowScoreThreshold,
  lowScoreSpecs,
  missingPreviewSpecs,
  missingTagsSpecs,
  oldestSpecs,
}: {
  lowScoreThreshold: number;
  lowScoreSpecs: ProblemSpec[];
  missingPreviewSpecs: ProblemSpec[];
  missingTagsSpecs: ProblemSpec[];
  oldestSpecs: ProblemSpec[];
}) {
  return (
    <>
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>problem areas</em>} />
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {[
          { title: `low scores (avg < ${lowScoreThreshold})`, items: lowScoreSpecs },
          { title: 'missing previews', items: missingPreviewSpecs },
          { title: 'missing tags', items: missingTagsSpecs },
          { title: 'oldest specs', items: oldestSpecs },
        ].map(section => (
          <Box
            key={section.title}
            component="details"
            sx={{
              border: '1px solid var(--rule)',
              borderRadius: 1,
              p: 0,
              '& > summary': { cursor: 'pointer', listStyle: 'none' },
              '& > summary::-webkit-details-marker': { display: 'none' },
            }}
          >
            <Box
              component="summary"
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                px: 1.5,
                py: 1,
                fontFamily: typography.fontFamily,
                fontSize: fontSize.xs,
                color: 'var(--ink-soft)',
              }}
            >
              <Box component="span" sx={{ color: semanticColors.mutedText }}>
                ▸
              </Box>
              <Box component="span" sx={{ fontWeight: 600 }}>
                {section.title}
              </Box>
              <Box component="span" sx={{ color: semanticColors.mutedText }}>
                {section.items.length}
              </Box>
            </Box>
            {section.items.length > 0 && (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  borderTop: '1px solid var(--rule)',
                }}
              >
                {section.items.map((item, idx) => (
                  <Link
                    key={`${item.id}-${idx}`}
                    component={RouterLink}
                    to={specPath(item.id)}
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: { xs: '1fr auto', sm: 'minmax(140px, 200px) 1fr auto' },
                      gap: 1,
                      px: 1.5,
                      py: 0.75,
                      alignItems: 'center',
                      textDecoration: 'none',
                      color: 'inherit',
                      fontFamily: typography.fontFamily,
                      fontSize: fontSize.xs,
                      borderTop: idx > 0 ? '1px solid var(--rule)' : 'none',
                      '&:hover': { bgcolor: 'var(--bg-surface)' },
                    }}
                  >
                    <Box
                      component="span"
                      sx={{
                        color: colors.primary,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {item.id}
                    </Box>
                    <Box
                      component="span"
                      sx={{
                        color: semanticColors.mutedText,
                        display: { xs: 'none', sm: 'inline' },
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {item.issue}
                    </Box>
                    {item.value && (
                      <Box
                        component="span"
                        sx={{ color: colors.error, whiteSpace: 'nowrap', textAlign: 'right' }}
                      >
                        {item.value}
                      </Box>
                    )}
                  </Link>
                ))}
              </Box>
            )}
          </Box>
        ))}
      </Box>
    </>
  );
}
