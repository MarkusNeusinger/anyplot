import { useEffect, useState } from 'react';

import { Link as RouterLink } from 'react-router-dom';

import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Typography from '@mui/material/Typography';

import { LIB_ABBREV } from 'src/constants';
import { useTheme } from 'src/hooks/useLayoutContext';
import { apiGet, endpoints } from 'src/lib/api';
import { colors, fontSize, semanticColors, typography } from 'src/theme';
import { specPath } from 'src/utils/paths';
import { buildSrcSet, getFallbackSrc } from 'src/utils/responsiveImage';
import { selectPreviewUrl } from 'src/utils/themedPreview';

interface RelatedSpec {
  id: string;
  title: string;
  // Theme-aware previews (optional during backend transition).
  preview_url_light?: string | null;
  preview_url_dark?: string | null;
  preview_url: string | null;
  library_id: string | null;
  language: string | null;
  similarity: number;
  shared_tags: string[];
}

const mono = typography.fontFamily;

// 6 columns max at md+, ~160px each → 400w is plenty
const SIZES = '(max-width: 599px) 50vw, (max-width: 899px) 33vw, 17vw';

interface RelatedSpecsProps {
  specId: string;
  /** "spec" = spec tags only (overview), "full" = spec + impl tags (detail) */
  mode?: 'spec' | 'full';
  /** Current library — in full mode, matches tags against this library's impl_tags */
  library?: string;
  /** Called when hovering a related spec card — passes shared tag values */
  onHoverTags?: (tags: string[]) => void;
}

export function RelatedSpecs({ specId, mode = 'spec', library, onHoverTags }: RelatedSpecsProps) {
  const [related, setRelated] = useState<RelatedSpec[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [prevDeps, setPrevDeps] = useState({ specId, mode, library });
  const { isDark } = useTheme();

  // React 19 "Adjusting state on prop change": runs during render, no cascading re-render.
  if (prevDeps.specId !== specId || prevDeps.mode !== mode || prevDeps.library !== library) {
    setPrevDeps({ specId, mode, library });
    setLoading(true);
    if (prevDeps.specId !== specId) setExpanded(false);
  }

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({ limit: '24', mode });
    if (library && mode === 'full') params.set('library', library);
    apiGet<{ related?: RelatedSpec[] }>(endpoints.relatedSpecs(specId, params.toString()))
      .then(data => {
        if (!cancelled) {
          setRelated(data.related ?? []);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRelated([]);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [specId, mode, library]);

  // After loading, if no related specs, render nothing
  if (!loading && related.length === 0) return null;

  // Collapsed: CSS hides extra rows via gridAutoRows:0 + overflow:hidden

  // While loading, reserve space without showing the tab bar.
  // This prevents CLS both when results exist (common) and when they don't (rare).
  if (loading) {
    return (
      <Box
        sx={{
          mt: 1.5,
          maxWidth: { xs: '100%', md: 1200, lg: 1400, xl: 1600 },
          mx: 'auto',
          minHeight: { xs: 250, sm: 210 },
        }}
      />
    );
  }

  return (
    <Box
      sx={{
        mt: 1.5,
        maxWidth: { xs: '100%', md: 1200, lg: 1400, xl: 1600 },
        mx: 'auto',
        animation: 'relatedFadeIn 0.4s ease-out',
        '@keyframes relatedFadeIn': { from: { opacity: 0 }, to: { opacity: 1 } },
      }}
    >
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={expanded ? 0 : false}
          onChange={() => setExpanded(e => !e)}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              fontFamily: typography.fontFamily,
              textTransform: 'none',
              fontSize: '0.875rem',
              minHeight: 48,
              transition: 'background-color 0.15s ease, color 0.15s ease',
              borderRadius: '4px 4px 0 0',
              '&:hover': { backgroundColor: 'var(--bg-surface)', color: colors.primary },
            },
            '& .Mui-selected': { color: colors.primary },
            '& .MuiTabs-indicator': { backgroundColor: colors.primary },
          }}
        >
          <Tab
            onClick={() => expanded && setExpanded(false)}
            icon={<AutoAwesomeIcon sx={{ fontSize: '1.1rem' }} />}
            iconPosition="start"
            label="Similar"
          />
        </Tabs>
      </Box>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: 'repeat(2, 1fr)',
            sm: 'repeat(3, 1fr)',
            md: 'repeat(4, 1fr)',
            lg: 'repeat(6, 1fr)',
          },
          columnGap: 2,
          rowGap: expanded ? 2 : 0,
          pt: 2,
          ...(!expanded && { gridTemplateRows: 'auto', gridAutoRows: 0, overflow: 'hidden' }),
        }}
      >
        {related.map(spec => {
          const previewUrl = selectPreviewUrl(spec, isDark);
          return (
            <Link
              key={spec.id}
              component={RouterLink}
              to={
                mode === 'full' && spec.library_id && spec.language
                  ? specPath(spec.id, spec.language, spec.library_id)
                  : specPath(spec.id)
              }
              onMouseEnter={() => onHoverTags?.(spec.shared_tags)}
              onMouseLeave={() => onHoverTags?.([])}
              sx={{
                textDecoration: 'none',
                color: 'inherit',
                border: '1px solid var(--rule)',
                borderRadius: 1,
                overflow: 'hidden',
                transition: 'transform 0.15s ease',
                '&:hover': { transform: 'scale(1.02)', borderColor: 'var(--ink-muted)' },
              }}
            >
              {previewUrl ? (
                <Box component="picture" key={previewUrl} sx={{ display: 'block' }}>
                  <source
                    type="image/webp"
                    srcSet={buildSrcSet(previewUrl, 'webp')}
                    sizes={SIZES}
                  />
                  <source type="image/png" srcSet={buildSrcSet(previewUrl, 'png')} sizes={SIZES} />
                  <Box
                    component="img"
                    src={getFallbackSrc(previewUrl)}
                    alt={spec.title}
                    sizes={SIZES}
                    loading="lazy"
                    sx={{
                      width: '100%',
                      aspectRatio: '16/9',
                      objectFit: 'cover',
                      display: 'block',
                    }}
                  />
                </Box>
              ) : (
                <Box
                  sx={{
                    width: '100%',
                    aspectRatio: '16/9',
                    bgcolor: 'var(--bg-elevated)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Typography
                    sx={{ fontFamily: mono, fontSize: '0.7rem', color: 'var(--ink-muted)' }}
                  >
                    no preview
                  </Typography>
                </Box>
              )}
              <Box sx={{ p: 1.5 }}>
                <Typography
                  title={spec.title}
                  sx={{
                    fontFamily: mono,
                    fontSize: fontSize.sm,
                    color: 'var(--ink-soft)',
                    lineHeight: 1.3,
                  }}
                  noWrap
                >
                  {spec.title}
                </Typography>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mt: 0.25,
                    gap: 0.5,
                  }}
                >
                  <Typography
                    title={`${spec.shared_tags.length} tags in common: ${spec.shared_tags.join(', ')}`}
                    sx={{
                      fontFamily: mono,
                      fontSize: fontSize.xs,
                      color: semanticColors.mutedText,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {spec.shared_tags.length} tags in common
                  </Typography>
                  {mode === 'full' && spec.library_id && (
                    <Typography
                      title={spec.library_id}
                      sx={{
                        fontFamily: mono,
                        fontSize: fontSize.xs,
                        color: semanticColors.mutedText,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {LIB_ABBREV[spec.library_id] || spec.library_id}
                    </Typography>
                  )}
                </Box>
              </Box>
            </Link>
          );
        })}
      </Box>
    </Box>
  );
}
