import { lazy, Suspense, useCallback, useState } from 'react';

import CheckIcon from '@mui/icons-material/Check';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';

import type { TrackEventFn } from 'src/sections/spec-detail/SpecTabs/utils';
import { semanticColors, typography } from 'src/theme';

const CodeHighlighter = lazy(() => import('src/components/CodeHighlighter'));

interface CodeTabProps {
  code: string | null;
  specId: string;
  libraryId: string;
  language?: string;
  onTrackEvent?: TrackEventFn;
}

export function CodeTab({ code, specId, libraryId, language, onTrackEvent }: CodeTabProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      onTrackEvent?.('copy_code', {
        spec: specId,
        library: libraryId,
        method: 'tab',
        page: 'spec_detail',
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Copy failed:', err);
    }
  }, [code, specId, libraryId, onTrackEvent]);

  // Lazy-loaded syntax highlighter - only loads when Code tab is opened
  const highlightedCode = code ? (
    <Suspense
      fallback={
        <Box
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: '0.85rem',
            whiteSpace: 'pre-wrap',
            overflowWrap: 'anywhere',
            overflowX: 'auto',
            minWidth: 0,
            color: semanticColors.labelText,
          }}
        >
          {code}
        </Box>
      }
    >
      <CodeHighlighter code={code} language={language} library={libraryId} />
    </Suspense>
  ) : null;

  return (
    <Box sx={{ position: 'relative', minWidth: 0 }}>
      <Tooltip title={copied ? '.copied' : '.copy()'}>
        <IconButton
          onClick={handleCopy}
          aria-label="Copy code"
          sx={{
            position: 'absolute',
            top: 12,
            right: 12,
            bgcolor: 'var(--bg-elevated)',
            border: '1px solid var(--code-border)',
            zIndex: 1,
            '&:hover': { bgcolor: 'var(--bg-surface)' },
          }}
          size="small"
        >
          {copied ? <CheckIcon color="success" /> : <ContentCopyIcon fontSize="small" />}
        </IconButton>
      </Tooltip>
      {highlightedCode}
    </Box>
  );
}
