/**
 * The agent chat's composer at the foot of the thread (`AgentChatPage.tsx`): the line that names
 * the step's action, the service's pause note, `.example_data()` while the session has no data,
 * the message box and its buttons, and the counter near the message cap.
 *
 * The step's one filled call to action sits at the composer's right end: `.confirm()` in step 1
 * once there is data, which confirms the data and its bindings, with the line above the box
 * that names what it waits for as its description; `.create_plot()` in step 2 before this
 * library's first plot. Once the library has a plot, `.start_over()` beside `.send()` is a quiet
 * button, as is the plot after a switch (its carry) beside it, and with `all` pressed
 * `.plot_all()` takes the create button's place. The plot buttons exist only in step 2, so no
 * click asks for something the data card has not settled yet; the server's `data_unconfirmed`
 * stays the backstop. `.stop()` replaces them while a run is in progress, as a button of its own
 * key, so the one a run replaces never turns into `.stop()` in place, with a focus that a second
 * key press would spend on stopping.
 *
 * The page decides what each button does and when it waits; this component only lays them out.
 */

import Box from '@mui/material/Box';

import type { Failure } from 'src/hooks/useAgentSession';
import { MAX_MESSAGE_CHARS } from 'src/lib/agent';
import { ExampleDataLine } from 'src/sections/agent-chat/ExampleData';
import { describeDataFailure, servicePausedText } from 'src/sections/agent-chat/messages';
import { DATA_SUMMARY_ID } from 'src/sections/agent-chat/steps';
import {
  actionButtonSx,
  bodyTextSx,
  ctaButtonSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { colors } from 'src/theme';

/**
 * What `.start_over()` does, unlike `.send()` beside it (the owner could not tell the two apart),
 * and the quiet `.create_plot()` beside the offer after a switch: the catalogue code again, with the
 * remembered decisions, which only the user clears (owner decision of 2026-11-02).
 */
const START_OVER_HELP = 'new from the catalogue plot; keeps your remembered decisions';
const START_OVER_HELP_ID = 'agent-start-over-help';

/** Step 1's line above the box, `.confirm()`'s description. */
const STEP_LINE_ID = 'agent-step-line';

/** Step 1 with data: what `.confirm()` at the composer's end needs. */
export interface ComposerConfirm {
  /** The line above the box: what the confirmation waits for, or what to check (`confirmStepLine`). */
  line: string;
  enabled: boolean;
  /** The confirmation call is in flight. */
  busy: boolean;
  error: Failure | null;
  onConfirm: () => void;
}

export interface ComposerProps {
  draft: string;
  onDraftChange: (text: string) => void;
  /** The form's submit, also Enter in the box: the page's `handleSend`. */
  onSubmit: (event?: React.FormEvent) => void;
  messageRef: React.RefObject<HTMLTextAreaElement | null>;
  /** Step 2's action button, where the keyboard continues after `.confirm()`. */
  createRef: React.RefObject<HTMLButtonElement | null>;
  /** The session is open and answers. */
  ready: boolean;
  busy: boolean;
  running: boolean;
  stopping: boolean;
  step2: boolean;
  firstPlot: boolean;
  hasPlot: boolean;
  canCreate: boolean;
  plotAll: boolean;
  chatLocked: boolean;
  /** The libraries `.plot_all()` plots in, for the line that names them. */
  libraryCount: number;
  /** The fan-out's panel is open: `.plot_all()` waits. */
  fanOutOpen: boolean;
  /** The carry after a switch, as the button names it; null without an offer. */
  carryText: string | null;
  /** Step 1 with data: `.confirm()` and its line; null without data and in step 2. */
  confirm: ComposerConfirm | null;
  /** Until when (ISO) the service paused, for the note above the box. */
  pausedUntil: string | null;
  exampleOffer: boolean;
  exampleWorking: boolean;
  onExampleData: (event: React.MouseEvent) => void;
  onStop: (event: React.MouseEvent) => void;
  onCreate: (event: React.MouseEvent) => void;
  onCarry: (event: React.MouseEvent) => void;
  onPlotAll: (event: React.MouseEvent) => void;
  /** A key press on a button a run replaces continues in the message box. */
  keepKeyboardFocus: (event: React.MouseEvent) => void;
}

export function Composer(props: ComposerProps) {
  const { draft, onDraftChange, onSubmit, messageRef, createRef } = props;
  const { ready, busy, running, stopping, step2, firstPlot, hasPlot } = props;
  const { canCreate, plotAll, chatLocked, libraryCount, fanOutOpen, carryText, confirm } = props;
  const { pausedUntil, exampleOffer, exampleWorking, onExampleData } = props;
  const { onStop, onCreate, onCarry, onPlotAll, keepKeyboardFocus } = props;
  const carry = carryText !== null;

  // `.send()`: a turn about the data or the plot; before the library's first plot in step 2 the
  // CTA submits the text instead.
  const sendButton = (
    <Box
      key="send"
      component="button"
      type="submit"
      onClick={keepKeyboardFocus}
      disabled={chatLocked || !draft.trim() || !ready || busy}
      aria-describedby={chatLocked ? 'agent-create-line' : undefined}
      sx={ghostButtonSx}
    >
      .send()
    </Box>
  );

  // Step 1's action: a plain button, so Enter in the box still sends the text. It stays in its
  // place while a turn runs (the summary after a parse), waiting beside `.stop()`, so the next
  // step is in view the whole time.
  const confirmButton = confirm && (
    <Box
      key="confirm"
      component="button"
      type="button"
      onClick={confirm.onConfirm}
      disabled={!confirm.enabled}
      aria-describedby={STEP_LINE_ID}
      sx={ctaButtonSx}
    >
      {confirm.busy ? '.confirm() …' : '.confirm()'}
    </Box>
  );

  // Step 2's create action while `all` is pressed, for every library at once: the CTA before
  // the first plot, the quiet button otherwise. It waits while the panel is open.
  const plotAllButton = (
    <Box
      key="plot-all"
      component="button"
      type="button"
      ref={createRef}
      onClick={onPlotAll}
      disabled={fanOutOpen || !canCreate}
      aria-label="Plot in all libraries"
      aria-describedby={[DATA_SUMMARY_ID, chatLocked ? 'agent-create-line' : null]
        .filter(Boolean)
        .join(' ')}
      sx={firstPlot ? ctaButtonSx : actionButtonSx}
    >
      .plot_all()
    </Box>
  );

  return (
    <>
      {/* Step 1: what `.confirm()` waits for, or what to check; the button names it as its
          description. */}
      {confirm && (
        <Box
          id={STEP_LINE_ID}
          data-testid="data-step"
          sx={{ ...labelSx, color: 'var(--ink-soft)', mb: -1 }}
        >
          {confirm.line}
        </Box>
      )}
      {/* While the chat waits for `all`, the line says so in the ink of the text, and the
          message box names it as its description. */}
      {(firstPlot || chatLocked) && (
        <Box
          id="agent-create-line"
          sx={{ ...labelSx, color: chatLocked ? 'var(--ink)' : 'var(--ink-soft)', mb: -1 }}
        >
          {chatLocked
            ? `# ${firstPlot ? 'step 2 — ' : ''}plot the table as it is in all ${libraryCount} libraries at once · turn all off to chat`
            : carry
              ? `# step 2 — ${carryText}, or say first what it should do differently`
              : '# step 2 — create the plot as it is, or say first what it should do differently'}
        </Box>
      )}
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
      {/* A key press continues in the message box: the button gives way to the working
          line while the turn runs. */}
      {exampleOffer && (
        <ExampleDataLine working={exampleWorking} disabled={busy} onClick={onExampleData} />
      )}
      <Box
        component="form"
        onSubmit={onSubmit}
        sx={{ display: 'flex', gap: 1, alignItems: 'flex-end', flexWrap: 'wrap' }}
      >
        <Box
          component="textarea"
          ref={messageRef}
          aria-label="Message"
          placeholder={
            // Step 1 talks about the data, step 2 about the plot; short since
            // 2026-11-02, the how-to is behind the data card's ⓘ. Without data,
            // the chat is the other way to get some: example data or a formula.
            // While `all` is pressed in step 2 the box waits: the fan-out takes
            // no text.
            chatLocked
              ? 'all libraries: the table goes as it is · turn all off to chat'
              : !step2
                ? 'ask for example data, a curve, or a fix to your data'
                : firstPlot
                  ? 'optional: what the first plot should do differently'
                  : 'ask for a change, e.g. log scale on y'
          }
          value={draft}
          maxLength={MAX_MESSAGE_CHARS}
          rows={2}
          disabled={!ready || chatLocked}
          aria-describedby={chatLocked ? 'agent-create-line' : undefined}
          onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
            onDraftChange(event.target.value)
          }
          onKeyDown={(event: React.KeyboardEvent<HTMLTextAreaElement>) => {
            // Enter sends text; an empty box creates nothing by accident.
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              if (draft.trim()) onSubmit();
            }
          }}
          sx={{ ...nativeControlSx, flex: '1 1 240px', resize: 'vertical' }}
        />
        {/* Own keys: the button a run replaces never turns into `.stop()` in place,
            with a focus that a second key press would spend on stopping the run. */}
        {running ? (
          <>
            <Box
              key="stop"
              component="button"
              type="button"
              onClick={onStop}
              disabled={stopping}
              aria-label="Stop"
              sx={{
                ...ghostButtonSx,
                color: colors.error,
                '&:hover:not(:disabled)': { color: colors.error, borderColor: colors.error },
              }}
            >
              {stopping ? '.stop() …' : '.stop()'}
            </Box>
            {confirmButton}
          </>
        ) : !step2 ? (
          <>
            {sendButton}
            {confirmButton}
          </>
        ) : firstPlot && plotAll ? (
          plotAllButton
        ) : firstPlot && !carry ? (
          <Box
            key="create"
            component="button"
            type="submit"
            ref={createRef}
            onClick={keepKeyboardFocus}
            disabled={!canCreate}
            aria-label="Create plot"
            aria-describedby={`${DATA_SUMMARY_ID} agent-create-line`}
            sx={ctaButtonSx}
          >
            .create_plot()
          </Box>
        ) : (
          <>
            {/* After a switch that offered it: the plot in this library with the remembered
                decisions, the step's action. Before the library's first plot it submits
                the form, so typed text goes as the turn, as `.create_plot()` does. */}
            {carry && (
              <Box
                key="carry"
                component="button"
                type={firstPlot ? 'submit' : 'button'}
                ref={createRef}
                data-testid="carry-plot"
                onClick={firstPlot ? keepKeyboardFocus : onCarry}
                disabled={!canCreate}
                aria-describedby={`${DATA_SUMMARY_ID}${firstPlot ? ' agent-create-line' : ''}`}
                // The library's name and the count make it long: it wraps at phone width.
                sx={{ ...ctaButtonSx, whiteSpace: 'normal', textAlign: 'left', maxWidth: '100%' }}
              >
                {carryText}
              </Box>
            )}
            {/* After a plot: start over from the catalogue plot with this data. Beside the
                offer: the plot from the catalogue code, without the carry. With `all`,
                `.plot_all()`. */}
            {plotAll && plotAllButton}
            {!plotAll && (
              <Box
                key="create-quiet"
                component="button"
                type="button"
                ref={carry ? undefined : createRef}
                onClick={onCreate}
                disabled={!canCreate}
                // Once this library has a plot, the button starts over from the
                // catalogue plot; `.send()` beside it changes the latest version.
                aria-label={hasPlot ? 'Start over' : 'Create plot'}
                title={hasPlot || carry ? START_OVER_HELP : undefined}
                aria-describedby={[hasPlot || carry ? START_OVER_HELP_ID : null, DATA_SUMMARY_ID]
                  .filter(Boolean)
                  .join(' ')}
                sx={actionButtonSx}
              >
                {hasPlot ? '.start_over()' : '.create_plot()'}
              </Box>
            )}
            {(hasPlot || carry) && !plotAll && (
              <Box component="span" id={START_OVER_HELP_ID} sx={visuallyHiddenSx}>
                {START_OVER_HELP}
              </Box>
            )}
            {/* Before the library's first plot the offer submits text; no `.send()` then. */}
            {!firstPlot && sendButton}
          </>
        )}
      </Box>
      {confirm?.error && (
        <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: -1 }}>
          {describeDataFailure(confirm.error.code, confirm.error.ref)}
        </Box>
      )}
      {draft.length > MAX_MESSAGE_CHARS * 0.9 && (
        <Box sx={{ ...labelSx, mt: -1 }}>
          {draft.length} / {MAX_MESSAGE_CHARS}
        </Box>
      )}
    </>
  );
}
