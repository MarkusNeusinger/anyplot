import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';

import { API_URL } from '../constants';
import { buildSrcSet, getFallbackSrc } from '../utils/responsiveImage';

interface RelatedSpec {
  id: string;
  title: string;
  preview_url: string | null;
  library_id: string | null;
  similarity: number;
  shared_tags: string[];
}

const mono = '"MonoLisa", "MonoLisa Fallback", monospace';

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

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({ limit: '6', mode });
    if (library && mode === 'full') params.set('library', library);
    fetch(`${API_URL}/insights/related/${specId}?${params}`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => { if (!cancelled) setRelated(data.related ?? []); })
      .catch(() => { if (!cancelled) setRelated([]); });
    return () => { cancelled = true; };
  }, [specId, mode, library]);

  if (related.length === 0) return null;

  return (
    <Box sx={{ mt: 4 }}>
      <Typography sx={{ fontFamily: mono, fontSize: '0.85rem', fontWeight: 600, color: '#374151', mb: 1.5 }}>
        {mode === 'full' ? 'similar implementations' : 'similar specifications'}
      </Typography>
      <Box sx={{
        display: 'grid',
        gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: `repeat(${Math.min(related.length, 6)}, 1fr)` },
        gap: 1.5,
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
              border: '1px solid #f3f4f6',
              borderRadius: 1,
              overflow: 'hidden',
              transition: 'transform 0.15s ease',
              '&:hover': { transform: 'scale(1.02)', borderColor: '#e5e7eb' },
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
              <Box sx={{ width: '100%', aspectRatio: '16/9', bgcolor: '#f9fafb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography sx={{ fontFamily: mono, fontSize: '0.7rem', color: '#d1d5db' }}>no preview</Typography>
              </Box>
            )}
            <Box sx={{ p: 1 }}>
              <Typography sx={{ fontFamily: mono, fontSize: '0.7rem', color: '#374151', lineHeight: 1.3 }} noWrap>
                {spec.title}
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 0.25 }}>
                <Typography sx={{ fontFamily: mono, fontSize: '0.6rem', color: '#9ca3af' }}>
                  {spec.shared_tags.length} tags in common
                </Typography>
                {mode === 'full' && spec.library_id && (
                  <Typography sx={{ fontFamily: mono, fontSize: '0.6rem', color: '#9ca3af' }}>
                    {spec.library_id}
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
