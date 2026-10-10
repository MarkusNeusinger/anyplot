/**
 * The chat thread: the user's turns, the assistant's replies, the fixed
 * refusal, errors with their code and request id, and a result card per plot
 * version. Earlier versions stay in the thread, collapsed, each with its own
 * image and code.
 */

import Box from '@mui/material/Box';

import { type AgentSessionState, type ChatItem, sessionBusy } from 'src/hooks/useAgentSession';
import type { ArtifactName, Theme } from 'src/lib/agent';
import { ERROR_TEXT, PLOT_FAILED_TEXT } from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { ResultCard } from 'src/sections/agent-chat/ResultCard';
import { bodyTextSx, labelSx } from 'src/sections/agent-chat/styles';
import { colors, typography } from 'src/theme';

interface ChatThreadProps {
  state: AgentSessionState;
  specId: string;
  language: string;
  onRequestTheme: (version: number, theme: Theme) => void;
  onFetchArtifact: (version: number, name: ArtifactName) => Promise<Blob>;
  onRefine: (text: string) => void;
  onTrack: (event: string, props?: Record<string, string | undefined>) => void;
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
      return (
        <Box sx={{ ...promptSx, fontFamily: typography.mono }}>
          <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', mr: 1 }}>
            ❯
          </Box>
          .create_plot()
          <Box component="span" sx={{ color: 'var(--ink-muted)', ml: 1 }}>
            # {item.library}
          </Box>
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
      return <Box sx={labelSx}># {item.text}</Box>;
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
          onRefine={props.onRefine}
          onTrack={props.onTrack}
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
  return (
    <Box
      role="log"
      aria-label="Conversation"
      sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, minWidth: 0 }}
    >
      {items.map(item => (
        <Item key={item.id} item={item} props={props} latestVersion={latestVersion} />
      ))}
    </Box>
  );
}
