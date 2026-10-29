import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { LIB_ABBREV, LIB_TO_LANG, LIBRARIES } from 'src/constants';
import { specPath } from 'src/routes/paths';
import { timeAgo } from 'src/sections/debug/format';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

import { SpecStatus } from './useDebugStatus';
import { countImpls, SortDir, SortKey } from './useSpecFilters';

interface DebugSpecsSectionProps {
  filteredSpecs: SpecStatus[];
  searchText: string;
  setSearchText: (v: string) => void;
  showIncomplete: boolean;
  setShowIncomplete: (v: boolean) => void;
  showLowScores: boolean;
  setShowLowScores: (v: boolean) => void;
  missingLibrary: string;
  setMissingLibrary: (v: string) => void;
  sortKey: SortKey;
  sortDir: SortDir;
  handleSort: (key: SortKey) => void;
}

function formatDateShort(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function scoreColor(score: number | null): string {
  if (score === null) return 'var(--ink-muted)';
  if (score >= 90) return colors.success;
  if (score >= 75) return colors.warning;
  return colors.error;
}

function HeaderCell({ children, center }: { children: React.ReactNode; center?: boolean }) {
  return (
    <Typography
      sx={{
        fontFamily: typography.fontFamily,
        fontSize: fontSize.xs,
        fontWeight: 600,
        color: 'var(--ink-soft)',
        textAlign: center ? 'center' : 'left',
      }}
    >
      {children}
    </Typography>
  );
}

function SortableHeader({
  label,
  active,
  dir,
  onClick,
  center,
}: {
  label: string;
  active: boolean;
  dir: SortDir;
  onClick: () => void;
  center?: boolean;
}) {
  return (
    <Box
      component="button"
      type="button"
      onClick={onClick}
      sx={{
        background: 'none',
        border: 'none',
        p: 0,
        cursor: 'pointer',
        fontFamily: typography.fontFamily,
        fontSize: fontSize.xs,
        fontWeight: 600,
        color: active ? colors.primary : 'var(--ink-soft)',
        textAlign: center ? 'center' : 'left',
        display: 'flex',
        alignItems: 'center',
        gap: 0.25,
        justifyContent: center ? 'center' : 'flex-start',
        '&:hover': { color: colors.primaryDark },
      }}
    >
      {label}
      {active && (
        <Box component="span" sx={{ fontSize: fontSize.micro }}>
          {dir === 'asc' ? '▲' : '▼'}
        </Box>
      )}
    </Box>
  );
}

export function DebugSpecsSection({
  filteredSpecs,
  searchText,
  setSearchText,
  showIncomplete,
  setShowIncomplete,
  showLowScores,
  setShowLowScores,
  missingLibrary,
  setMissingLibrary,
  sortKey,
  sortDir,
  handleSort,
}: DebugSpecsSectionProps) {
  return (
    <>
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>specs</em>} />
      </Box>

      {/* Filter Bar */}
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 2,
          mb: 3,
          alignItems: 'center',
          fontFamily: typography.fontFamily,
          fontSize: fontSize.sm,
        }}
      >
        <Box
          component="input"
          type="text"
          placeholder="search specs..."
          value={searchText}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchText(e.target.value)}
          sx={{
            flex: 1,
            minWidth: 200,
            p: 1,
            border: '1px solid var(--rule)',
            borderRadius: 1,
            bgcolor: 'var(--bg-surface)',
            color: 'var(--ink)',
            outline: 'none',
            '&:focus': { borderColor: colors.primary },
          }}
        />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Box component="label" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <input
              type="checkbox"
              checked={showIncomplete}
              onChange={e => setShowIncomplete(e.target.checked)}
            />
            incomplete ({'<'} LIBRARIES.length)
          </Box>
          <Box component="label" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <input
              type="checkbox"
              checked={showLowScores}
              onChange={e => setShowLowScores(e.target.checked)}
            />
            low score (avg {'<'} 90)
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box component="span" sx={{ color: 'var(--ink-soft)' }}>
              missing:
            </Box>
            <Box
              component="select"
              value={missingLibrary}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                setMissingLibrary(e.target.value)
              }
              sx={{
                p: 0.5,
                border: '1px solid var(--rule)',
                borderRadius: 1,
                bgcolor: 'var(--bg-surface)',
                color: 'var(--ink)',
                outline: 'none',
              }}
            >
              <option value="">(any)</option>
              {LIBRARIES.map(lib => (
                <option key={lib} value={lib}>
                  {lib}
                </option>
              ))}
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Desktop: matrix view */}
      <Box
        sx={{
          display: { xs: 'none', md: 'block' },
          overflowX: 'auto',
          border: '1px solid var(--rule)',
          borderRadius: 1,
        }}
      >
        <Box sx={{ minWidth: 1000 }}>
          {/* Header row */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: `180px minmax(180px, 1fr) 50px 50px repeat(${LIBRARIES.length}, 40px) 80px`,
              gap: 0,
              alignItems: 'center',
              px: 1,
              py: 0.75,
              borderBottom: '1px solid var(--rule)',
              bgcolor: 'var(--bg-elevated)',
            }}
          >
            <SortableHeader
              label="id"
              active={sortKey === 'id'}
              dir={sortDir}
              onClick={() => handleSort('id')}
            />
            <SortableHeader
              label="title"
              active={sortKey === 'title'}
              dir={sortDir}
              onClick={() => handleSort('title')}
            />
            <HeaderCell center>cvrg</HeaderCell>
            <SortableHeader
              label="avg"
              active={sortKey === 'avg_score'}
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
              active={sortKey === 'updated'}
              dir={sortDir}
              onClick={() => handleSort('updated')}
            />
          </Box>

          {/* Body rows */}
          {filteredSpecs.map(spec => {
            const implCount = countImpls(spec);
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
                    px: 1,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  {spec.id}
                </Link>
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    color: 'var(--ink)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    pr: 1,
                  }}
                  title={spec.title}
                >
                  {spec.title}
                </Typography>
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    color:
                      implCount === LIBRARIES.length
                        ? colors.success
                        : implCount > 0
                          ? colors.warning
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
