/**
 * The agent chat's composer at the foot of the thread (`AgentChatPage.tsx`): the service's pause
 * note, the drop hint, and one row in four fixed places, the message box with its `❯`, `.open()`,
 * `.example_data()` and the plot button, with the counter near the message cap below it. Nothing
 * in the row comes or goes and nothing moves: a state only changes which button is filled and
 * which are inert (`aria-disabled`, so a focused button keeps the focus). What the step waits for
 * is the line's at the chat frame's foot (`StatusLine`, `ChatFrame.tsx`), the plot button's
 * description, which also holds `.stop()`, `.start_over()` and `.feedback()`.
 *
 * - The message box: Enter sends its text as a turn, or the attachment with the text as its note;
 *   Shift+Enter is a new line. On a touch screen, whose keyboard names Enter "return", a small
 *   `↵` inside the box sends too. It has no `.send()` beside it any more.
 * - `.example_data()`: the filled button while the session has no data, which asks the assistant
 *   for a made-up table to try the plot; quiet and inert once there is data.
 * - The plot button, filled from the moment data is stored, quiet and inert before: `.create_plot()
 *   →` (confirms the data and the bindings as shown, then plots, with the box's text as the
 *   request), `.update_plot() →` once the library has a plot (sends the box's text, inert while
 *   the box is empty), `plot the new data` after a change to data the user had confirmed (acts
 *   with an empty box), `.plot_all()` while the admin's fan-out is on. A switch keeps its name.
 *
 * A table pasted into the box, or a file opened with `.open()` or dropped on the chat, waits
 * above the text as an attachment (`AttachmentChip`, `useChatAttachment.ts`): Enter reads it with
 * the typed text as its note, and the plot button waits until it is read, since it would plot
 * the data before it.
 *
 * The page decides what each button does and when it acts; this component only lays them out.
 */

import Box from '@mui/material/Box';

