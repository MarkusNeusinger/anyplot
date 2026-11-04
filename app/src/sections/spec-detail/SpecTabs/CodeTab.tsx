import { lazy, Suspense, useCallback, useState } from 'react';

import CheckIcon from '@mui/icons-material/Check';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';

import { UseMyDataAction } from 'src/sections/spec-detail/LibraryPills';
import type { TrackEventFn } from 'src/sections/spec-detail/SpecTabs/utils';
import { semanticColors, typography } from 'src/theme';

const CodeHighlighter = lazy(() => import('src/components/CodeHighlighter'));

interface CodeTabProps {
  code: string | null;
  specId: string;
  libraryId: string;
  language?: string;
  onTrackEvent?: TrackEventFn;
  /** The agent chat's entry beside `.copy()`: present only for an eligible pair. */
  onUseWithMyData?: () => void;
}

export function CodeTab({
  code,
  specId,
  libraryId,
  language,
  onTrackEvent,
  onUseWithMyData,
}: CodeTabProps) {
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
      {/* The header's actions sit over the code's first line, the short `anyplot.ai` header
          comment, each on the elevated surface so the code never shows through. Below 600 px
          the chat's entry and the copy button together would cover that line: they stand in a
          row above the code instead. */}
      <Box
        sx={{
          position: onUseWithMyData ? { xs: 'static', sm: 'absolute' } : 'absolute',
          top: 12,
          right: 12,
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          gap: 1,
          mb: onUseWithMyData ? { xs: 1, sm: 0 } : 0,
        }}
      >
        {onUseWithMyData && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              height: 32,
              px: 1,
              bgcolor: 'var(--bg-elevated)',
              border: '1px solid var(--code-border)',
              borderRadius: '16px',
            }}
          >
            <UseMyDataAction onActivate={onUseWithMyData} />
          </Box>
        )}
        <Tooltip title={copied ? '.copied' : '.copy()'}>
          <IconButton
            onClick={handleCopy}
            aria-label="Copy code"
            sx={{
              bgcolor: 'var(--bg-elevated)',
              border: '1px solid var(--code-border)',
              '&:hover': { bgcolor: 'var(--bg-surface)' },
            }}
            size="small"
          >
            {copied ? <CheckIcon color="success" /> : <ContentCopyIcon fontSize="small" />}
          </IconButton>
        </Tooltip>
      </Box>
      {highlightedCode}
    </Box>
  );
}
