import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Box from '@mui/material/Box';
import ButtonBase from '@mui/material/ButtonBase';
import Collapse from '@mui/material/Collapse';
import Typography from '@mui/material/Typography';

import { MdHeading } from 'src/sections/spec-detail/SpecTabs/md';
import { colors, semanticColors, typography } from 'src/theme';

interface QualityTabProps {
  qualityScore: number | null;
  criteriaChecklist?: Record<string, unknown>;
  expandedCategories: Record<string, boolean>;
  onToggleCategory: (category: string) => void;
}

export function QualityTab({
  qualityScore,
  criteriaChecklist,
  expandedCategories,
  onToggleCategory,
}: QualityTabProps) {
  return (
    <Box
      sx={{
        bgcolor: 'var(--bg-page)',
        p: 3,
        borderRadius: 1,
        fontFamily: typography.fontFamily,
      }}
    >
      {/* Score */}
      <MdHeading level={2}>Score</MdHeading>
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: '2rem',
          fontWeight: 700,
          color:
            qualityScore !== null && qualityScore >= 90
              ? colors.success
              : qualityScore !== null && qualityScore >= 70
                ? colors.warning
                : colors.error,
        }}
      >
        {qualityScore !== null ? `${Math.round(qualityScore)}/100` : 'N/A'}
      </Typography>

      {/* Criteria Checklist */}
      {criteriaChecklist && Object.keys(criteriaChecklist).length > 0 && (
        <>
          <MdHeading level={2}>Breakdown</MdHeading>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {Object.entries(criteriaChecklist).map(([category, data]) => {
              const catData = data as {
                score?: number;
                max?: number;
                items?: Array<{
                  id: string;
                  name: string;
                  score: number;
                  max: number;
                  passed: boolean;
                  comment?: string;
                }>;
              };
              const score = catData.score ?? 0;
              const max = catData.max ?? 0;
              const pct = max > 0 ? (score / max) * 100 : 0;
              const items = catData.items || [];
              const isExpanded = expandedCategories[category] ?? false;

              return (
                <Box key={category}>
                  {/* Category header - clickable */}
                  <ButtonBase
                    onClick={() => items.length > 0 && onToggleCategory(category)}
                    disabled={items.length === 0}
                    disableRipple
                    aria-expanded={items.length > 0 ? isExpanded : undefined}
                    sx={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      mb: 0.5,
                      textAlign: 'left',
                      cursor: items.length > 0 ? 'pointer' : 'default',
                      '&:hover': items.length > 0 ? { opacity: 0.8 } : {},
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {items.length > 0 &&
                        (isExpanded ? (
                          <ExpandLessIcon sx={{ fontSize: '1rem', color: 'var(--ink-muted)' }} />
                        ) : (
                          <ExpandMoreIcon sx={{ fontSize: '1rem', color: 'var(--ink-muted)' }} />
                        ))}
                      <Typography
                        sx={{
                          fontFamily: typography.fontFamily,
                          fontSize: '0.85rem',
                          color: semanticColors.labelText,
                        }}
                      >
                        {category.replace(/_/g, ' ')}
                      </Typography>
                    </Box>
                    <Typography
                      sx={{
                        fontFamily: typography.fontFamily,
                        fontSize: '0.85rem',
                        color: semanticColors.mutedText,
                      }}
                    >
                      {score}/{max}
                    </Typography>
                  </ButtonBase>
                  {/* Progress bar */}
                  <Box
                    sx={{
                      height: 4,
                      bgcolor: 'var(--rule)',
                      borderRadius: 2,
                      overflow: 'hidden',
                    }}
                  >
                    <Box
                      sx={{
                        height: '100%',
                        width: `${pct}%`,
                        bgcolor:
                          pct >= 90 ? colors.success : pct >= 70 ? colors.warning : colors.error,
                        borderRadius: 2,
                      }}
                    />
                  </Box>
                  {/* Expandable items */}
                  <Collapse in={isExpanded}>
                    <Box
                      sx={{
                        mt: 1,
                        ml: 2,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 0.75,
                      }}
                    >
                      {items.map(item => (
                        <Box
                          key={item.id}
                          sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}
                        >
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <Box
                                sx={{
                                  width: 6,
                                  height: 6,
                                  borderRadius: '50%',
                                  bgcolor:
                                    item.score === 0
                                      ? colors.error
                                      : item.score === item.max
                                        ? colors.success
                                        : colors.warning,
                                }}
                              />
                              <Typography
                                sx={{
                                  fontFamily: typography.fontFamily,
                                  fontSize: '0.85rem',
                                  color: semanticColors.labelText,
                                }}
                              >
                                {item.name}
                              </Typography>
                            </Box>
                            <Typography
                              sx={{
                                fontFamily: typography.fontFamily,
                                fontSize: '0.8rem',
                                color: 'var(--ink-muted)',
                              }}
                            >
                              {item.score}/{item.max}
                            </Typography>
                          </Box>
                          {item.comment && (
                            <Typography
                              sx={{
                                fontFamily: typography.fontFamily,
                                fontSize: '0.85rem',
                                color: semanticColors.mutedText,
                                ml: 1.5,
                                fontStyle: 'italic',
                              }}
                            >
                              {item.comment}
                            </Typography>
                          )}
                        </Box>
                      ))}
                    </Box>
                  </Collapse>
                </Box>
              );
            })}
          </Box>
        </>
      )}

      {/* No data message */}
      {qualityScore === null &&
        (!criteriaChecklist || Object.keys(criteriaChecklist).length === 0) && (
          <Typography
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: '0.85rem',
              color: 'var(--ink-muted)',
            }}
          >
            No quality data available.
          </Typography>
        )}
    </Box>
  );
}
