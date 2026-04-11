import { useEffect, useRef, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

import { API_URL, LIB_ABBREV } from '../constants';
import { buildSrcSet, getFallbackSrc } from '../utils/responsiveImage';
import { colors, fontSize, semanticColors, typography } from '../theme';

interface RelatedSpec {
  id: string;
  title: string;
  preview_url: string | null;
  library_id: string | null;
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
  const prevSpecIdRef = useRef(specId);

  // Reset expanded when specId changes (no effect needed)
  if (prevSpecIdRef.current !== specId) {
    prevSpecIdRef.current = specId;
    setExpanded(false);
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const params = new URLSearchParams({ limit: '24', mode });
    if (library && mode === 'full') params.set('library', library);
    fetch(`${API_URL}/insights/related/${specId}?${params}`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => { if (!cancelled) { setRelated(data.related ?? []); setLoading(false); } })
      .catch(() => { if (!cancelled) { setRelated([]); setLoading(false); } });
    return () => { cancelled = true; };
  }, [specId, mode, library]);

  // After loading, if no related specs, render nothing
  if (!loading && related.length === 0) return null;

  // Collapsed: CSS hides extra rows via gridAutoRows:0 + overflow:hidden

  // While loading, reserve space without showing the tab bar.
  // This prevents CLS both when results exist (common) and when they don't (rare).
  if (loading) {
    return (
      <Box sx={{ mt: 1.5, maxWidth: { xs: '100%', md: 1200, lg: 1400, xl: 1600 }, mx: 'auto', minHeight: { xs: 250, sm: 210 } }} />
    );
  }

  return (
    <Box sx={{
      mt: 1.5, maxWidth: { xs: '100%', md: 1200, lg: 1400, xl: 1600 }, mx: 'auto',
      animation: 'relatedFadeIn 0.4s ease-out',
      '@keyframes relatedFadeIn': { from: { opacity: 0 }, to: { opacity: 1 } },
    }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={expanded ? 0 : false}
          onChange={() => setExpanded((e) => !e)}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              fontFamily: typography.fontFamily,
              textTransform: 'none',
              fontSize: '0.875rem',
              minHeight: 48,
              transition: 'background-color 0.15s ease, color 0.15s ease',
              borderRadius: '4px 4px 0 0',
              '&:hover': { backgroundColor: colors.gray[100], color: colors.primary },
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
      <Box sx={{
        display: 'grid',
        gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)', lg: 'repeat(6, 1fr)' },
        columnGap: 2,
        rowGap: expanded ? 2 : 0,
        pt: 2,
        ...(!expanded && { gridTemplateRows: 'auto', gridAutoRows: 0, overflow: 'hidden' }),
      }}>
        {related.map(spec => (
          <Link
            key={spec.id}
            component={RouterLink}
            to={mode === 'full' && spec.library_id ? `/${spec.id}/${spec.library_id}` : `/${spec.id}`}
            onMouseEnter={() => onHoverTags?.(spec.shared_tags)}
            onMouseLeave={() => onHoverTags?.([])}
            sx={{
              textDecoration: 'none',
              color: 'inherit',
              border: `1px solid ${colors.gray[200]}`,
              borderRadius: 1,
              overflow: 'hidden',
              transition: 'transform 0.15s ease',
              '&:hover': { transform: 'scale(1.02)', borderColor: colors.gray[200] },
            }}
          >
            {spec.preview_url ? (
              <Box component="picture" sx={{ display: 'block' }}>
                <source type="image/webp" srcSet={buildSrcSet(spec.preview_url, 'webp')} sizes={SIZES} />
                <source type="image/png" srcSet={buildSrcSet(spec.preview_url, 'png')} sizes={SIZES} />
                <Box component="img" src={getFallbackSrc(spec.preview_url)} alt={spec.title}
                  sizes={SIZES} loading="lazy"
                  sx={{ width: '100%', aspectRatio: '16/9', objectFit: 'cover', display: 'block' }}
                />
              </Box>
            ) : (
              <Box sx={{ width: '100%', aspectRatio: '16/9', bgcolor: colors.gray[50], display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography sx={{ fontFamily: mono, fontSize: '0.7rem', color: colors.gray[300] }}>no preview</Typography>
              </Box>
            )}
            <Box sx={{ p: 1.5 }}>
              <Typography title={spec.title} sx={{ fontFamily: mono, fontSize: fontSize.sm, color: colors.gray[700], lineHeight: 1.3 }} noWrap>
                {spec.title}
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 0.25, gap: 0.5 }}>
                <Typography title={`${spec.shared_tags.length} tags in common: ${spec.shared_tags.join(', ')}`} sx={{ fontFamily: mono, fontSize: fontSize.xs, color: semanticColors.mutedText, whiteSpace: 'nowrap' }}>
                  {spec.shared_tags.length} tags in common
                </Typography>
                {mode === 'full' && spec.library_id && (
                  <Typography title={spec.library_id} sx={{ fontFamily: mono, fontSize: fontSize.xs, color: semanticColors.mutedText, whiteSpace: 'nowrap' }}>
                    {LIB_ABBREV[spec.library_id] || spec.library_id}
                  </Typography>
                )}
              </Box>
            </Box>
          </Link>
        ))}
      </Box>
    </Box>
  );
}
