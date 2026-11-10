/**
 * The agent chat's composer at the foot of the thread (`AgentChatPage.tsx`): the drop hint, the
 * data line, and one row in two fixed places, the message box with its
 * `❯` and the plot button, with the counter near the message cap below it. Below the theme's `sm`
 * (a phone) the row stacks them: the box takes the whole line, the plot button the line under it
 * at the full width, in the same order for the eye, the DOM and Tab. Nothing comes or goes
 * and nothing moves: a state only changes how the data line reads, whether the plot button is
 * filled, and which controls are inert (`aria-disabled`, so a focused one keeps the focus). What
 * the step waits for is the line's at the chat frame's foot (`StatusLine`, `ChatFrame.tsx`), the
 * plot button's description, which also holds `.stop()`, `.start_over()` and `.feedback()`.
 *
 * - The data line, one quiet line right above the box, never gone: before the first data
 *   `# no data at hand? .example_data() · .open() a file`, highlighted (the words in green, the two
 *   links underlined in green); after it, muted, `# other data? .open() · .example_data()`.
 *   `.example_data()` asks the assistant for a made-up table to try the plot, and is inert once
 *   there is data, since it would replace the data; `.open()` opens the file picker. Both are
 *   buttons styled as links, with a 44 px target at phone width.
 * - The message box: Enter sends its text as a turn, or the attachment with the text as its note;
 *   Shift+Enter is a new line. On a touch screen, whose keyboard names Enter "return", a small
 *   `↵` inside the box sends too. It has no `.send()` beside it any more. A browser cuts a long
 *   placeholder without an ellipsis, so on a phone the placeholders with data are short ones
 *   (`PHONE_PLACEHOLDER`): "ask or say what to plot", "ask a question or a change".
 * - The plot button, filled from the moment data is stored or waits in the box, quiet and inert
 *   before, two lines, its name over a quiet line on what one click does (`PLOT_BUTTON`):
 *   `.create_plot() →` (confirms the data and the bindings as shown, then plots, with the
 *   box's text as the request), `.update_plot() →` once the library has a plot (sends the box's
 *   text, inert while the box is empty), `plot the new data` after a change to data the user had
 *   confirmed (acts with an empty box), `.plot_all()` while the admin's fan-out is on. A switch
 *   keeps its name.
 *
 * A table pasted into the box, or a file opened with `.open()` or dropped on the chat, waits
 * above the text as an attachment (`AttachmentChip`, `useChatAttachment.ts`): Enter reads it with
 * the typed text as its note; the plot button reads it the same way and plots it in one click
 * once it reads clean (`plotChain.ts`), and names the plot it makes: `.create_plot() →`, or
 * `plot the new data` once the library has a plot.
 *
 * The page decides what each button does and when it acts; this component only lays them out.
 */

import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';

