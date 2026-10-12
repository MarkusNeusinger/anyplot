/**
 * The light and dark render of a case, fetched through the BFF's files proxy
 * (the bucket is private) and shown as blob URLs: an `<img src>` could not send
 * the admin token on a cross-origin API, and the blob path works for the
 * Access cookie too. The URLs are revoked when the case changes or the detail
 * closes.
 */

import { useEffect, useState } from 'react';

import Box from '@mui/material/Box';

import { agentApi, AgentApiError, type CaseFileName, type Theme } from 'src/lib/agent';
import { detailLabelSx, detailMutedSx } from 'src/sections/debug/styles';
import { colors } from 'src/theme';

const THEMES: readonly Theme[] = ['light', 'dark'];
const FILE: Record<Theme, CaseFileName> = { light: 'plot-light.png', dark: 'plot-dark.png' };

type ImageState = { state: 'ready'; url: string } | { state: 'failed'; code: string };

export interface CaseImagesProps {
  token: string;
  caseId: string;
  files: string[];
  specId: string | null;
  libraryId: string | null;
}

export function CaseImages({ token, caseId, files, specId, libraryId }: CaseImagesProps) {
  const hasLight = files.includes(FILE.light);
  const hasDark = files.includes(FILE.dark);
  // Keyed by the case, so a stale image never shows under another case.
  const [images, setImages] = useState<{ key: string } & Partial<Record<Theme, ImageState>>>({
    key: '',
  });

  useEffect(() => {
    let cancelled = false;
    const urls: string[] = [];
    const wanted = THEMES.filter(theme => (theme === 'light' ? hasLight : hasDark));
    for (const theme of wanted) {
      agentApi
        .caseFile(token, caseId, FILE[theme])
        .then(blob => {
          if (cancelled) return;
          const url = URL.createObjectURL(blob);
          urls.push(url);
          setImages(prev => ({
            ...(prev.key === caseId ? prev : { key: caseId }),
            [theme]: { state: 'ready', url },
          }));
        })
        .catch((err: unknown) => {
          if (cancelled) return;
          const code = err instanceof AgentApiError ? err.code : 'network';
          setImages(prev => ({
            ...(prev.key === caseId ? prev : { key: caseId }),
            [theme]: { state: 'failed', code },
          }));
        });
    }
    return () => {
      cancelled = true;
      for (const url of urls) URL.revokeObjectURL(url);
    };
  }, [token, caseId, hasLight, hasDark]);

  const subject = `${specId ?? 'unknown spec'} (${libraryId ?? 'unknown library'})`;

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
        gap: 2,
        minWidth: 0,
      }}
    >
      {THEMES.map(theme => {
        const present = theme === 'light' ? hasLight : hasDark;
        const image = images.key === caseId ? images[theme] : undefined;
        return (
          <Box key={theme} sx={{ minWidth: 0 }}>
            <Box sx={detailLabelSx}># {theme}</Box>
            <Box
              sx={{
                bgcolor: 'var(--bg-surface)',
                border: '1px solid var(--rule)',
                borderRadius: 1,
                p: 1,
                minHeight: 80,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {!present ? (
                <Box sx={detailMutedSx}>no {theme} render</Box>
              ) : image?.state === 'ready' ? (
                <Box
                  component="img"
                  src={image.url}
                  alt={`${theme} render of ${subject}`}
                  sx={{ display: 'block', maxWidth: '100%', height: 'auto' }}
                />
              ) : image?.state === 'failed' ? (
                <Box role="alert" sx={{ ...detailMutedSx, color: colors.error }}>
                  image failed ({image.code})
                </Box>
              ) : (
                <Box sx={detailMutedSx}>loading image…</Box>
              )}
            </Box>
          </Box>
        );
      })}
    </Box>
  );
}
