/**
 * The thread's one language line: the offer of a language the server found in the user's
 * message or data, `# German detected in your message · .switch()`, with what the button sets,
 * that everything stays as it is until then and the menu at the top behind its ⓘ. Ignored, it
 * changes nothing. `.switch()` sets the replies and the plot labels to the language
 * (`acceptLanguage`, `PUT .../language` with `via: offer`); the same line then reads `#
 * replies and plot labels: Deutsch`, with `· the next plot version uses it` when a plot was on
 * screen, since the click starts no run. A pick elsewhere (the chip, a request in the chat,
 * another offer taken) closes an open line: its button goes and its words stay.
 *
 * At phone width the line wraps and `.switch()` stands on its own line below the words, a 44 px
 * target; from `sm` up it follows them inline at 32 px (`statusActionSx`). Like the chip, the
 * button is `aria-disabled` during its own call, so the keyboard focus stays on it; once the
 * line names the language, the focus moves to the line, since the button is gone. While
 * anything else is in flight it is disabled, as the server would refuse with `409 run_active`.
 */

import { useEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';

import type { ChatItem } from 'src/hooks/useAgentSession';
import { AgentApiError } from 'src/lib/agent';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import {
  describeLanguageFailure,
  languageAcceptedLine,
  languageOfferLine,
  languageSwitchLabel,
} from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { labelSx, readableSx, smallText, statusActionSx } from 'src/sections/agent-chat/styles';
import { colors, typography } from 'src/theme';

type OfferItem = Extract<ChatItem, { kind: 'language_offer' }>;

export interface LanguageOfferLineProps {
  item: OfferItem;
  /** The session language, which everything stays in until the user takes the offer. */
  current: string;
  /** Something else is in flight: the server would refuse the pick. */
  busy: boolean;
  /** Take the offer; rejects with an `AgentApiError` on failure. Without it the line has no button. */
  onAccept?: (offerId: number) => Promise<void>;
}

export function LanguageOfferLine({ item, current, busy, onAccept }: LanguageOfferLineProps) {
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<{ code: string; ref: string | null } | null>(null);
  const lineRef = useRef<HTMLDivElement>(null);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  // The button goes once the line names the language: the focus it held (now on the page's body)
  // moves to the line, and only then, so a line accepted while the user typed elsewhere takes none.
  const accepted = item.state === 'accepted';
  const pressed = useRef(false);
  useEffect(() => {
    if (accepted && pressed.current && document.activeElement === document.body) {
      lineRef.current?.focus();
    }
  }, [accepted]);

  if (accepted) {
    return (
      <Box
        ref={lineRef}
        tabIndex={-1}
        data-testid="language-offer"
        sx={{ ...labelSx, ...readableSx, lineHeight: 1.6, outline: 'none' }}
      >
        # {languageAcceptedLine(item.language, item.plot ?? false)}
      </Box>
    );
  }

  const offer = languageOfferLine(item.language, item.basis, current);
  const open = item.state === 'open' && !!onAccept;
  const accept = async () => {
    if (!onAccept || pending) return;
    pressed.current = true;
    setPending(true);
    setFailure(null);
    try {
      await onAccept(item.id);
    } catch (err) {
      if (mounted.current) {
        setFailure(
          err instanceof AgentApiError
            ? { code: err.code, ref: err.shownRef }
            : { code: 'network', ref: null }
        );
      }
    } finally {
      if (mounted.current) setPending(false);
    }
  };

  return (
    <Box
      ref={lineRef}
      tabIndex={-1}
      data-testid="language-offer"
      sx={{ ...readableSx, outline: 'none' }}
    >
      <Box
        sx={{
          ...labelSx,
          lineHeight: 1.6,
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          columnGap: 0.5,
        }}
      >
        <Box component="span">
          # {offer.text}
          <InfoPopover
            label={offer.info.label}
            heading={offer.info.heading}
            lines={offer.info.lines}
          />
        </Box>
        {open && (
          <Box
            component="span"
            sx={{ display: 'flex', alignItems: 'center', width: { xs: '100%', sm: 'auto' } }}
          >
            <Box component="span" aria-hidden sx={{ display: { xs: 'none', sm: 'inline' } }}>
              ·
            </Box>
            <Box
              component="button"
              type="button"
              onClick={() => void accept()}
              disabled={busy && !pending}
              aria-disabled={pending || undefined}
              aria-label={languageSwitchLabel(item.language)}
              sx={{ ...statusActionSx, ml: { xs: -1.25, sm: 0 } }}
            >
              .switch(){pending ? ' …' : ''}
            </Box>
          </Box>
        )}
      </Box>
      {failure && (
        <Box
          role="alert"
          sx={{
            fontFamily: typography.mono,
            fontSize: smallText,
            color: colors.error,
            overflowWrap: 'anywhere',
            mt: 0.5,
          }}
        >
          {describeLanguageFailure(failure.code, failure.ref)}
          <ReloadHint code={failure.code} />
        </Box>
      )}
    </Box>
  );
}
