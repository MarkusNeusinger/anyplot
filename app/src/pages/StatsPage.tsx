import { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import Tooltip from '@mui/material/Tooltip';

import { useAnalytics } from '../hooks';
import { Breadcrumb } from '../components/Breadcrumb';
import { Footer } from '../components/Footer';
import { API_URL } from '../constants';
import { specPath } from '../utils/paths';
import { buildSrcSet, getFallbackSrc } from '../utils/responsiveImage';
import {
  typography,
  colors,
  semanticColors,
  fontSize,
  subheadingStyle,
} from '../theme';

interface LibraryStats {
  id: string;
  name: string;
  impl_count: number;
  avg_score: number | null;
  min_score: number | null;
  max_score: number | null;
  score_buckets: Record<string, number>;
  loc_buckets: Record<string, number>;
  avg_loc: number | null;
}

interface CoverageCell {
  score: number | null;
  has_impl: boolean;
}

interface CoverageRow {
  spec_id: string;
  title: string;
  libraries: Record<string, CoverageCell>;
}

interface TopImpl {
  spec_id: string;
  spec_title: string;
  library_id: string;
  quality_score: number;
  preview_url: string | null;
}

interface TimelinePoint {
  month: string;
  count: number;
}

interface DashboardData {
  total_specs: number;
  total_implementations: number;
  total_interactive: number;
  total_lines_of_code: number;
  avg_quality_score: number | null;
  coverage_percent: number;
  library_stats: LibraryStats[];
  coverage_matrix: CoverageRow[];
  top_implementations: TopImpl[];
  tag_distribution: Record<string, Record<string, number>>;
  score_distribution: Record<string, number>;
  timeline: TimelinePoint[];
}

function scoreColor(score: number | null): string {
  if (score === null) return colors.gray[200];
  if (score >= 90) return colors.success;
  if (score >= 75) return colors.warning;
  return colors.error;
}


function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

export function StatsPage() {
  const { trackPageview, trackEvent } = useAnalytics();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    trackPageview('/stats');
  }, [trackPageview]);

  useEffect(() => {
    fetch(`${API_URL}/insights/dashboard`)
      .then(r => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <Box sx={{ maxWidth: 960, mx: 'auto', px: 2, py: 4, textAlign: 'center' }}>
      <Typography sx={{ fontFamily: typography.fontFamily, color: semanticColors.mutedText }}>loading stats...</Typography>
    </Box>
  );

  if (error || !data) return (
    <Box sx={{ maxWidth: 960, mx: 'auto', px: 2, py: 4, textAlign: 'center' }}>
      <Typography sx={{ fontFamily: typography.fontFamily, color: colors.error }}>failed to load stats{error ? `: ${error}` : ''}</Typography>
    </Box>
  );

  const maxTimeline = Math.max(...data.timeline.map(t => t.count), 1);

  return (
    <>
      <Helmet>
        <title>stats | anyplot.ai</title>
        <meta name="description" content="Platform statistics for anyplot.ai — plot counts, quality scores, library coverage, and more." />
      </Helmet>

      <Box sx={{ maxWidth: 960, mx: 'auto', px: 2, py: 2 }}>
        <Breadcrumb items={[{ label: 'anyplot.ai', shortLabel: 'ap', to: '/' }, { label: 'stats' }]} />

        {/* Summary Counters */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(6, 1fr)' }, gap: 2, mt: 3, mb: 4 }}>
          {[
            { label: 'specifications', value: data.total_specs, suffix: '' },
            { label: 'implementations', value: data.total_implementations, suffix: '' },
            { label: 'interactive', value: data.total_interactive, suffix: '' },
            { label: 'lines of code', value: data.total_lines_of_code, suffix: '' },
            { label: 'avg quality', value: data.avg_quality_score, suffix: '' },
            { label: 'coverage', value: data.coverage_percent, suffix: '%' },
          ].map(item => (
            <Box key={item.label} sx={{ textAlign: 'center', p: 2, border: `1px solid ${colors.gray[100]}`, borderRadius: 1 }}>
              <Typography sx={{ fontFamily: typography.serif, fontSize: '2rem', fontWeight: 300, color: colors.gray[800], lineHeight: 1.2 }}>
                {typeof item.value === 'number' ? `${formatNum(item.value)}${item.suffix}` : '—'}
              </Typography>
              <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, mt: 0.5 }}>
                {item.label}
              </Typography>
            </Box>
          ))}
        </Box>
        <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: semanticColors.mutedText, textAlign: 'center', mt: -2, mb: 3 }}>
          visitor analytics at{' '}
          <Link href="https://plausible.io/anyplot.ai" target="_blank" rel="noopener noreferrer"
            onClick={() => trackEvent('external_link', { destination: 'plausible' })}
            sx={{ color: semanticColors.mutedText, textDecoration: 'none', '&:hover': { color: colors.primaryDark } }}
          >plausible.io/anyplot.ai</Link>
        </Typography>

        {/* Library Stats — dual mini histograms per library */}
        <Typography sx={subheadingStyle}>libraries</Typography>
        {/* Quality distribution per library */}
        <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, mb: 1 }}>
          quality distribution 50–100 · count · avg
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {[...data.library_stats].sort((a, b) => (b.avg_score ?? 0) - (a.avg_score ?? 0)).map(lib => {
            const allBuckets = Array.from({ length: 10 }, (_, i) => {
              const lo = 50 + i * 5;
              const key = `${lo}-${lo + 5}`;
              return [key, lib.score_buckets[key] ?? 0] as const;
            });
            const maxBucket = Math.max(...allBuckets.map(([, c]) => c), 1);
            return (
              <Box key={lib.id} sx={{ display: 'flex', alignItems: 'flex-end', gap: 1.5 }}>
                <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, width: 80, textAlign: 'right', flexShrink: 0, pb: '2px' }}>
                  {lib.name}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: '1px', height: 22, flex: 1 }}>
                  {allBuckets.map(([bucket, count]) => {
                    const lo = parseInt(bucket.split('-')[0]);
                    return (
                      <Tooltip key={bucket} title={`${bucket}: ${count}`} arrow>
                        <Box sx={{
                          flex: 1,
                          height: count > 0 ? `${Math.max((count / maxBucket) * 100, 15)}%` : 0,
                          bgcolor: scoreColor(lo >= 90 ? 95 : lo >= 75 ? 80 : 50),
                          opacity: 0.6,
                          borderRadius: '1px 1px 0 0',
                        }} />
                      </Tooltip>
                    );
                  })}
                </Box>
                <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: semanticColors.mutedText, width: 70, flexShrink: 0, pb: '2px', textAlign: 'right' }}>
                  {lib.impl_count} · {lib.avg_score ?? '—'}
                </Typography>
              </Box>
            );
          })}
        </Box>

        {/* LOC distribution per library */}
        <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, mt: 2, mb: 1 }}>
          lines of code per implementation 0–400+ · avg
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {[...data.library_stats].sort((a, b) => (a.avg_loc ?? 999) - (b.avg_loc ?? 999)).map(lib => {
            const locRanges = Array.from({ length: 20 }, (_, i) => `${i * 20}-${(i + 1) * 20}`).concat('400+');
            const locBuckets = locRanges.map(key => [key, lib.loc_buckets[key] ?? 0] as const);
            const maxLoc = Math.max(...locBuckets.map(([, c]) => c), 1);
            return (
              <Box key={lib.id} sx={{ display: 'flex', alignItems: 'flex-end', gap: 1.5 }}>
                <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, width: 80, textAlign: 'right', flexShrink: 0, pb: '2px' }}>
                  {lib.name}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: '1px', height: 22, flex: 1 }}>
                  {locBuckets.map(([bucket, count]) => (
                    <Tooltip key={bucket} title={`${bucket} lines: ${count}`} arrow>
                      <Box sx={{
                        flex: 1,
                        height: count > 0 ? `${Math.max((count / maxLoc) * 100, 15)}%` : 0,
                        bgcolor: colors.primaryDark,
                        opacity: 0.4,
                        borderRadius: '1px 1px 0 0',
                      }} />
                    </Tooltip>
                  ))}
                </Box>
                <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: semanticColors.mutedText, width: 70, flexShrink: 0, pb: '2px', textAlign: 'right' }}>
                  avg {lib.avg_loc?.toFixed(0) ?? '—'}
                </Typography>
              </Box>
            );
          })}
        </Box>

        {/* Coverage dot matrix — right after libraries */}
        <Typography sx={subheadingStyle}>coverage</Typography>
        <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, mb: 1 }}>
          {data.coverage_percent}% · {data.total_implementations} of {data.total_specs * 9} possible
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '2px' }}>
          {data.coverage_matrix.map(row => {
            const count = Object.values(row.libraries).filter(c => c.has_impl).length;
            const intensity = count / 9;
            return (
              <Tooltip key={row.spec_id} title={`${row.title}: ${count}/9`} arrow>
                <Link
                  component={RouterLink}
                  to={specPath(row.spec_id)}
                  sx={{
                    display: 'block', width: 10, height: 10, borderRadius: '2px',
                    bgcolor: count === 0 ? colors.gray[100] : `rgba(34, 197, 94, ${0.15 + intensity * 0.7})`,
                    textDecoration: 'none',
                    '&:hover': { outline: `1px solid ${colors.success}` },
                  }}
                />
              </Tooltip>
            );
          })}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
          <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.micro, color: semanticColors.mutedText }}>less</Typography>
          {[0, 0.25, 0.5, 0.75, 1].map(v => (
            <Box key={v} sx={{ width: 8, height: 8, borderRadius: '1px', bgcolor: `rgba(34, 197, 94, ${0.15 + v * 0.7})` }} />
          ))}
          <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.micro, color: semanticColors.mutedText }}>more</Typography>
        </Box>

        {/* Timeline */}
        {data.timeline.length > 0 && (
          <>
            <Typography sx={subheadingStyle}>timeline</Typography>
            <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 0.25, height: 70, overflow: 'hidden' }}>
              {data.timeline.slice(-24).map(point => (
                <Tooltip key={point.month} title={`${point.month}: ${point.count} new`} arrow>
                  <Box sx={{
                    flex: 1,
                    height: `${Math.max((point.count / maxTimeline) * 100, 3)}%`,
                    bgcolor: colors.primaryDark,
                    opacity: 0.5,
                    borderRadius: '2px 2px 0 0',
                    minHeight: 2,
                    '&:hover': { opacity: 0.8 },
                    transition: 'opacity 0.15s ease',
                  }} />
                </Tooltip>
              ))}
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.25 }}>
              <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.micro, color: semanticColors.mutedText }}>
                {data.timeline.slice(-24)[0]?.month ?? data.timeline[0]?.month}
              </Typography>
              <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.micro, color: semanticColors.mutedText }}>
                {data.timeline[data.timeline.length - 1]?.month}
              </Typography>
            </Box>
          </>
        )}

        {/* Top Implementations */}
        <Typography sx={subheadingStyle}>top rated</Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' }, gap: 1.5 }}>
          {data.top_implementations.slice(0, 8).map((impl) => (
            <Link
              key={`${impl.spec_id}-${impl.library_id}`}
              component={RouterLink}
              to={specPath(impl.spec_id, impl.library_id)}
              sx={{ textDecoration: 'none', color: 'inherit', '&:hover': { opacity: 0.85 }, transition: 'opacity 0.15s ease' }}
              onClick={() => trackEvent('stats_top_impl_click', { spec: impl.spec_id, library: impl.library_id })}
            >
              <Box sx={{ border: `1px solid ${colors.gray[100]}`, borderRadius: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ width: '100%', aspectRatio: '16/9', overflow: 'hidden', flexShrink: 0 }}>
                  {impl.preview_url ? (
                    <Box component="picture" sx={{ display: 'block', width: '100%', height: '100%' }}>
                      <source type="image/webp" srcSet={buildSrcSet(impl.preview_url, 'webp')} sizes="(max-width: 599px) 50vw, 25vw" />
                      <source type="image/png" srcSet={buildSrcSet(impl.preview_url, 'png')} sizes="(max-width: 599px) 50vw, 25vw" />
                      <Box component="img" src={getFallbackSrc(impl.preview_url)} alt={impl.spec_title} loading="lazy"
                        sx={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                      />
                    </Box>
                  ) : (
                    <Box sx={{ width: '100%', height: '100%', bgcolor: colors.gray[50] }} />
                  )}
                </Box>
                <Box sx={{ p: 1 }}>
                  <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: colors.gray[700], lineHeight: 1.3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {impl.spec_title}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.25 }}>
                    <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: semanticColors.mutedText }}>
                      {impl.library_id}
                    </Typography>
                    <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: scoreColor(impl.quality_score), fontWeight: 600 }}>
                      {impl.quality_score}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Link>
          ))}
        </Box>

        {/* Tag Distribution */}
        <Typography sx={subheadingStyle}>tags</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          {Object.entries(data.tag_distribution).map(([category, values]) => {
            const paramMap: Record<string, string> = {
              plot_type: 'plot', data_type: 'data', domain: 'dom', features: 'feat',
              dependencies: 'dep', techniques: 'tech', patterns: 'pat', dataprep: 'prep', styling: 'style',
            };
            const param = paramMap[category];
            const entries = Object.entries(values);
            return (
            <Box key={category}>
              <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, mb: 0.5 }}>
                {category.replace('_', ' ')}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {entries.slice(0, 20).map(([tag, count]) => {
                  const size = count >= 100 ? fontSize.md : count >= 50 ? fontSize.xs : count >= 10 ? fontSize.xxs : fontSize.xxs;
                  const weight = count >= 50 ? 600 : count >= 10 ? 500 : 400;
                  const opacity = count >= 100 ? 1 : count >= 50 ? 0.85 : count >= 10 ? 0.7 : 0.5;
                  return (
                    <Link
                      key={tag}
                      component={RouterLink}
                      to={param ? `/?${param}=${tag}` : '/'}
                      sx={{
                        fontFamily: typography.fontFamily, fontSize: size, fontWeight: weight, textDecoration: 'none',
                        px: 0.75, py: 0.25, borderRadius: 0.5,
                        color: `rgba(55, 65, 81, ${opacity})`,
                        '&:hover': { color: colors.primaryDark },
                      }}
                    >
                      {tag}<Box component="span" sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.micro, color: semanticColors.mutedText, ml: 0.5 }}>{count}</Box>
                    </Link>
                  );
                })}
              </Box>
            </Box>
            );
          })}
        </Box>


        <Footer onTrackEvent={trackEvent} />
      </Box>
    </>
  );
}
