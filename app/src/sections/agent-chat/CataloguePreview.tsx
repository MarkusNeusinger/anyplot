/**
 * The catalogue plot the chat adapts, small in the page header beside the spec's title: the
 * preview of the library in use, in the site theme, so the plot the data should become stays in
 * view. It follows a library switch. A click (or Enter, or Space) opens it large in a dialog,
 * which keeps the keyboard focus inside until Escape, `.close()` or a click outside closes it and
 * returns the focus to the thumbnail. Without a preview (the spec did not load) nothing shows.
 *
 * Both sizes come from the catalogue's responsive files (`buildSrcSet`): the thumbnail loads the
 * 400 px WebP, the large view up to the full-size original.
 */

import { useId, useState } from 'react';

import Box from '@mui/material/Box';
import Dialog from '@mui/material/Dialog';

import { useTheme } from 'src/hooks/useLayoutContext';
import { actionButtonSx, labelSx } from 'src/sections/agent-chat/styles';
import { colors, fontSize } from 'src/theme';
import { buildDetailSrcSet, buildSrcSet, getFallbackSrc } from 'src/utils/responsiveImage';
import { selectPreviewUrl, type ThemedPreviewSource } from 'src/utils/themedPreview';

/** The thumbnail's width; its height follows the catalogue's 16:9. */
const THUMB_WIDTH = { xs: 64, sm: 80 } as const;
const THUMB_SIZES = '80px';
/** The large view takes the dialog's width, at most `lg` (1200 px) less its padding. */
const LARGE_SIZES = '(max-width: 1232px) calc(100vw - 96px), 1136px';

export interface CataloguePreviewProps {
  /** The spec's title, for the dialog's heading. */
  title: string;
  /** The library in use, whose catalogue plot shows. */
  library: string;
  /** That library's catalogue previews; null without one. */
  preview: ThemedPreviewSource | null;
}

function Picture({
  url,
  srcSet,
  sizes,
  alt,
}: {
  url: string;
  srcSet: (format: 'webp' | 'png') => string;
  sizes: string;
  alt: string;
}) {
  return (
    <Box component="picture" sx={{ display: 'block', lineHeight: 0 }}>
      <source type="image/webp" srcSet={srcSet('webp')} sizes={sizes} />
      <source type="image/png" srcSet={srcSet('png')} sizes={sizes} />
      <Box
        component="img"
        src={getFallbackSrc(url)}
        alt={alt}
        sizes={sizes}
        sx={{ display: 'block', width: '100%', height: 'auto' }}
      />
    </Box>
  );
}

export function CataloguePreview({ title, library, preview }: CataloguePreviewProps) {
  const { isDark } = useTheme();
  const [open, setOpen] = useState(false);
  const titleId = useId();
  const url = selectPreviewUrl(preview, isDark);
  if (!url) return null;

  return (
    <>
      <Box
        component="button"
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        aria-label={`Show the ${library} catalogue plot large`}
        data-testid="catalogue-thumbnail"
        sx={{
          flex: 'none',
          width: THUMB_WIDTH,
          aspectRatio: '16 / 9',
          p: 0,
          overflow: 'hidden',
          cursor: 'zoom-in',
          bgcolor: 'var(--bg-elevated)',
          border: '1px solid var(--rule)',
          borderRadius: '4px',
          transition: 'border-color 0.2s',
          '&:hover': { borderColor: colors.primary },
          '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
          '& picture': { height: '100%' },
          '& img': { height: '100%', objectFit: 'cover' },
        }}
      >
        {/* The button's name says what it shows; the image adds nothing for a screen reader. */}
        <Picture url={url} srcSet={format => buildSrcSet(url, format)} sizes={THUMB_SIZES} alt="" />
      </Box>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth="lg"
        aria-labelledby={titleId}
        slotProps={{
          paper: {
            sx: {
              bgcolor: 'var(--bg-elevated)',
              backgroundImage: 'none',
              color: 'var(--ink)',
              border: '1px solid var(--rule)',
              borderRadius: 2,
              m: { xs: 2, sm: 4 },
              width: { xs: 'calc(100% - 32px)', sm: 'calc(100% - 64px)' },
            },
          },
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            px: { xs: 1.5, sm: 2 },
            pt: 1.25,
            pb: 1,
          }}
        >
          <Box
            component="h2"
            id={titleId}
            sx={{
              ...labelSx,
              fontSize: fontSize.md,
              color: 'var(--ink)',
              fontWeight: 600,
              m: 0,
              flex: '1 1 auto',
              minWidth: 0,
              overflowWrap: 'anywhere',
            }}
          >
            # {title} · {library}
          </Box>
          <Box
            component="button"
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close the catalogue plot"
            sx={{ ...actionButtonSx, flex: 'none' }}
          >
            .close()
          </Box>
        </Box>
        <Box
          sx={{
            mx: { xs: 1.5, sm: 2 },
            mb: { xs: 1.5, sm: 2 },
            border: '1px solid var(--rule)',
            borderRadius: 1,
            overflow: 'hidden',
          }}
        >
          <Picture
            url={url}
            srcSet={format => buildDetailSrcSet(url, format)}
            sizes={LARGE_SIZES}
            alt={`${title} in ${library}, the plot from the catalogue`}
          />
        </Box>
      </Dialog>
    </>
  );
}
