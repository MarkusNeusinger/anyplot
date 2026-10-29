import React from 'react';

import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { FEEDBACK_STATUS_OPTIONS, FeedbackMessageFilter } from 'src/sections/debug/constants';
import { CopyClaudePromptButton } from 'src/sections/debug/CopyClaudePromptButton';
import { FeedbackTopList, FeedbackTopPage } from 'src/sections/debug/FeedbackTopList';
import { timeAgo } from 'src/sections/debug/format';
import { debugControlSx } from 'src/sections/debug/styles';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

export interface FeedbackMessage {
  contact: string | null;
  id: string;
  reaction: string | null;
  message: string | null;
  path: string | null;
  status: string;
  created_at: string;
}

export function FeedbackSection({
  topThumbsUp,
  topThumbsDown,
  feedbackStatusFilter,
  setFeedbackStatusFilter,
  feedbackMessages,
  handleStatusChange,
}: {
  topThumbsUp: FeedbackTopPage[];
  topThumbsDown: FeedbackTopPage[];
  feedbackStatusFilter: FeedbackMessageFilter;
  setFeedbackStatusFilter: (val: FeedbackMessageFilter) => void;
  feedbackMessages: FeedbackMessage[];
  handleStatusChange: (id: string, newStatus: string) => void;
}) {
  return (
    <>
      {/* Feedback: top pages + messages with triage (issue #5662) */}
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>feedback · top pages</em>} />
      </Box>
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.xs,
          color: semanticColors.mutedText,
          mb: 1,
        }}
      >
        grouped by URL — clickable
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
          sx={{ ...debugControlSx, cursor: 'pointer', ml: 'auto' }}
        >
          <option value="open">open (new + in progress)</option>
          <option value="">all statuses</option>
          {FEEDBACK_STATUS_OPTIONS.map(s => (
            <option key={s} value={s}>
              {s.replace('_', ' ')}
            </option>
          ))}
        </Box>
      </Box>
      {feedbackMessages.length === 0 ? (
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xs,
            color: semanticColors.mutedText,
            py: 2,
          }}
        >
          no messages{feedbackStatusFilter ? ` with status "${feedbackStatusFilter}"` : ''}
        </Typography>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 4 }}>
          {feedbackMessages.map(m => (
            <Box
              key={m.id}
              sx={{
                border: '1px solid var(--rule)',
                borderRadius: 1,
                p: 1.5,
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', sm: 'auto 1fr auto' },
                columnGap: 1.5,
                rowGap: 0.5,
                alignItems: 'start',
                bgcolor: m.status === 'new' ? 'var(--bg-surface)' : 'transparent',
              }}
            >
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25, minWidth: 90 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box component="span" sx={{ fontSize: 14 }}>
                    {m.reaction === 'thumbs_up'
                      ? '👍'
                      : m.reaction === 'thumbs_down'
                        ? '👎'
                        : m.reaction === 'idea'
                          ? '💡'
                          : m.reaction === 'bug'
                            ? '🪲'
                            : '—'}
                  </Box>
                  <Typography
                    sx={{
                      fontFamily: typography.fontFamily,
                      fontSize: fontSize.xxs,
                      color: semanticColors.mutedText,
                    }}
                  >
                    {timeAgo(m.created_at)}
                  </Typography>
                </Box>
                {m.path && (
                  <Link
                    component={RouterLink}
                    to={m.path}
                    sx={{
                      fontFamily: typography.fontFamily,
                      fontSize: fontSize.xxs,
                      color: colors.primary,
                      textDecoration: 'none',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      '&:hover': { textDecoration: 'underline' },
                    }}
                  >
                    {m.path}
                  </Link>
                )}
              </Box>
              <Box sx={{ minWidth: 0 }}>
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: fontSize.xs,
                    color: 'var(--ink)',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {m.message}
                </Typography>
                {m.contact && (
                  <Typography
                    sx={{
                      fontFamily: typography.fontFamily,
                      fontSize: fontSize.xxs,
                      color: semanticColors.mutedText,
                      mt: 0.5,
                    }}
                  >
                    contact: {m.contact}
                  </Typography>
                )}
              </Box>
              <Box sx={{ display: 'flex', gap: 0.75, alignItems: 'start' }}>
                {m.message && (
                  <CopyClaudePromptButton message={m.message} path={m.path} reaction={m.reaction} />
                )}
                <Box
                  component="select"
                  value={m.status}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                    handleStatusChange(
                      m.id,
                      e.target.value as import('src/sections/debug/constants').FeedbackStatus
                    )
                  }
                  sx={{ ...debugControlSx, cursor: 'pointer', alignSelf: 'start' }}
                >
                  {FEEDBACK_STATUS_OPTIONS.map(s => (
                    <option key={s} value={s}>
                      {s.replace('_', ' ')}
                    </option>
                  ))}
                </Box>
              </Box>
            </Box>
          ))}
        </Box>
      )}
    </>
  );
}