import type { Failure } from 'src/hooks/useAgentSession';
import { MAX_MESSAGE_CHARS } from 'src/lib/agent';
import { AttachmentChip } from 'src/sections/agent-chat/AttachmentChip';
import { attachmentLabel } from 'src/sections/agent-chat/attachmentText';
import { FILE_ACCEPT } from 'src/sections/agent-chat/fileText';
import {
  ATTACHMENT_PLACEHOLDER,
  describeDataFailure,
  ERROR_TEXT,
  NEW_DATA_HELP,
  NEW_DATA_PLOT,
  NO_DATA_PLACEHOLDER,
  PHONE_PLACEHOLDER,
  START_OVER_HELP,
} from 'src/sections/agent-chat/messages';
import { type PlotButtonKind, STATUS_LINE_ID } from 'src/sections/agent-chat/steps';
import {
  bodyTextSx,
  composerFilledSx,
  composerGhostSx,
  labelSx,
  messageBoxSx,
  PHONE_QUERY,
  smallText,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import type { Attachment } from 'src/sections/agent-chat/useChatAttachment';
import { colors, fontSize, typography } from 'src/theme';

/**
 * The plot button's words, the quiet line under them and its accessible name, per kind. The arrow
 * says that the click sends the box's text along; `.plot_all()` opens the fan-out's panel instead.
 * The line under the name says what one click does: `.update_plot() →` sends the box's text as
 * Enter does, so it answers a question and changes the data as well as the plot, which its name
 * alone does not say. Every kind has a line, so the button is one height in every state.
 */
const PLOT_BUTTON: Record<PlotButtonKind, { text: string; hint: string; name: string }> = {
  create: { text: '.create_plot() →', hint: 'confirm data · plot it', name: 'Create plot' },
  update: { text: '.update_plot() →', hint: 'ask · edit data · change plot', name: 'Update plot' },
  new_data: { text: NEW_DATA_PLOT, hint: 'confirm data · plot it', name: 'Plot the new data' },
  all: { text: '.plot_all()', hint: 'one plot per library', name: 'Plot in all libraries' },
};

/** The hidden help the plot button names when its click starts from the catalogue plot. */
const PLOT_HELP_ID = 'agent-plot-help';

/**
 * A link of the data line: a button in the line's small mono, with a 44 px target at phone width
 * and the site's focus ring. Highlighted, its words are ink with a brand-green underline; muted,
 * soft ink without one. Green as a line, never as small text: the hover turns the words into the
 * green that reads 4.5:1 in each theme (`--code-comment`).
 */
function dataLinkSx(highlighted: boolean) {
  return {
    fontFamily: typography.mono,
    fontSize: smallText,
    fontWeight: 500,
    color: highlighted ? 'var(--ink)' : 'var(--ink-soft)',
    bgcolor: 'transparent',
    border: 'none',
    borderRadius: '4px',
    px: 0.5,
    py: 0,
    minHeight: { xs: 44, sm: 28 },
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    textDecoration: highlighted ? 'underline' : 'none',
    textDecorationColor: colors.primary,
    textUnderlineOffset: '3px',
    '&:hover:not([aria-disabled="true"])': {
      color: 'var(--code-comment)',
      textDecoration: 'underline',
      textDecorationColor: colors.primary,
    },
    '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
    '&[aria-disabled="true"]': { opacity: 0.45, cursor: 'default', textDecoration: 'none' },
  } as const;
}

/** The muted words between the data line's links; hidden at phone width when `wide` is set. */
function LineWords({ children, wide = false }: { children: React.ReactNode; wide?: boolean }) {
  return (
    <Box
      component="span"
      sx={{ color: 'var(--ink-muted)', display: wide ? { xs: 'none', sm: 'inline' } : 'inline' }}
    >
      {children}
    </Box>
  );
}

/** The plot button as the page decides it. */
export interface PlotButtonState {
  kind: PlotButtonKind;
  /** The click acts now; else the button is inert and keeps its place and the focus. */
  active: boolean;
  /** The confirmation the click starts with is in flight: the button says it works on it. */
  confirming: boolean;
  /**
   * The click may start from the catalogue plot although the library has one (the data or the
   * bindings changed since): the button names what that keeps as part of its description, and
   * `plot the new data` also when it changes the latest plot instead (`NEW_DATA_HELP`).
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
  /** The box's text is a table that Enter sends as data (`plotChain.boxData`), not a message. */
  typedData?: boolean;
  plot: PlotButtonState;
  /** `.example_data()` in the data line: whether its click acts now. */
  example: { active: boolean };
  /** Why the confirmation a plot click starts with was refused; it shows under the composer. */
  confirmError: Failure | null;
  onExampleData: () => void;
  onPlot: (event: React.MouseEvent) => void;
}

export function Composer(props: ComposerProps) {
  const { draft, onDraftChange, onPaste, onSubmit, messageRef, plotRef } = props;
  const { attachment, attachmentNotice, onRemoveAttachment, dropHint } = props;
  const { canOpen, fileInputRef, onFileChosen } = props;
  const { ready, busy, hasData, step2, hasPlot, chatLocked, plot, example, typedData } = props;
  const { confirmError, onExampleData, onPlot } = props;
  // Read at the first render, so a phone never shows the long placeholder first.
  const narrow = useMediaQuery(PHONE_QUERY, { noSsr: true });
  // While `all` holds the box in step 2, the line at the frame's foot says why, and the box names
  // it as its description; an attachment, new data, goes all the same, with Enter in the box,
  // which it opens for that.
  const lockedBox = chatLocked && !attachment;
  // An attachment goes once it is read and the dataset route can take it; a refused one again.
  const sendable = !attachment || attachment.status === 'ready' || attachment.status === 'failed';
  // A message over the cap is never cut: the counter turns red and nothing sends until it fits. A
  // table in the box is data, which goes by the dataset's own limits (`typedData`), so no cap holds it.
  const tooLong = draft.length > MAX_MESSAGE_CHARS && !typedData;
  // What Enter and the `↵` send now: text or an attachment, while nothing else runs.
  const canSend =
    ready && !busy && sendable && !tooLong && (!!draft.trim() || !!attachment) && !lockedBox;

  const plotWords = PLOT_BUTTON[plot.kind];
  // The confirmation the click starts with: the button says it works on it.
  const plotText = plot.confirming ? `${plotWords.text} …` : plotWords.text;

  return (
    <>
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
      {/* The data line: the two ways to data besides a paste, highlighted until the first data
          arrives, muted after, never gone. `.example_data()` holds the same slot in both forms,
          so a focus on it survives the change; the `.open()` before or after it is a slot of its
          own. At phone width the line drops "at hand" and "a file". */}
      <Box
        data-testid="data-line"
        data-highlighted={!hasData || undefined}
        sx={{
          ...labelSx,
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          columnGap: 0.5,
          mb: -1,
        }}
      >
        <Box component="span" sx={{ color: hasData ? 'var(--ink-muted)' : 'var(--code-comment)' }}>
          {hasData ? (
            '# other data?'
          ) : (
            <>
              # no data<LineWords wide> at hand</LineWords>?
            </>
          )}
        </Box>
        {hasData && (
          <Box
            component="button"
            type="button"
            onClick={() => {
              if (canOpen) fileInputRef.current?.click();
            }}
            aria-disabled={!canOpen || undefined}
            aria-label="Open a data file"
            sx={dataLinkSx(false)}
          >
            .open()
          </Box>
        )}
        {hasData && <LineWords>·</LineWords>}
        <Box
          component="button"
          type="button"
          onClick={() => {
            if (example.active) onExampleData();
          }}
          aria-disabled={!example.active || undefined}
          aria-label="Make example data"
          sx={dataLinkSx(!hasData)}
        >
          .example_data()
        </Box>
        {!hasData && <LineWords>·</LineWords>}
        {!hasData && (
          <Box
            component="button"
            type="button"
            onClick={() => {
              if (canOpen) fileInputRef.current?.click();
            }}
            aria-disabled={!canOpen || undefined}
            aria-label="Open a data file"
            sx={dataLinkSx(true)}
          >
            .open()
          </Box>
        )}
        {!hasData && <LineWords wide>a file</LineWords>}
      </Box>
      {/* One row: the box and the plot button side by side from `sm` up, where a row too narrow
          for both wraps the plot button to a line of its own at the right end. Below `sm` the box
          takes the whole line and the plot button the next one at the full width, so the box's
          placeholder reads on a phone; the order is the same, box first. */}
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
              // otherwise holds the box: the fan-out takes no text. On a phone, where the browser
              // cuts it without an ellipsis, the placeholder with data is a short one.
              attachment
                ? ATTACHMENT_PLACEHOLDER
                : chatLocked
                  ? 'all libraries: the table goes as it is · turn all off to chat'
                  : !hasData
                    ? NO_DATA_PLACEHOLDER
                    : narrow
                      ? hasPlot
                        ? PHONE_PLACEHOLDER.change
                        : PHONE_PLACEHOLDER.first
                      : !step2
                        ? `ask about your data, or say what the ${hasPlot ? 'next' : 'first'} plot should do`
                        : !hasPlot
                          ? 'optional: what the first plot should do differently'
                          : 'ask a question or a change, e.g. log scale on y'
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
              // The box grows with its text up to a few lines, where the browser can. Empty, it
              // stays one line; a placeholder too long for it is cut, with an ellipsis where the
              // browser draws one (a desktop browser), without one on a phone, hence its short
              // placeholders there.
              fieldSizing: 'content',
              maxHeight: '12rem',
              '&:placeholder-shown': { fieldSizing: 'fixed' },
              '&::placeholder': {
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              },
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
        {/* The step's action from the moment data is stored or waits in the box, quiet and inert
            before. A plain button: Enter in the box sends a turn and never confirms. */}
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
            ...(hasData || attachment || plot.active ? composerFilledSx : composerGhostSx),
            display: 'inline-flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            rowGap: '2px',
            // From `sm` up as wide as its longest line (the 29 characters of `update`'s hint in
            // the small size, 27 of the button's own), so a new name moves nothing beside it;
            // below `sm` a line of its own at the full width, in the same size, since it no
            // longer shares the line with the box.
            minWidth: 'calc(27ch + 26px)',
            flex: { xs: '1 1 100%', sm: 'none' },
            ml: 'auto',
          }}
        >
          <Box component="span" data-plot-label>
            {plotText}
          </Box>
          {/* What one click does. The accessible name stays the short one, and the box's
              placeholder says the same to a screen reader, so the line is for the eye only. */}
          <Box
            component="span"
            aria-hidden
            data-testid="plot-hint"
            sx={{
              fontSize: smallText,
              fontWeight: 400,
              color: 'color-mix(in srgb, currentColor 78%, transparent)',
            }}
          >
            {plotWords.hint}
          </Box>
        </Box>
      </Box>
      {plot.fresh && (
        <Box component="span" id={PLOT_HELP_ID} sx={visuallyHiddenSx}>
          {/* `plot the new data` may change the latest plot instead (`plot_new_data`). */}
          {plot.kind === 'new_data' ? NEW_DATA_HELP : START_OVER_HELP}
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
      {draft.length > MAX_MESSAGE_CHARS * 0.9 && !typedData && (
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
