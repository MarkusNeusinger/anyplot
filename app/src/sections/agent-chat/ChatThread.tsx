/**
 * The chat thread: the user's turns and the page's own (`.summarize_data()`
 * after a parse, `.create_plot()`, `.carry_plot()`), the assistant's replies, the fixed
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
import { type ArtifactName, isPlotAction, type Theme } from 'src/lib/agent';
import { Ellipsis } from 'src/sections/agent-chat/Ellipsis';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import { ERROR_TEXT, localClock, PLOT_FAILED_TEXT } from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { type CardOutcome, ResultCard } from 'src/sections/agent-chat/ResultCard';
import { type PendingReply, pendingReply } from 'src/sections/agent-chat/steps';
import {
  bodyTextSx,
  CHAT_TEXT_MAX,
  labelSx,
  readableSx as textSx,
} from 'src/sections/agent-chat/styles';
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
  onFetchArtifact: (version: number, name: ArtifactName, theme?: Theme) => Promise<Blob>;
  onTrack: (event: string, props?: Record<string, string | undefined>) => void;
  /** The result cards' usage beacon (`ResultCard`'s `onOutcome`). */
  onOutcome?: (action: CardOutcome, version: number) => void;
  /** The result cards' quick feedback; without it they show no control. */
  onSendFeedback?: (version: number, input: FeedbackInput) => Promise<void>;
}

/**
 * The user's turns, on the right; like every text item of the thread (`textSx`), no wider than
 * a readable line since the column grows up to 1360 px (2026-11-02). The result cards take the
 * full width.
 */
const promptSx = {
  ...bodyTextSx,
  alignSelf: 'flex-end',
  maxWidth: { xs: '100%', sm: `min(85%, ${CHAT_TEXT_MAX})` },
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
      // The page's own turns: `.summarize_data()` after a parse, `.create_plot()` in step 2,
      // `.carry_plot()` after a library switch; a plot names the library it is made in.
      return (
        <Box sx={{ ...promptSx, fontFamily: typography.mono }}>
          <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', mr: 1 }}>
            ❯
          </Box>
          .{item.action}()
          {isPlotAction(item.action) && (
            <Box component="span" sx={{ color: 'var(--ink-muted)', ml: 1 }}>
              # {item.library}
            </Box>
          )}
        </Box>
      );
    case 'assistant':
      return (
        <Box sx={{ ...bodyTextSx, ...textSx, borderLeft: '2px solid var(--rule)', pl: 1.5 }}>
          {item.text}
        </Box>
      );
    case 'refusal':
      return (
        <Box
          sx={{ ...textSx, borderLeft: `2px solid ${colors.warning}`, pl: 1.5 }}
          data-testid="refusal"
        >
          <Box sx={labelSx}>
            refusal · {item.code}
            {/* The service's own text says 00:00 UTC: the page adds the user's own time. */}
            {item.until && localClock(item.until) ? ` · until ${localClock(item.until)}` : ''}
          </Box>
          <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>{item.text}</Box>
        </Box>
      );
    case 'error':
      return (
        <Box role="alert" sx={{ ...textSx, borderLeft: `2px solid ${colors.error}`, pl: 1.5 }}>
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
            ...textSx,
            color: 'var(--ink)',
            borderLeft: `3px solid ${colors.warning}`,
            pl: 1.5,
          }}
        >
          # {item.text}
        </Box>
      ) : (
        // A quiet line; its details, where it has any, behind the ⓘ at its end.
        <Box sx={{ ...labelSx, ...textSx, lineHeight: 1.6 }}>
          # {item.text}
          {item.info && (
            <InfoPopover
              label={item.info.label}
              heading={item.info.heading}
              lines={item.info.lines}
            />
          )}
        </Box>
      );
    case 'plot_failed':
      return (
        <Box sx={{ ...textSx, borderLeft: `2px solid ${colors.error}`, pl: 1.5 }}>
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
          onOutcome={props.onOutcome}
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
            ...textSx,
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
