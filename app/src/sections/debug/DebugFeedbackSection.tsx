import { Link as RouterLink } from 'react-router-dom';

import CheckIcon from '@mui/icons-material/Check';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { useCopyCode } from 'src/hooks';
import { timeAgo } from 'src/sections/debug/format';
import { colors, fontSize, semanticColors, typography } from 'src/theme';
import { buildClaudePrompt } from 'src/utils/claudePrompt';

import {
  FeedbackMessageFilter,
  FeedbackMessageItem,
  FeedbackStatus,
  FeedbackTopPage,
} from './useDebugFeedback';

interface DebugFeedbackSectionProps {
  topThumbsUp: FeedbackTopPage[];
  topThumbsDown: FeedbackTopPage[];
  feedbackMessages: FeedbackMessageItem[];
  feedbackStatusFilter: FeedbackMessageFilter;
  setFeedbackStatusFilter: (val: FeedbackMessageFilter) => void;
  updateFeedbackStatus: (id: string, newStatus: FeedbackStatus) => void;
}

function FeedbackTopList({
  title,
  items,
  accent,
}: {
  title: string;
  items: FeedbackTopPage[];
  accent: string;
}) {
  return (
    <Box sx={{ border: '1px solid var(--rule)', borderRadius: 1, p: 1.5 }}>
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.xs,
          fontWeight: 600,
          color: 'var(--ink-soft)',
          mb: 1,
        }}
      >
        {title}
      </Typography>
      {items.length === 0 ? (
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xxs,
            color: semanticColors.mutedText,
          }}
        >
          no entries yet
        </Typography>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
          {items.map(it => (
            <Box
              key={it.path}
              sx={{
                display: 'grid',
                gridTemplateColumns: '32px 1fr auto',
                gap: 1,
                alignItems: 'baseline',
                py: 0.4,
                borderBottom: '1px solid var(--rule)',
                '&:last-of-type': { borderBottom: 'none' },
              }}
            >
              <Typography
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xxs,
                  color: accent,
                  fontWeight: 600,
                  textAlign: 'right',
                }}
              >
                {it.count}
              </Typography>
              <Link
                component={RouterLink}
                to={it.path}
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xs,
                  color: colors.primary,
                  textDecoration: 'none',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  '&:hover': { textDecoration: 'underline' },
                }}
              >
                {it.path}
              </Link>
              <Typography
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.micro,
                  color: semanticColors.mutedText,
                }}
              >
                {it.last_seen ? timeAgo(it.last_seen) : ''}
              </Typography>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}

function CopyClaudePromptButton({
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

export function DebugFeedbackSection({
  topThumbsUp,
  topThumbsDown,
  feedbackMessages,
  feedbackStatusFilter,
  setFeedbackStatusFilter,
  updateFeedbackStatus,
}: DebugFeedbackSectionProps) {
  return (
    <>
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>feedback · top pages</em>} />
      </Box>
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.xs,
          color: semanticColors.mutedText,
          mb: 2,
        }}
      >
        pages with the most reaction clicks in the last 7 days
      </Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
        <FeedbackTopList title="👍 thumbs up" items={topThumbsUp} accent={colors.success} />
        <FeedbackTopList title="👎 thumbs down" items={topThumbsDown} accent={colors.error} />
      </Box>

      <Box sx={{ mt: 4, display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        <SectionHeader prompt="❯" title={<em>feedback · messages</em>} />
        <Box
          component="select"
          value={feedbackStatusFilter}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
            setFeedbackStatusFilter(e.target.value as FeedbackMessageFilter)
          }
          sx={{
            ml: 'auto',
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xs,
            p: 0.5,
            border: '1px solid var(--rule)',
            borderRadius: 1,
            bgcolor: 'var(--bg-surface)',
            color: 'var(--ink)',
            outline: 'none',
          }}
        >
          <option value="">all statuses</option>
          <option value="open">open (new + in progress)</option>
          <option value="new">new</option>
          <option value="in_progress">in progress</option>
          <option value="done">done</option>
          <option value="wont_solve">won't solve</option>
        </Box>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 2 }}>
        {feedbackMessages.length === 0 ? (
          <Typography
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: fontSize.sm,
              color: semanticColors.mutedText,
              textAlign: 'center',
              py: 4,
            }}
          >
            no messages found.
          </Typography>
        ) : (
          feedbackMessages.map(msg => (
            <Box
              key={msg.id}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 1,
                p: 1.5,
                border: '1px solid var(--rule)',
                borderRadius: 1,
                bgcolor:
                  msg.status === 'done' || msg.status === 'wont_solve'
                    ? 'var(--bg-surface)'
                    : 'transparent',
                opacity: msg.status === 'done' || msg.status === 'wont_solve' ? 0.7 : 1,
              }}
            >
              <Box sx={{ display: 'flex', gap: 1.5 }}>
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.sm,
                    color: 'var(--ink)',
                    flex: 1,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  "{msg.message}"
                </Typography>
                <CopyClaudePromptButton
                  message={msg.message}
                  path={msg.path}
                  reaction={msg.reaction}
                />
              </Box>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  flexWrap: 'wrap',
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xs,
                  color: semanticColors.mutedText,
                }}
              >
                <Box
                  component="span"
                  sx={{
                    color:
                      msg.reaction === 'thumbs_up'
                        ? colors.success
                        : msg.reaction === 'thumbs_down'
                          ? colors.error
                          : 'inherit',
                  }}
                >
                  {msg.reaction === 'thumbs_up'
                    ? '👍'
                    : msg.reaction === 'thumbs_down'
                      ? '👎'
                      : '💬'}
                </Box>
                {msg.path && (
                  <Link
                    component={RouterLink}
                    to={msg.path}
                    sx={{ color: colors.primary, textDecoration: 'none' }}
                  >
                    {msg.path}
                  </Link>
                )}
                <Box component="span">·</Box>
                <Box component="span" title={msg.timestamp}>
                  {timeAgo(msg.timestamp)}
                </Box>
                <Box component="span">·</Box>
                <Box
                  component="span"
                  sx={{ fontFamily: 'monospace', fontSize: fontSize.micro, opacity: 0.5 }}
                >
                  {msg.session_id?.slice(0, 8) || ''}
                </Box>
                <Box
                  component="select"
                  value={msg.status}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                    updateFeedbackStatus(msg.id, e.target.value as FeedbackStatus)
                  }
                  sx={{
                    ml: 'auto',
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    p: '2px 4px',
                    border: '1px solid var(--rule)',
                    borderRadius: 1,
                    bgcolor: 'transparent',
                    color:
                      msg.status === 'done'
                        ? colors.success
                        : msg.status === 'in_progress'
                          ? colors.primary
                          : 'var(--ink-soft)',
                    outline: 'none',
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'var(--bg-surface)' },
                  }}
                >
                  <option value="new">new</option>
                  <option value="in_progress">in progress</option>
                  <option value="done">done</option>
                  <option value="wont_solve">won't solve</option>
                </Box>
              </Box>
            </Box>
          ))
        )}
      </Box>
    </>
  );
}
