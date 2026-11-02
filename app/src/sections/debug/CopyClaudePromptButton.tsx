import CheckIcon from '@mui/icons-material/Check';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';

import { useCopyCode } from 'src/hooks';
import { colors } from 'src/theme';
import { buildClaudePrompt } from 'src/utils/claudePrompt';

export function CopyClaudePromptButton({
  message,
  path,
  reaction,
}: {
  message: string;
  path: string | null;
  reaction: string | null;
}) {
  const { copied, copyToClipboard } = useCopyCode();
  return (
    <Tooltip title={copied ? 'copied — paste into Claude Code' : 'copy prompt for Claude Code'}>
      <IconButton
        onClick={() => copyToClipboard(buildClaudePrompt(message, path, reaction))}
        aria-label="Copy Claude Code prompt"
        size="small"
        sx={{
          alignSelf: 'start',
          color: copied ? colors.success : 'var(--ink-muted)',
          border: '1px solid var(--rule)',
          borderRadius: 1,
          '&:hover': { bgcolor: 'var(--bg-surface)', color: colors.primary },
        }}
      >
        {copied ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
      </IconButton>
    </Tooltip>
  );
}
