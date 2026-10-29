import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { specPath } from 'src/routes/paths';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

import { DebugStatus } from './useDebugStatus';
import { LOW_SCORE_THRESHOLD } from './useSpecFilters';

interface DebugOverviewSectionProps {
  data: DebugStatus;
}

function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

export function DebugOverviewSection({ data }: DebugOverviewSectionProps) {
  const totalImplsWithScore = data.library_stats.reduce(
    (acc, l) => acc + (l.avg_score !== null ? l.impl_count : 0),
    0
  );
  const weightedScoreSum = data.library_stats.reduce(
    (acc, l) => acc + (l.avg_score !== null ? l.avg_score * l.impl_count : 0),
    0
  );
  const avgQuality = totalImplsWithScore > 0 ? weightedScoreSum / totalImplsWithScore : null;

  const maxDaily = Math.max(...data.daily_impls.map(p => p.impls_updated), 1);
  const maxLibCount = Math.max(...data.library_stats.map(l => l.impl_count), 1);
  const maxWeakness = Math.max(...data.common_weaknesses.map(w => w.count), 1);

  const kpis: Array<{ label: string; value: number | null; suffix?: string }> = [
    { label: 'specs', value: data.total_specs },
    { label: 'impls', value: data.total_implementations },
    { label: 'coverage', value: data.coverage_percent, suffix: '%' },
    { label: 'avg quality', value: avgQuality !== null ? Math.round(avgQuality * 10) / 10 : null },
    { label: 'low score', value: data.low_score_specs.length },
    { label: 'stale specs', value: data.oldest_specs.length },
  ];

  const firstDate = data.daily_impls[0]?.date ?? '';
  const lastDate = data.daily_impls[data.daily_impls.length - 1]?.date ?? '';

  return (
    <>
      {/* KPIs */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: 'repeat(3, 1fr)', sm: 'repeat(6, 1fr)' },
          gap: 1.5,
          mb: 4,
        }}
      >
        {kpis.map(k => (
          <Box
            key={k.label}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              p: 1.5,
              bgcolor: 'var(--bg-elevated)',
              borderRadius: 1,
              border: '1px solid var(--rule)',
            }}
          >
            <Typography
              sx={{
                fontFamily: typography.fontFamily,
                fontSize: fontSize.xs,
                color: 'var(--ink-soft)',
                fontWeight: 500,
                mb: 0.5,
              }}
            >
              {k.label}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.25 }}>
              <Typography
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.lg,
                  color: 'var(--ink)',
                  fontWeight: 600,
                  lineHeight: 1,
                }}
              >
                {k.value !== null ? formatNum(k.value) : '—'}
              </Typography>
              {k.suffix && k.value !== null && (
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    color: 'var(--ink-soft)',
                    fontWeight: 600,
                  }}
                >
                  {k.suffix}
                </Typography>
              )}
            </Box>
          </Box>
        ))}
      </Box>

      {/* Daily Activity Bar Chart */}
      <SectionHeader prompt="❯" title={<em>daily activity</em>} />
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.xs,
          color: semanticColors.mutedText,
          mb: 1.5,
        }}
      >
        {firstDate && lastDate ? `${firstDate} to ${lastDate}` : 'no recent activity'}
      </Typography>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: '2px',
          height: 64,
          borderBottom: '1px solid var(--rule)',
          pb: 0.5,
          px: 1,
        }}
      >
        {data.daily_impls.map((pt, i) => {
          const ratio = Math.max(pt.impls_updated / maxDaily, 0.05); // min 5% height if > 0
          return (
            <Tooltip
              key={i}
              title={pt.impls_updated > 0 ? `${pt.impls_updated} updates on ${pt.date}` : pt.date}
              arrow
            >
              <Box
                sx={{
                  flex: 1,
                  height: pt.impls_updated === 0 ? '1px' : `${ratio * 100}%`,
                  bgcolor: pt.impls_updated === 0 ? 'var(--rule)' : colors.primary,
                  opacity: pt.impls_updated === 0 ? 1 : 0.7,
                  borderTopLeftRadius: 2,
                  borderTopRightRadius: 2,
                  transition: 'opacity 0.2s',
                  '&:hover': { opacity: 1 },
                }}
              />
            </Tooltip>
          );
        })}
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5, px: 1 }}>
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.micro,
            color: semanticColors.mutedText,
          }}
        >
          {firstDate}
        </Typography>
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.micro,
            color: semanticColors.mutedText,
          }}
        >
          {lastDate}
        </Typography>
      </Box>

      {/* Library Coverage */}
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>libraries</em>} />
      </Box>
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.xs,
          color: semanticColors.mutedText,
          mb: 2,
        }}
      >
        total verified implementations by target library
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {data.library_stats.map(lib => {
          const percent = ((lib.impl_count / maxLibCount) * 100).toFixed(1);
          return (
            <Box key={lib.id} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography
                sx={{
                  width: 100,
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.sm,
                  fontWeight: 500,
                  color: 'var(--ink)',
                }}
              >
                {lib.name}
              </Typography>
              <Box sx={{ flex: 1, height: 16, bgcolor: 'var(--bg-elevated)', borderRadius: 1 }}>
                <Box
                  sx={{
                    width: `${percent}%`,
                    height: '100%',
                    bgcolor: colors.primary,
                    borderRadius: 1,
                    opacity: 0.6,
                  }}
                />
              </Box>
              <Typography
                sx={{
                  width: 48,
                  textAlign: 'right',
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.sm,
                  fontWeight: 600,
                  color: 'var(--ink-soft)',
                }}
              >
                {lib.impl_count}
              </Typography>
            </Box>
          );
        })}
      </Box>

      {/* Recent Activity */}
      {data.recent_activity.length > 0 && (
        <>
          <Box sx={{ mt: 4 }}>
            <SectionHeader prompt="❯" title={<em>recent activity</em>} />
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {data.recent_activity.map((act, idx) => (
              <Link
                key={`${act.spec_id}-${act.library_id}-${idx}`}
                component={RouterLink}
                to={specPath(act.spec_id, act.language_id, act.library_id)}
                sx={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: 1.5,
                  py: 0.5,
                  px: 1,
                  borderRadius: 1,
                  textDecoration: 'none',
                  '&:hover': { bgcolor: 'var(--bg-surface)' },
                }}
              >
                <Typography
                  sx={{
                    width: 70,
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    color: colors.primary,
                    fontWeight: 600,
                  }}
                >
                  {act.quality_score !== null ? act.quality_score : '—'}
                </Typography>
                <Typography
                  sx={{
                    flex: 1,
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    color: 'var(--ink)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {act.spec_id}{' '}
                  <Box component="span" sx={{ color: 'var(--ink-muted)' }}>
                    ({act.library_id})
                  </Box>
                </Typography>
              </Link>
            ))}
          </Box>
        </>
      )}

      {/* Common Weaknesses */}
      {data.common_weaknesses.length > 0 && (
        <>
          <Box sx={{ mt: 4 }}>
            <SectionHeader prompt="❯" title={<em>common weaknesses</em>} />
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, alignItems: 'baseline' }}>
            {data.common_weaknesses.map(w => {
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
      )}

      {/* Problem Areas */}
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>problem areas</em>} />
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {[
          { title: `low scores (avg < ${LOW_SCORE_THRESHOLD})`, items: data.low_score_specs },
          { title: 'missing previews', items: data.missing_preview_specs },
          { title: 'missing tags', items: data.missing_tags_specs },
          { title: 'oldest specs', items: data.oldest_specs },
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
                p: 1.5,
                bgcolor: 'var(--bg-surface)',
                fontFamily: typography.fontFamily,
                fontSize: fontSize.sm,
                fontWeight: 600,
                color: 'var(--ink-soft)',
                '&:hover': { bgcolor: 'var(--bg-elevated)' },
              }}
            >
              {section.title} ({section.items.length})
            </Box>
            <Box sx={{ p: 1.5, pt: 1, borderTop: '1px solid var(--rule)' }}>
              {section.items.length === 0 ? (
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    color: semanticColors.mutedText,
                  }}
                >
                  all clear
                </Typography>
              ) : (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {section.items.map((it, idx) => (
                    <Link
                      key={`${it.id}-${idx}`}
                      component={RouterLink}
                      to={specPath(it.id)}
                      sx={{
                        display: 'inline-block',
                        px: 0.75,
                        py: 0.25,
                        bgcolor: 'var(--bg-elevated)',
                        border: '1px solid var(--rule)',
                        borderRadius: 1,
                        fontFamily: typography.fontFamily,
                        fontSize: fontSize.xs,
                        color: 'var(--ink)',
                        textDecoration: 'none',
                        '&:hover': { bgcolor: 'var(--bg-surface)' },
                      }}
                    >
                      {it.id}
                    </Link>
                  ))}
                </Box>
              )}
            </Box>
          </Box>
        ))}
      </Box>
    </>
  );
}
