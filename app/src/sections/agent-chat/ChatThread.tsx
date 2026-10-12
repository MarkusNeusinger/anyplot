/**
 * The chat thread: the user's turns and the page's own (`.summarize_data()`
 * after a parse, `.create_plot()`), the assistant's replies, the fixed
 * refusal, errors with their code and request id, and a result card per plot
 * version. Earlier versions stay in the thread, collapsed, each with its own
 * image and code. A lost confirmation shows as a warning notice where it was
 * lost. While a turn without pipeline steps waits for its reply, an
 * in-progress line holds the assistant's slot (`pendingReply` in `steps.ts`);
 * the log's own polite live region announces it once, and the reply takes its
 * place.
 */

import Box from '@mui/material/Box';

import {
  type AgentSessionState,
  type ChatItem,
  type FeedbackInput,
  sessionBusy,
} from 'src/hooks/useAgentSession';
import type { ArtifactName, Theme } from 'src/lib/agent';
import { Ellipsis } from 'src/sections/agent-chat/Ellipsis';
import { ERROR_TEXT, PLOT_FAILED_TEXT } from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { ResultCard } from 'src/sections/agent-chat/ResultCard';
import { type PendingReply, pendingReply } from 'src/sections/agent-chat/steps';
import { bodyTextSx, labelSx } from 'src/sections/agent-chat/styles';
import { colors, typography } from 'src/theme';

/** The in-progress line's words; the pulsing `…` follows them. */
const PENDING_TEXT: Record<PendingReply, string> = {
  summarize_data: 'summarizing your data',
  message: 'working on your message',
  stopping: 'stopping',
};

interface ChatThreadProps {
  state: AgentSessionState;
  specId: string;
  language: string;
  onRequestTheme: (version: number, theme: Theme) => void;
  onFetchArtifact: (version: number, name: ArtifactName) => Promise<Blob>;
  onTrack: (event: string, props?: Record<string, string | undefined>) => void;
  /** The result cards' quick feedback; without it they show no control. */
  onSendFeedback?: (version: number, input: FeedbackInput) => Promise<void>;
}

const promptSx = {
  ...bodyTextSx,
  alignSelf: 'flex-end',
  maxWidth: { xs: '100%', sm: '85%' },
  bgcolor: 'var(--bg-elevated)',
  border: '1px solid var(--rule)',
  borderRadius: 2,
  px: 1.5,
  py: 1,
} as const;

function Item({
  item,
  props,
  latestVersion,
}: {
  item: ChatItem;
  props: ChatThreadProps;
  latestVersion: number;
}) {
  switch (item.kind) {
    case 'user':
      return (
        <Box sx={promptSx}>
          <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', mr: 1 }}>
            ❯
          </Box>
          {item.text}
        </Box>
      );
    case 'action':
      // The page's own turns: `.summarize_data()` after a parse, `.create_plot()` in step 2.
      return (
        <Box sx={{ ...promptSx, fontFamily: typography.mono }}>
          <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', mr: 1 }}>
            ❯
          </Box>
          .{item.action}()
          {item.action === 'create_plot' && (
            <Box component="span" sx={{ color: 'var(--ink-muted)', ml: 1 }}>
              # {item.library}
            </Box>
          )}
        </Box>
      );
    case 'assistant':
      return (
        <Box sx={{ ...bodyTextSx, borderLeft: '2px solid var(--rule)', pl: 1.5 }}>{item.text}</Box>
      );
    case 'refusal':
      return (
        <Box sx={{ borderLeft: `2px solid ${colors.warning}`, pl: 1.5 }} data-testid="refusal">
          <Box sx={labelSx}>refusal · {item.code}</Box>
          <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>{item.text}</Box>
        </Box>
      );
    case 'error':
      return (
        <Box role="alert" sx={{ borderLeft: `2px solid ${colors.error}`, pl: 1.5 }}>
          <Box sx={{ ...labelSx, color: colors.error }}>
            error · {item.code}
            {item.ref ? ` · ref ${item.ref}` : ''}
          </Box>
          <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
            {ERROR_TEXT[item.code] ?? 'the request failed'}
            <ReloadHint code={item.code} />
          </Box>
        </Box>
      );
    case 'notice':
      // A lost confirmation reads as the result card's residual notes do: a warning border.
      return item.tone === 'warning' ? (
        <Box
          data-testid="confirm-lost"
          sx={{
            ...labelSx,
            color: 'var(--ink)',
            borderLeft: `3px solid ${colors.warning}`,
            pl: 1.5,
          }}
        >
          # {item.text}
        </Box>
      ) : (
        <Box sx={labelSx}># {item.text}</Box>
      );
    case 'plot_failed':
      return (
        <Box sx={{ borderLeft: `2px solid ${colors.error}`, pl: 1.5 }}>
          <Box sx={{ ...labelSx, color: colors.error }}>
            plot · {item.result.status === 'not_ready' ? 'not ready' : 'failed'}
            {item.result.reason ? ` · ${item.result.reason}` : ''}
          </Box>
          <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
            {PLOT_FAILED_TEXT[item.result.reason ?? ''] ?? 'no plot this time'}
          </Box>
        </Box>
      );
    case 'plot': {
      const version = props.state.versions[item.version];
      if (!version) return null;
      return (
        <ResultCard
          version={version}
          specId={props.specId}
          language={props.language}
          latest={version.number === latestVersion}
          busy={sessionBusy(props.state)}
          onRequestTheme={props.onRequestTheme}
          onFetchArtifact={props.onFetchArtifact}
          onTrack={props.onTrack}
          onSendFeedback={props.onSendFeedback}
        />
      );
    }
    default:
      return null;
  }
}

export function ChatThread(props: ChatThreadProps) {
  const { items, versions } = props.state;
  const numbers = Object.keys(versions).map(Number);
  const latestVersion = numbers.length ? Math.max(...numbers) : 0;
  const pending = pendingReply(props.state);
  return (
    <Box
      role="log"
      aria-label="Conversation"
      sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, minWidth: 0 }}
    >
      {items.map(item => (
        <Item key={item.id} item={item} props={props} latestVersion={latestVersion} />
      ))}
      {/* The assistant's slot, in its style, in softer ink: provisional until the reply. */}
      {pending && (
        <Box
          data-testid="pending-reply"
          sx={{
            ...bodyTextSx,
            color: 'var(--ink-soft)',
            borderLeft: '2px solid var(--rule)',
            pl: 1.5,
          }}
        >
          {PENDING_TEXT[pending]} <Ellipsis />
        </Box>
      )}
    </Box>
  );
}
