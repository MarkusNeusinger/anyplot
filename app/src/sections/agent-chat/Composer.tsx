/**
 * The agent chat's composer at the foot of the thread (`AgentChatPage.tsx`): the line that names
 * the step's action, the service's pause note, `.example_data()` while the session has no data,
 * the message box and its buttons, and the counter near the message cap.
 *
 * The step's one filled call to action sits at the composer's right end from the moment data is
 * stored: `.create_plot()` (with `all` pressed `.plot_all()`, after a switch's offer the carry),
 * while the data is unconfirmed, also when this library already has a plot (the click makes a
 * new version from the data as the card shows it), and while the data is confirmed and the
 * library has no plot yet. Its click takes the data and the bindings as shown, confirms them
 * first when they are not (the page chains it), and starts the plot, with the box's text as its
 * request; the line above the box, its description, says what it waits for. Once the confirmed
 * data has a plot in this library, `.start_over()` is a quiet button beside the offer, if any.
 * `.send()` shows only while the box holds text: Enter sends a turn too, and a disabled outline
 * beside the CTA read as "blocked until something". `.stop()` stands beside the CTA while a run
 * is in progress, a button of its own key, so no button turns into `.stop()` in place with a
 * focus that a second key press would spend on stopping.
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
 * the quiet `.create_plot()` beside the offer after a switch, and `.create_plot()` on changed data
 * when the library has a plot: the catalogue code again, with the remembered decisions, which
 * only the user clears (owner decision of 2026-11-02).
 */
const START_OVER_HELP = 'new from the catalogue plot; keeps your remembered decisions';
const START_OVER_HELP_ID = 'agent-start-over-help';

/** Step 1's line above the box, the plot button's description. */
const STEP_LINE_ID = 'agent-step-line';
/** Step 2's line above the box before the library's first plot, or while `all` holds the box. */
const CREATE_LINE_ID = 'agent-create-line';

export interface ComposerProps {
  draft: string;
  onDraftChange: (text: string) => void;
  /** The form's submit, Enter in the box and `.send()`: the page's `handleSend`, a turn. */
  onSubmit: (event?: React.FormEvent) => void;
  messageRef: React.RefObject<HTMLTextAreaElement | null>;
  /** The step's action button, where the keyboard returns after the fan-out's panel. */
  createRef: React.RefObject<HTMLButtonElement | null>;
  /** The session is open and answers. */
  ready: boolean;
  busy: boolean;
  running: boolean;
  stopping: boolean;
  /** The session holds data. */
  hasData: boolean;
  step2: boolean;
  hasPlot: boolean;
  /** The filled CTA is a plot button: data stored, unconfirmed or without a plot in this library. */
  ctaPlot: boolean;
  canCreate: boolean;
  plotAll: boolean;
  chatLocked: boolean;
  /** The libraries `.plot_all()` plots in, for the line that names them. */
  libraryCount: number;
  /** The fan-out's panel is open: `.plot_all()` waits. */
  fanOutOpen: boolean;
  /** The carry after a switch, as the button names it; null without an offer. */
  carryText: string | null;
  /** Step 1's line above the box (`stepOneLine`); null without data and in step 2. */
  stepLine: string | null;
  /** The confirmation a plot button starts with is in flight. */
  confirming: boolean;
  /** Why that confirmation was refused; it shows under the composer. */
  confirmError: Failure | null;
  /** Until when (ISO) the service paused, for the note above the box. */
  pausedUntil: string | null;
  exampleOffer: boolean;
  exampleWorking: boolean;
  onExampleData: (event: React.MouseEvent) => void;
  onStop: (event: React.MouseEvent) => void;
  /** The filled `.create_plot()`: the plot, with the box's text as its request. */
  onPlot: (event: React.MouseEvent) => void;
  /** The quiet `.create_plot()` or `.start_over()`: the catalogue plot again, text left in the box. */
  onCreate: (event: React.MouseEvent) => void;
  onCarry: (event: React.MouseEvent) => void;
  onPlotAll: (event: React.MouseEvent) => void;
  /** A key press on a button a run replaces continues in the message box. */
  keepKeyboardFocus: (event: React.MouseEvent) => void;
}

