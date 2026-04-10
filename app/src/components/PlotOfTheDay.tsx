import { useEffect, useState, useCallback } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

import { API_URL, GITHUB_URL } from '../constants';
import { colors, typography, fontSize, semanticColors } from '../theme';
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
  library_version: string | null;
  python_version: string | null;
  date: string;
}

const mono = typography.fontFamily;

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
    <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
      <Box sx={{
        width: { xs: '92vw', sm: 'auto' },
        maxWidth: 700,
        borderRadius: 2,
        overflow: 'hidden',
        border: `1px solid ${colors.gray[200]}`,
        boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: '0 6px 24px rgba(0,0,0,0.1)',
        },
        opacity: 0,
        animation: 'potdFadeIn 1s ease-out 0.3s forwards',
        '@keyframes potdFadeIn': {
          '0%': { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      }}>
        {/* Top bar — full width terminal prompt */}
        <Box sx={{
          display: 'flex',
          alignItems: 'center',
          px: 1.5,
          py: 0.5,
          bgcolor: colors.gray[100],
          borderBottom: `1px solid ${colors.gray[200]}`,
          gap: 0.75,
        }}>
          <Typography sx={{ fontFamily: mono, fontSize: fontSize.xs, color: colors.primary, fontWeight: 600 }}>$</Typography>
          <Typography
            component="a"
            href={`${GITHUB_URL}/blob/main/plots/${data.spec_id}/implementations/${data.library_id}.py`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
            sx={{
              fontFamily: mono, fontSize: fontSize.xxs, color: semanticColors.mutedText,
              flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              textDecoration: 'none',
              '&:hover': { color: colors.primary },
            }}
          >
            python plots/{data.spec_id}/{data.library_id}.py
          </Typography>
          <IconButton
            onClick={handleDismiss}
            size="small"
            sx={{
              color: colors.gray[400], p: 0.25,
              '&:hover': { color: colors.gray[600] },
            }}
          >
            <CloseIcon sx={{ fontSize: fontSize.sm }} />
          </IconButton>
        </Box>

        {/* Middle — image left, info right */}
        <Box sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
        }}>
          {/* Image */}
          <Link
            component={RouterLink}
            to={`/${data.spec_id}/${data.library_id}`}
            sx={{
              display: 'block',
              textDecoration: 'none',
              flexShrink: 0,
              width: { xs: '100%', sm: '50%' },
              '&:hover': { opacity: 0.95 },
            }}
          >
            {data.preview_url && (
              <Box component="picture" sx={{ display: 'block' }}>
                <source type="image/webp" srcSet={buildSrcSet(data.preview_url, 'webp')} sizes="(max-width: 599px) 92vw, 350px" />
                <source type="image/png" srcSet={buildSrcSet(data.preview_url, 'png')} sizes="(max-width: 599px) 92vw, 350px" />
                <Box component="img" src={getFallbackSrc(data.preview_url)} alt={data.spec_title}
                  sx={{
                    width: '100%',
                    height: '100%',
                    aspectRatio: { xs: '16/9', sm: 'unset' },
                    objectFit: 'cover',
                    display: 'block',
                  }}
                />
              </Box>
            )}
          </Link>

          {/* Info */}
          <Box sx={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            flex: 1,
            minWidth: 0,
            p: 2,
            bgcolor: colors.gray[50],
            borderLeft: { xs: 'none', sm: `1px solid ${colors.gray[200]}` },
            borderTop: { xs: `1px solid ${colors.gray[200]}`, sm: 'none' },
          }}>
            {/* Label */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 1 }}>
              <AutoAwesomeIcon sx={{ fontSize: fontSize.sm, color: colors.accent }} />
              <Typography sx={{
                fontFamily: mono,
                fontSize: fontSize.sm,
                color: colors.gray[700],
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                fontWeight: 600,
              }}>
                plot of the day
              </Typography>
            </Box>

            {/* Title */}
            <Link
              component={RouterLink}
              to={`/${data.spec_id}/${data.library_id}`}
              sx={{
                textDecoration: 'none',
                color: colors.gray[800],
                '&:hover': { color: colors.primaryDark },
              }}
            >
              <Typography sx={{
                fontFamily: mono,
                fontSize: fontSize.lg,
                fontWeight: 600,
                lineHeight: 1.4,
              }}>
                {data.spec_title}
              </Typography>
            </Link>

            {/* Description */}
            {data.image_description && (
              <Typography sx={{
                fontFamily: mono,
                fontSize: fontSize.xs,
                color: semanticColors.subtleText,
                mt: 1,
                lineHeight: 1.5,
                fontStyle: 'italic',
                display: '-webkit-box',
                WebkitLineClamp: { xs: 2, sm: 3 },
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}>
                &ldquo;{data.image_description.trim()}&rdquo;
              </Typography>
            )}
          </Box>
        </Box>

        {/* Bottom bar — terminal output style */}
        <Box sx={{
          display: 'flex',
          alignItems: 'center',
          px: 1.5,
          py: 0.5,
          bgcolor: colors.gray[100],
          borderTop: `1px solid ${colors.gray[200]}`,
        }}>
          <Typography sx={{ fontFamily: mono, fontSize: fontSize.xxs, color: colors.primary, mr: 0.5 }}>
            &gt;&gt;&gt;
          </Typography>
          <Typography sx={{ fontFamily: mono, fontSize: fontSize.xxs, color: semanticColors.mutedText }}>
            plot.png saved
          </Typography>
          <Box sx={{ flex: 1 }} />
          <Typography sx={{ fontFamily: mono, fontSize: fontSize.xxs, color: colors.gray[300], mx: 1 }}>
            │
          </Typography>
          <Typography sx={{ fontFamily: mono, fontSize: fontSize.xxs, color: semanticColors.mutedText, whiteSpace: 'nowrap' }}>
            {data.library_name}{data.library_version && data.library_version !== 'unknown' ? ` ${data.library_version}` : ''} · Python {data.python_version || '3.13'}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}