import type { Failure } from 'src/hooks/useAgentSession';
import { MAX_MESSAGE_CHARS } from 'src/lib/agent';
import { AttachmentChip } from 'src/sections/agent-chat/AttachmentChip';
import { attachmentLabel } from 'src/sections/agent-chat/attachmentText';
import { FILE_ACCEPT } from 'src/sections/agent-chat/fileText';
import {
  ATTACHMENT_PLACEHOLDER,
  describeDataFailure,
  ERROR_TEXT,
  NEW_DATA_PLOT,
  NO_DATA_PLACEHOLDER,
  servicePausedText,
  START_OVER_HELP,
} from 'src/sections/agent-chat/messages';
import { type PlotButtonKind, STATUS_LINE_ID } from 'src/sections/agent-chat/steps';
import {
  bodyTextSx,
  composerFilledSx,
  composerGhostSx,
  composerQuietSx,
  labelSx,
  messageBoxSx,
  smallText,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import type { Attachment } from 'src/sections/agent-chat/useChatAttachment';
import { colors, fontSize, typography } from 'src/theme';

/**
 * The plot button's words and its accessible name, per kind. The arrow says that the click sends
 * the box's text along; `.plot_all()` opens the fan-out's panel instead.
 */
const PLOT_BUTTON: Record<PlotButtonKind, { text: string; name: string }> = {
  create: { text: '.create_plot() →', name: 'Create plot' },
  update: { text: '.update_plot() →', name: 'Update plot' },
  new_data: { text: NEW_DATA_PLOT, name: 'Plot the new data' },
  all: { text: '.plot_all()', name: 'Plot in all libraries' },
};

/** The hidden help the plot button names when its click starts from the catalogue plot. */
const PLOT_HELP_ID = 'agent-plot-help';

/** The row's buttons, one size in every state: smaller at phone width, where the row wraps. */
const ROW_BUTTON_SIZE = {
  fontSize: { xs: smallText, sm: fontSize.md },
  px: { xs: 1, sm: 1.5 },
} as const;

/** The plot button as the page decides it. */
export interface PlotButtonState {
  kind: PlotButtonKind;
  /** The click acts now; else the button is inert and keeps its place and the focus. */
  active: boolean;
  /** The confirmation the click starts with is in flight: the button says it works on it. */
  confirming: boolean;
  /**
   * The click starts from the catalogue plot although the library has one (the data or the
   * bindings changed since): the button names what that keeps as part of its description.
   */
  fresh: boolean;
}

export interface ComposerProps {
  draft: string;
  /** The box's input: the page keeps the text, or routes a paste the browser inserted itself. */
  onDraftChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  /** The box's paste: a table becomes the attachment, other text is the box's. */
  onPaste: (event: React.ClipboardEvent<HTMLTextAreaElement>) => void;
  /** The table or file waiting in the box for Enter, or null. */
  attachment: Attachment | null;
  /** Why a file was not attached (a running step, a format not read here): an alert. */
  attachmentNotice: string | null;
  onRemoveAttachment: () => void;
  /** While a file is dragged over the chat: whether it would be taken, or why not. */
  dropHint: { ready: boolean; text: string } | null;
  /** `.open()`: a file is taken now (no step running, no file read on the server). */
  canOpen: boolean;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  onFileChosen: (event: React.ChangeEvent<HTMLInputElement>) => void;
  /** The form's submit, Enter in the box and the `↵`: the page's `handleSend`, a turn. */
  onSubmit: (event?: React.FormEvent) => void;
  messageRef: React.RefObject<HTMLTextAreaElement | null>;
  /** The plot button, where the keyboard returns after the fan-out's panel. */
  plotRef: React.RefObject<HTMLButtonElement | null>;
  /** The session is open and answers. */
  ready: boolean;
  busy: boolean;
  /** The session holds data. */
  hasData: boolean;
  step2: boolean;
  hasPlot: boolean;
  /** `all` holds the box in step 2: the fan-out takes no text. */
  chatLocked: boolean;
  plot: PlotButtonState;
  /** `.example_data()`: filled before there is data, and whether its click acts now. */
  example: { filled: boolean; active: boolean };
  /** Why the confirmation a plot click starts with was refused; it shows under the composer. */
  confirmError: Failure | null;
  /** Until when (ISO) the service paused, for the note above the box. */
  pausedUntil: string | null;
  onExampleData: () => void;
  onPlot: (event: React.MouseEvent) => void;
}

export function Composer(props: ComposerProps) {
  const { draft, onDraftChange, onPaste, onSubmit, messageRef, plotRef } = props;
  const { attachment, attachmentNotice, onRemoveAttachment, dropHint } = props;
  const { canOpen, fileInputRef, onFileChosen } = props;
  const { ready, busy, hasData, step2, hasPlot, chatLocked, plot, example } = props;
  const { confirmError, pausedUntil, onExampleData, onPlot } = props;
  // While `all` holds the box in step 2, the line at the frame's foot says why, and the box names
  // it as its description; an attachment, new data, goes all the same, with Enter in the box,
  // which it opens for that.
  const lockedBox = chatLocked && !attachment;
  // An attachment goes once it is read and the dataset route can take it; a refused one again.
  const sendable = !attachment || attachment.status === 'ready' || attachment.status === 'failed';
  // A message over the cap is never cut: the counter turns red and nothing sends until it fits.
  const tooLong = draft.length > MAX_MESSAGE_CHARS;
  // What Enter and the `↵` send now: text or an attachment, while nothing else runs.
  const canSend =
    ready && !busy && sendable && !tooLong && (!!draft.trim() || !!attachment) && !lockedBox;

  const plotWords = PLOT_BUTTON[plot.kind];
  // The confirmation the click starts with: the button says it works on it.
  const plotText = plot.confirming ? `${plotWords.text} …` : plotWords.text;

  return (
    <>
      {/* Told before the user types: every turn would get `service_paused` until then. */}
      {pausedUntil && (
        <Box
          role="note"
          data-testid="service-paused"
          sx={{
            ...labelSx,
            color: 'var(--ink)',
            borderLeft: `3px solid ${colors.warning}`,
            pl: 1.5,
            lineHeight: 1.6,
          }}
        >
          # {servicePausedText(pausedUntil)}
        </Box>
      )}
      {/* A file dragged over the chat: whether a drop attaches it, or why it waits. */}
      {dropHint && (
        <Box
          aria-hidden
          data-testid="drop-hint"
          data-drag={dropHint.ready ? 'ready' : 'busy'}
          sx={{
            ...labelSx,
            fontSize: fontSize.md,
            color: 'var(--ink)',
            border: `1px dashed ${dropHint.ready ? colors.primary : colors.warning}`,
            borderRadius: '4px',
            bgcolor: `color-mix(in srgb, ${dropHint.ready ? colors.primary : colors.warning} 10%, var(--bg-elevated))`,
            px: 1.5,
            py: 1,
            textAlign: 'center',
          }}
        >
          {dropHint.text}
        </Box>
      )}
      {/* One row on a wide screen. At phone width the box takes the first line, `.open()` and
          `.example_data()` the next, and the plot button a line of its own at the right end:
          the three need about 390 px, a phone's frame about 330. Every state wraps the same. */}
      <Box
        component="form"
        data-testid="composer-row"
        onSubmit={onSubmit}
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          columnGap: 1,
          rowGap: 1,
        }}
      >
        {attachment && <AttachmentChip attachment={attachment} onRemove={onRemoveAttachment} />}
        {/* The terminal prompt before the box, beside it as the line at the foot has `>>>`. */}
        <Box
          component="span"
          aria-hidden
          sx={{
            display: { xs: 'none', sm: 'block' },
            fontFamily: typography.mono,
            fontSize: fontSize.md,
            color: colors.primary,
          }}
        >
          ❯
        </Box>
        <Box
          sx={{
            position: 'relative',
            display: 'flex',
            flex: { xs: '1 1 100%', sm: '1 1 240px' },
            minWidth: 0,
          }}
        >
          <Box
            component="textarea"
            ref={messageRef}
            aria-label="Message"
            placeholder={
              // Without data, the chat is the other way to get some: example data or a formula.
              // With data, step 1 talks about the data and what the plot should do, step 2 about
              // the plot; short since 2026-11-02, the how-to is behind the header's ⓘ. With an
              // attachment the text is its note, also while `all` is pressed in step 2, which
              // otherwise holds the box: the fan-out takes no text.
              attachment
                ? ATTACHMENT_PLACEHOLDER
                : chatLocked
                  ? 'all libraries: the table goes as it is · turn all off to chat'
                  : !hasData
                    ? NO_DATA_PLACEHOLDER
                    : !step2
                      ? `ask about your data, or say what the ${hasPlot ? 'next' : 'first'} plot should do`
                      : !hasPlot
                        ? 'optional: what the first plot should do differently'
                        : 'ask for a change, e.g. log scale on y'
            }
            value={draft}
            rows={1}
            // An attachment, new data, goes while `all` holds the box: Enter in the box sends it.
            disabled={!ready || lockedBox}
            aria-invalid={tooLong || undefined}
            aria-describedby={lockedBox ? STATUS_LINE_ID : undefined}
            onChange={onDraftChange}
            onPaste={onPaste}
            onKeyDown={(event: React.KeyboardEvent<HTMLTextAreaElement>) => {
              // Enter (also with Ctrl or ⌘) sends text as a turn, or the attachment with the text
              // as its note; Shift+Enter is a new line, and an empty box sends nothing by
              // accident. An input method's composition takes Enter for itself.
              if (event.key !== 'Enter' || event.shiftKey || event.nativeEvent.isComposing) return;
              event.preventDefault();
              if ((draft.trim() || attachment) && !tooLong) onSubmit();
            }}
            sx={{
              ...messageBoxSx,
              flex: 1,
              resize: 'vertical',
              // The box grows with its text up to a few lines, where the browser can.
              fieldSizing: 'content',
              maxHeight: '12rem',
              // Room for the `↵` at the box's right end, where the resize grip would sit under it.
              '@media (pointer: coarse)': { pr: '48px', resize: 'none' },
            }}
          />
          {/* A touch keyboard names Enter "return" and may read it as a new line: the `↵` says
              where sending is. A pointer and a keyboard have Enter, so it shows on touch only. */}
          <Box
            component="button"
            type="button"
            data-testid="send-return"
            onClick={() => {
              if (canSend) onSubmit();
            }}
            aria-disabled={!canSend || undefined}
            aria-label="Send"
            sx={{
              display: 'none',
              '@media (pointer: coarse)': { display: 'inline-flex' },
              position: 'absolute',
              right: 0,
              bottom: 0,
              width: 44,
              height: 44,
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: typography.mono,
              fontSize: fontSize.md,
              color: 'var(--ink)',
              bgcolor: 'transparent',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: -2 },
              '&[aria-disabled="true"]': { opacity: 0.45, cursor: 'default' },
            }}
          >
            ↵
          </Box>
        </Box>
        <Box
          component="input"
          type="file"
          ref={fileInputRef}
          accept={FILE_ACCEPT}
          onChange={onFileChosen}
          tabIndex={-1}
          aria-hidden
          data-testid="chat-file-input"
          sx={{ display: 'none' }}
        />
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            columnGap: 1,
            rowGap: 1,
            flex: { xs: '1 1 100%', sm: '0 1 auto' },
            // Below the box when the row wraps, at its right end; at phone width the plot button
            // wraps once more, to a line of its own.
            ml: 'auto',
            minWidth: 0,
          }}
        >
          {/* `.open()`: a file for the attachment, the keyboard's and the phone's way in (iOS has
              no drag and drop into a page). */}
          <Box
            component="button"
            type="button"
            onClick={() => {
              if (canOpen) fileInputRef.current?.click();
            }}
            aria-disabled={!canOpen || undefined}
            aria-label="Attach a data file"
            sx={{ ...composerGhostSx, ...ROW_BUTTON_SIZE }}
          >
            .open()
          </Box>
          {/* Filled while there is no data, the step's action then; quiet and inert after. */}
          <Box
            component="button"
            type="button"
            onClick={() => {
              if (example.active) onExampleData();
            }}
            aria-disabled={!example.active || undefined}
            aria-label="Make example data"
            sx={{ ...(example.filled ? composerFilledSx : composerQuietSx), ...ROW_BUTTON_SIZE }}
          >
            .example_data()
          </Box>
          {/* The step's action from the moment data is stored, quiet and inert before. A plain
              button: Enter in the box sends a turn and never confirms. */}
          <Box
            component="button"
            type="button"
            ref={plotRef}
            data-plot={plot.kind}
            onClick={(event: React.MouseEvent) => {
              if (plot.active) onPlot(event);
            }}
            aria-disabled={!plot.active || undefined}
            aria-label={plotWords.name}
            aria-describedby={plot.fresh ? `${STATUS_LINE_ID} ${PLOT_HELP_ID}` : STATUS_LINE_ID}
            sx={{
              ...(hasData ? composerFilledSx : composerQuietSx),
              ...ROW_BUTTON_SIZE,
              // As wide as its longest name (`plot the new data`, mono), so a new name moves
              // nothing beside it.
              minWidth: { xs: 'calc(17ch + 18px)', sm: 'calc(17ch + 26px)' },
              ml: 'auto',
            }}
          >
            {plotText}
          </Box>
        </Box>
      </Box>
      {plot.fresh && (
        <Box component="span" id={PLOT_HELP_ID} sx={visuallyHiddenSx}>
          {START_OVER_HELP}
        </Box>
      )}
      {confirmError && !step2 && (
        <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: -1 }}>
          {describeDataFailure(confirmError.code, confirmError.ref)}
        </Box>
      )}
      {attachmentNotice && (
        <Box
          role="alert"
          data-testid="attachment-notice"
          sx={{ ...bodyTextSx, color: colors.error, mt: -1, overflowWrap: 'anywhere' }}
        >
          {attachmentNotice}
        </Box>
      )}
      {/* Stays mounted, so a screen reader hears what came into the box, and once that the text
          ran over the cap: the line changes only when one of them does. */}
      <Box data-testid="composer-status" aria-live="polite" sx={visuallyHiddenSx}>
        {[attachment ? attachmentLabel(attachment) : null, tooLong ? ERROR_TEXT.too_long : null]
          .filter(Boolean)
          .join('. ')}
      </Box>
      {draft.length > MAX_MESSAGE_CHARS * 0.9 && (
        <Box
          data-testid="message-counter"
          sx={{ ...labelSx, mt: -1, color: tooLong ? colors.error : 'var(--ink-muted)' }}
        >
          {draft.length.toLocaleString('en-US')} / {MAX_MESSAGE_CHARS.toLocaleString('en-US')}
        </Box>
      )}
    </>
  );
}