export function Composer(props: ComposerProps) {
  const { draft, onDraftChange, onSubmit, messageRef, createRef } = props;
  const { ready, busy, running, stopping, hasData, step2, hasPlot, ctaPlot, canCreate } = props;
  const { plotAll, chatLocked, libraryCount, fanOutOpen, carryText, stepLine } = props;
  const { confirming, confirmError, pausedUntil, exampleOffer, exampleWorking } = props;
  const { onExampleData, onStop, onPlot, onCreate, onCarry, onPlotAll, keepKeyboardFocus } = props;
  const carry = carryText !== null;
  // Step 2 before this library's first plot: the line above the box says what the CTA does.
  const firstPlot = step2 && !hasPlot;
  const createLine = firstPlot || chatLocked;
  // The confirmation the click starts with: the button says it works on it.
  const working = (label: string) => (confirming ? `${label} …` : label);

  // What the filled CTA names as its description: step 1's line, else the pinned header's summary
  // and step 2's line; on changed data with a plot, also what a new version is made from.
  const ctaDescription = [
    stepLine ? STEP_LINE_ID : DATA_SUMMARY_ID,
    createLine ? CREATE_LINE_ID : null,
    ctaPlot && hasPlot && !carry && !plotAll ? START_OVER_HELP_ID : null,
  ]
    .filter(Boolean)
    .join(' ');

  // `.send()`: a turn about the data or the plot, only while the box holds text to send.
  const sendButton = draft.trim() ? (
    <Box
      key="send"
      component="button"
      type="submit"
      onClick={keepKeyboardFocus}
      disabled={chatLocked || !ready || busy}
      aria-describedby={chatLocked ? CREATE_LINE_ID : undefined}
      sx={ghostButtonSx}
    >
      .send()
    </Box>
  ) : null;

  // The admin's plot in every library at once while `all` is pressed: the filled CTA while the
  // step's action is a plot, the quiet button once the confirmed data has a plot here. It waits
  // while the panel is open.
  const plotAllButton = (
    <Box
      key="plot-all"
      component="button"
      type="button"
      ref={createRef}
      onClick={onPlotAll}
      disabled={fanOutOpen || !canCreate}
      aria-label="Plot in all libraries"
      aria-describedby={ctaPlot ? ctaDescription : DATA_SUMMARY_ID}
      sx={ctaPlot ? ctaButtonSx : actionButtonSx}
    >
      {working('.plot_all()')}
    </Box>
  );

  // After a switch that offered it: the plot in this library with the remembered decisions, the
  // step's filled action whatever else the row holds.
  const carryButton = carry && (
    <Box
      key="carry"
      component="button"
      type="button"
      ref={createRef}
      data-testid="carry-plot"
      onClick={onCarry}
      disabled={!canCreate}
      aria-describedby={ctaPlot ? ctaDescription : DATA_SUMMARY_ID}
      // The library's name and the count make it long: it wraps at phone width.
      sx={{ ...ctaButtonSx, whiteSpace: 'normal', textAlign: 'left', maxWidth: '100%' }}
    >
      {working(carryText)}
    </Box>
  );

  // The quiet plot from the catalogue code: `.start_over()` once the library has a plot, the
  // plain `.create_plot()` beside a switch's offer before it.
  const quietCreate = (
    <Box
      key="create-quiet"
      component="button"
      type="button"
      ref={carry ? undefined : createRef}
      onClick={onCreate}
      disabled={!canCreate}
      aria-label={hasPlot ? 'Start over' : 'Create plot'}
      title={START_OVER_HELP}
      aria-describedby={[START_OVER_HELP_ID, stepLine ? STEP_LINE_ID : DATA_SUMMARY_ID].join(' ')}
      sx={actionButtonSx}
    >
      {hasPlot ? '.start_over()' : '.create_plot()'}
    </Box>
  );

  // The step's one filled action while it is a plot button: a plain button, so Enter in the box
  // sends a turn and never confirms. It stays in its place while a turn runs, waiting beside
  // `.stop()`, so the next step is in view the whole time.
  const filledCta = plotAll ? (
    plotAllButton
  ) : carry ? (
    carryButton
  ) : (
    <Box
      key="create"
      component="button"
      type="button"
      ref={createRef}
      onClick={onPlot}
      disabled={!canCreate}
      aria-label="Create plot"
      aria-describedby={ctaDescription}
      sx={ctaButtonSx}
    >
      {working('.create_plot()')}
    </Box>
  );

  return (
    <>
      {/* Step 1: what the plot button waits for, or what to check; the button names it as its
          description. */}
      {stepLine && (
        <Box
          id={STEP_LINE_ID}
          data-testid="data-step"
          sx={{ ...labelSx, color: 'var(--ink-soft)', mb: -1 }}
        >
          {stepLine}
        </Box>
      )}
      {/* While the chat waits for `all`, the line says so in the ink of the text, and the
          message box names it as its description. */}
      {createLine && (
        <Box
          id={CREATE_LINE_ID}
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
      {/* At phone width the buttons wrap below the box and stay at its right end, as the
          step's one CTA does beside it on a wide screen. */}
      <Box
        component="form"
        onSubmit={onSubmit}
        sx={{
          display: 'flex',
          gap: 1,
          alignItems: 'flex-end',
          justifyContent: 'flex-end',
          flexWrap: 'wrap',
        }}
      >
        <Box
          component="textarea"
          ref={messageRef}
          aria-label="Message"
          placeholder={
            // Without data, the chat is the other way to get some: example data or a formula.
            // With data, step 1 talks about the data and what the plot should do, step 2 about
            // the plot; short since 2026-11-02, the how-to is behind the data card's ⓘ. While
            // `all` is pressed in step 2 the box waits: the fan-out takes no text.
            chatLocked
              ? 'all libraries: the table goes as it is · turn all off to chat'
              : !hasData
                ? 'ask for example data, a curve, or a fix to your data'
                : !step2
                  ? `ask about your data, or say what the ${hasPlot ? 'next' : 'first'} plot should do`
                  : firstPlot
                    ? 'optional: what the first plot should do differently'
                    : 'ask for a change, e.g. log scale on y'
          }
          value={draft}
          maxLength={MAX_MESSAGE_CHARS}
          rows={2}
          disabled={!ready || chatLocked}
          aria-describedby={chatLocked ? CREATE_LINE_ID : undefined}
          onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
            onDraftChange(event.target.value)
          }
          onKeyDown={(event: React.KeyboardEvent<HTMLTextAreaElement>) => {
            // Enter sends text as a turn; an empty box creates nothing by accident.
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              if (draft.trim()) onSubmit();
            }
          }}
          sx={{ ...nativeControlSx, flex: '1 1 240px', resize: 'vertical' }}
        />
        {/* One fragment in every state, with keyed children: the filled CTA keeps its element
            from idle to running and back. */}
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
            {ctaPlot && filledCta}
          </>
        ) : ctaPlot ? (
          <>
            {sendButton}
            {/* Beside a switch's offer: the plot from the catalogue code, without the carry. */}
            {carry && !plotAll && quietCreate}
            {filledCta}
          </>
        ) : hasData ? (
          <>
            {/* The confirmed data has a plot here: the offer after a switch, if any, then
                starting over from the catalogue plot; `.send()` changes the latest version. */}
            {carryButton}
            {plotAll ? plotAllButton : quietCreate}
            {sendButton}
          </>
        ) : (
          // No data yet: nothing to plot, only a request for example data or a curve to send.
          sendButton
        )}
      </Box>
      {hasData && !plotAll && (hasPlot || carry) && (
        <Box component="span" id={START_OVER_HELP_ID} sx={visuallyHiddenSx}>
          {START_OVER_HELP}
        </Box>
      )}
      {confirmError && !step2 && (
        <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: -1 }}>
          {describeDataFailure(confirmError.code, confirmError.ref)}
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
