import { useEffect, useState, useCallback } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';

import { API_URL } from '../constants';
import { fontSize, semanticColors } from '../theme';
import { buildSrcSet, getFallbackSrc } from '../utils/responsiveImage';

interface PlotOfTheDayData {
  spec_id: string;
  spec_title: string;
  description: string | null;
  library_id: string;
  library_name: string;
  quality_score: number;
  preview_url: string | null;
  image_description: string | null;
  date: string;
}

const mono = '"MonoLisa", "MonoLisa Fallback", monospace';

export function PlotOfTheDay() {
  const [data, setData] = useState<PlotOfTheDayData | null>(null);
  const [dismissed, setDismissed] = useState(() => window.sessionStorage.getItem('potd_dismissed') === 'true');

  useEffect(() => {
    if (dismissed) return;
    fetch(`${API_URL}/insights/plot-of-the-day`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(setData)
      .catch(() => {});
  }, [dismissed]);

  const handleDismiss = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setDismissed(true);
    window.sessionStorage.setItem('potd_dismissed', 'true');
  }, []);

  if (!data || dismissed) return null;

  return (
    <Box sx={{
      display: 'flex',
      flexDirection: { xs: 'column', sm: 'row' },
      gap: 2,
      p: 2,
      mb: 2,
      border: '1px solid #f3f4f6',
      borderLeft: '3px solid #FFD43B',
      borderRadius: 1,
      bgcolor: '#fffef5',
      position: 'relative',
    }}>
      <IconButton
        onClick={handleDismiss}
        size="small"
        sx={{
          position: 'absolute', top: 4, right: 4,
          color: '#d1d5db', p: 0.25,
          '&:hover': { color: '#9ca3af' },
        }}
      >
        <CloseIcon sx={{ fontSize: fontSize.lg }} />
      </IconButton>
      {/* Preview image */}
      {data.preview_url && (
        <Link component={RouterLink} to={`/${data.spec_id}/${data.library_id}`}
          sx={{ flexShrink: 0, display: 'block', '&:hover': { opacity: 0.9 } }}
        >
          <Box component="picture" sx={{ display: 'block' }}>
            <source type="image/webp" srcSet={buildSrcSet(data.preview_url, 'webp')} sizes="200px" />
            <source type="image/png" srcSet={buildSrcSet(data.preview_url, 'png')} sizes="200px" />
            <Box component="img" src={getFallbackSrc(data.preview_url)} alt={data.spec_title}
              sx={{
                width: { xs: '100%', sm: 200 },
                aspectRatio: '16/9',
                objectFit: 'cover',
                borderRadius: 0.5,
                display: 'block',
              }}
            />
          </Box>
        </Link>
      )}

      {/* Info */}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <Typography sx={{ fontFamily: mono, fontSize: fontSize.xs, color: semanticColors.mutedText, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            plot of the day
          </Typography>
          <Typography sx={{ fontFamily: mono, fontSize: fontSize.xs, color: semanticColors.mutedText }}>
            {data.date}
          </Typography>
        </Box>

        <Link component={RouterLink} to={`/${data.spec_id}/${data.library_id}`}
          sx={{ textDecoration: 'none', color: 'inherit', '&:hover': { color: '#306998' } }}
        >
          <Typography sx={{ fontFamily: mono, fontSize: fontSize.lg, fontWeight: 600, color: '#1f2937', lineHeight: 1.3 }}>
            {data.spec_title}
          </Typography>
        </Link>

        <Typography sx={{ fontFamily: mono, fontSize: fontSize.sm, color: semanticColors.mutedText, mt: 0.25 }}>
          {data.library_name} · {data.quality_score}/100
        </Typography>

        {data.image_description && (
          <Typography sx={{
            fontFamily: mono, fontSize: fontSize.sm, color: semanticColors.subtleText, mt: 1, lineHeight: 1.6,
            fontStyle: 'italic',
            display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden',
          }}>
            "{data.image_description.trim()}"
          </Typography>
        )}
      </Box>
    </Box>
  );
}
