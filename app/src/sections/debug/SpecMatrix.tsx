import React from 'react';

import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { LIB_ABBREV, LIB_TO_LANG, LIBRARIES } from 'src/constants';
import { specPath } from 'src/routes/paths';
import { formatDateShort, scoreColor } from 'src/sections/debug/debugFormat';
import { timeAgo } from 'src/sections/debug/format';
import { HeaderCell } from 'src/sections/debug/HeaderCell';
import { SortableHeader, SortDir } from 'src/sections/debug/SortableHeader';
import { debugControlSx } from 'src/sections/debug/styles';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

export interface SpecStatus {
  id: string;
  title: string;
  updated: string | null;
  avg_score: number | null;
  altair: number | null;
  bokeh: number | null;
  chartjs: number | null;
  d3: number | null;
  echarts: number | null;
  ggplot2: number | null;
  highcharts: number | null;
  letsplot: number | null;
  makie: number | null;
  matplotlib: number | null;
  muix: number | null;
  plotly: number | null;
  plotnine: number | null;
  pygal: number | null;
  seaborn: number | null;
}

export function SpecMatrix({
  searchText,
  setSearchText,
  showIncomplete,
  setShowIncomplete,
  showLowScores,
  setShowLowScores,
  missingLibrary,
  setMissingLibrary,
  filteredSpecs,
  totalSpecs,
  sortCol,
  sortDir,
  handleSort,
}: {
  searchText: string;
  setSearchText: (val: string) => void;
  showIncomplete: boolean;
  setShowIncomplete: (val: boolean | ((prev: boolean) => boolean)) => void;
  showLowScores: boolean;
  setShowLowScores: (val: boolean | ((prev: boolean) => boolean)) => void;
  missingLibrary: string;
  setMissingLibrary: (val: string) => void;
  filteredSpecs: SpecStatus[];
  totalSpecs: number;
  sortCol: keyof SpecStatus | 'coverage';
  sortDir: SortDir;
  handleSort: (col: keyof SpecStatus | 'coverage') => void;
}) {
  return (
    <>
      {/* Spec Matrix */}
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>specs</em>} />
      </Box>

      {/* Filter Bar */}
      <Box
        sx={{
          display: 'flex',
          gap: 1,
          mb: 2,
          flexWrap: { xs: 'nowrap', sm: 'wrap' },
          overflowX: { xs: 'auto', sm: 'visible' },
          pb: { xs: 0.5, sm: 0 },
        }}
      >
        <Box
          component="input"
          type="search"
          placeholder="search spec id or title..."
          value={searchText}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchText(e.target.value)}
          sx={{ ...debugControlSx, flex: { xs: '0 0 180px', sm: '1 1 220px' } }}
        />
        <Box
          component="button"
          type="button"
          onClick={() => setShowIncomplete(v => !v)}
          sx={{
            ...debugControlSx,
            cursor: 'pointer',
            flexShrink: 0,
            bgcolor: showIncomplete ? colors.highlight.bg : 'var(--bg-surface)',
            color: showIncomplete ? colors.highlight.text : 'var(--ink-soft)',
            borderColor: showIncomplete ? colors.primary : 'var(--rule)',
          }}
        >
          incomplete {'<'}
          {LIBRARIES.length}
        </Box>
        <Box
          component="button"
          type="button"
          onClick={() => setShowLowScores(v => !v)}
          sx={{
            ...debugControlSx,
            cursor: 'pointer',
            flexShrink: 0,
            bgcolor: showLowScores ? colors.highlight.bg : 'var(--bg-surface)',
            color: showLowScores ? colors.highlight.text : 'var(--ink-soft)',
            borderColor: showLowScores ? colors.primary : 'var(--rule)',
          }}
        >
          low scores {'<'}90
        </Box>
        <Box
          component="select"
          value={missingLibrary}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setMissingLibrary(e.target.value)}
          sx={{ ...debugControlSx, cursor: 'pointer', flexShrink: 0 }}
        >
          <option value="">missing library: any</option>
          {LIBRARIES.map(lib => (
            <option key={lib} value={lib}>
              missing: {lib}
            </option>
          ))}
        </Box>
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xs,
            color: semanticColors.mutedText,
            alignSelf: 'center',
            flexShrink: 0,
            ml: { xs: 0, sm: 'auto' },
          }}
        >
          {filteredSpecs.length} / {totalSpecs}
        </Typography>
      </Box>

      {/* Desktop: grid matrix */}
      <Box sx={{ display: { xs: 'none', md: 'block' }, overflowX: 'auto' }}>
        <Box sx={{ minWidth: 780 }}>
          {/* Header row */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: `180px minmax(180px, 1fr) 50px 50px repeat(${LIBRARIES.length}, 40px) 80px`,
              gap: 0,
              alignItems: 'center',
              position: 'sticky',
              top: 0,
              zIndex: 1,
              bgcolor: 'var(--bg-page)',
              borderBottom: '1px solid var(--rule)',
              py: 1,
            }}
          >
            <SortableHeader
              label="spec id"
              active={sortCol === 'id'}
              dir={sortDir}
              onClick={() => handleSort('id')}
            />
            <SortableHeader
              label="title"
              active={sortCol === 'title'}
              dir={sortDir}
              onClick={() => handleSort('title')}
            />
            <HeaderCell>#</HeaderCell>
            <SortableHeader
              label="avg"
              active={sortCol === 'avg_score'}
              dir={sortDir}
              onClick={() => handleSort('avg_score')}
              center
            />
            {LIBRARIES.map(lib => (
              <HeaderCell key={lib} center>
                {LIB_ABBREV[lib] ?? lib.slice(0, 3)}
              </HeaderCell>
            ))}
            <SortableHeader
              label="updated"
              active={sortCol === 'updated'}
              dir={sortDir}
              onClick={() => handleSort('updated')}
            />
          </Box>

          {/* Body rows */}
          {filteredSpecs.map(spec => {
            const implCount = ((spec: SpecStatus) => {
              let c = 0;
              for (const lib of LIBRARIES) if (spec[lib as keyof SpecStatus] !== null) c++;
              return c;
            })(spec);
            return (
              <Box
                key={spec.id}
                sx={{
                  display: 'grid',
                  gridTemplateColumns: `180px minmax(180px, 1fr) 50px 50px repeat(${LIBRARIES.length}, 40px) 80px`,
                  gap: 0,
                  alignItems: 'center',
                  py: 0.5,
                  borderBottom: '1px solid var(--rule)',
                  '&:hover': { bgcolor: 'var(--bg-surface)' },
                }}
              >
                <Link
                  component={RouterLink}
                  to={specPath(spec.id)}
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    color: colors.primary,
                    textDecoration: 'none',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  {spec.id}
                </Link>
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    color: semanticColors.labelText,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    pr: 1,
                  }}
                >
                  {spec.title}
                </Typography>
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    fontWeight: 600,
                    color:
                      implCount === LIBRARIES.length
                        ? colors.success
                        : implCount > 0
                          ? semanticColors.mutedText
                          : 'var(--ink-muted)',
                    textAlign: 'center',
                  }}
                >
                  {implCount}/{LIBRARIES.length}
                </Typography>
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    fontWeight: 600,
                    color: scoreColor(spec.avg_score),
                    textAlign: 'center',
                  }}
                >
                  {spec.avg_score !== null ? spec.avg_score.toFixed(1) : '—'}
                </Typography>
                {LIBRARIES.map(lib => {
                  const score = spec[lib as keyof SpecStatus] as number | null;
                  if (score === null) {
                    return (
                      <Box
                        key={lib}
                        sx={{
                          textAlign: 'center',
                          fontFamily: typography.fontFamily,
                          fontSize: fontSize.xs,
                          color: 'var(--ink-muted)',
                        }}
                      >
                        —
                      </Box>
                    );
                  }
                  return (
                    <Link
                      key={lib}
                      component={RouterLink}
                      to={specPath(spec.id, LIB_TO_LANG[lib] ?? 'python', lib)}
                      sx={{
                        textAlign: 'center',
                        textDecoration: 'none',
                        fontFamily: typography.fontFamily,
                        fontSize: fontSize.xs,
                        fontWeight: 600,
                        color: scoreColor(score),
                        '&:hover': { opacity: 0.7 },
                      }}
                    >
                      {Math.round(score)}
                    </Link>
                  );
                })}
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xxs,
                    color: semanticColors.mutedText,
                  }}
                >
                  {spec.updated ? formatDateShort(spec.updated) : '—'}
                </Typography>
              </Box>
            );
          })}
        </Box>
      </Box>

      {/* Mobile: card list */}
      <Box sx={{ display: { xs: 'flex', md: 'none' }, flexDirection: 'column', gap: 1.5 }}>
        {filteredSpecs.map(spec => (
          <Box
            key={spec.id}
            sx={{
              border: '1px solid var(--rule)',
              borderRadius: 1,
              p: 1.5,
              display: 'flex',
              flexDirection: 'column',
              gap: 1,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
              <Link
                component={RouterLink}
                to={specPath(spec.id)}
                sx={{
                  flex: 1,
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.sm,
                  color: 'var(--ink)',
                  textDecoration: 'none',
                  fontWeight: 500,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  '&:hover': { color: colors.primary },
                }}
              >
                {spec.title}
              </Link>
              <Typography
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xs,
                  color: scoreColor(spec.avg_score),
                  fontWeight: 600,
                  flexShrink: 0,
                }}
              >
                avg {spec.avg_score !== null ? spec.avg_score.toFixed(0) : '—'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {LIBRARIES.map(lib => {
                const score = spec[lib as keyof SpecStatus] as number | null;
                const missing = score === null;
                const abbrev = LIB_ABBREV[lib] ?? lib.slice(0, 3);
                const commonSx = {
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 0.5,
                  px: 0.75,
                  py: 0.25,
                  borderRadius: 0.5,
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xxs,
                  fontWeight: 600,
                  textDecoration: 'none',
                  bgcolor: missing ? 'var(--bg-elevated)' : `${scoreColor(score)}22`,
                  color: missing ? 'var(--ink-muted)' : scoreColor(score),
                };
                if (missing) {
                  return (
                    <Box key={lib} sx={commonSx}>
                      <Box component="span">{abbrev}</Box>
                      <Box component="span">—</Box>
                    </Box>
                  );
                }
                return (
                  <Link
                    key={lib}
                    component={RouterLink}
                    to={specPath(spec.id, LIB_TO_LANG[lib] ?? 'python', lib)}
                    sx={{ ...commonSx, '&:hover': { opacity: 0.75 } }}
                  >
                    <Box component="span">{abbrev}</Box>
                    <Box component="span">{Math.round(score)}</Box>
                  </Link>
                );
              })}
            </Box>
            <Box
              sx={{
                display: 'flex',
                gap: 1,
                fontFamily: typography.fontFamily,
                fontSize: fontSize.xxs,
                color: semanticColors.mutedText,
              }}
            >
              <Box component="span" sx={{ color: colors.primary }}>
                {spec.id}
              </Box>
              <Box component="span">·</Box>
              <Box component="span">{spec.updated ? timeAgo(spec.updated) : 'no activity'}</Box>
            </Box>
          </Box>
        ))}
      </Box>
    </>
  );
}
