/**
 * The attachment in the chat's message box (`useChatAttachment.ts`): one line with the table's
 * or the file's name, its size and ×, while it waits for Enter. While a file is read on the
 * server or the data is parsed, the line says so beside the site's loader; a table too large for
 * the dataset route, or one the route refused, turns the chip red with the reason under it, as
 * an alert. A screen reader hears the chip as a group named after what it holds.
 */

import Box from '@mui/material/Box';

import { LoaderSpinner } from 'src/components/LoaderSpinner';
import { attachmentLabel, attachmentLine } from 'src/sections/agent-chat/attachmentText';
import { ATTACHMENT_OVER_CAP_TEXT } from 'src/sections/agent-chat/messages';
import { actionButtonSx, bodyTextSx, labelSx, smallText } from 'src/sections/agent-chat/styles';
import type { Attachment } from 'src/sections/agent-chat/useChatAttachment';
import { colors } from 'src/theme';

export function AttachmentChip({
  attachment,
  onRemove,
}: {
  attachment: Attachment;
  onRemove: () => void;
}) {
  const { status } = attachment;
  const red = status === 'over_cap' || status === 'failed';
  const working = status === 'reading' || status === 'sending';
  const problem = status === 'over_cap' ? ATTACHMENT_OVER_CAP_TEXT : attachment.error;
  return (
    <Box sx={{ flex: '1 1 100%', minWidth: 0 }}>
      <Box
        role="group"
        aria-label={attachmentLabel(attachment)}
        data-testid="attachment"
        data-status={status}
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 1,
          maxWidth: '100%',
          border: `1px solid ${red ? colors.error : 'var(--rule)'}`,
          borderRadius: '4px',
          bgcolor: 'var(--bg-elevated)',
          pl: 1,
        }}
      >
        <Box
          component="span"
          sx={{
            ...labelSx,
            fontSize: smallText,
            color: red ? colors.error : 'var(--ink)',
            overflowWrap: 'anywhere',
            py: 0.5,
          }}
        >
          {attachmentLine(attachment)}
        </Box>
        {working && <LoaderSpinner size="inline" />}
        <Box
          component="button"
          type="button"
          onClick={onRemove}
          // A posted table is the parse's now: it goes once its answer is in.
          disabled={status === 'sending'}
          aria-label="Remove the attachment"
          sx={{ ...actionButtonSx, px: 1, minHeight: 28 }}
        >
          ×
        </Box>
      </Box>
      {attachment.notes.length > 0 && !working && (
        <Box sx={{ ...labelSx, mt: 0.5, overflowWrap: 'anywhere' }}>
          # {attachment.notes.join(' · ')}
        </Box>
      )}
      {red && problem && (
        <Box
          role="alert"
          data-testid="attachment-error"
          sx={{ ...bodyTextSx, color: colors.error, mt: 0.5, overflowWrap: 'anywhere' }}
        >
          {problem}
        </Box>
      )}
    </Box>
  );
}
