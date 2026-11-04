/**
 * The agent chat's composer at the foot of the thread (`AgentChatPage.tsx`): the line that names
 * the step's action, the service's pause note, `.example_data()` while the session has no data,
 * the message box and its buttons, and the counter near the message cap.
 *
 * Its buttons: `.send()`, the step's action (`.create_plot()`, or `.start_over()` once this
 * library has a plot, the carry after a switch, `.plot_all()` while `all` is pressed), and
 * `.stop()` while a run is in progress, as buttons of their own keys, so the one a run replaces
 * never turns into `.stop()` in place with a focus a second key press would spend on stopping.
 * The page decides what each does and when it waits; this component only lays them out.
 */

import Box from '@mui/material/Box';

import { MAX_MESSAGE_CHARS } from 'src/lib/agent';
import { ExampleDataLine } from 'src/sections/agent-chat/ExampleData';
import { servicePausedText } from 'src/sections/agent-chat/messages';
import { DATA_SUMMARY_ID } from 'src/sections/agent-chat/PinnedData';
import {
  actionButtonSx,
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

export interface ComposerProps {
  draft: string;
  onDraftChange: (text: string) => void;
  /** The form's submit, also Enter in the box: the page's `handleSend`. */
  onSubmit: (event?: React.FormEvent) => void;
  messageRef: React.RefObject<HTMLTextAreaElement | null>;
  /** The step's action button, where the keyboard continues after `.confirm()`. */
  createRef: React.RefObject<HTMLButtonElement | null>;
  /** The session is open and answers. */
  ready: boolean;
  busy: boolean;
  running: boolean;
  stopping: boolean;
  /** The session holds data. */
  hasData: boolean;
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
  /** Until when (ISO) the service paused, for the note above the box. */
  pausedUntil: string | null;
  exampleOffer: boolean;
  exampleWorking: boolean;
  onExampleData: (event: React.MouseEvent) => void;
  /** The notice after a click on the step's action before the confirmation. */
  gate: { text: string; action: string } | null;
  gateRef: React.RefObject<HTMLDivElement | null>;
  onGoToGate: () => void;
  onStop: (event: React.MouseEvent) => void;
  onCreate: (event: React.MouseEvent) => void;
  onCarry: (event: React.MouseEvent) => void;
  onPlotAll: (event: React.MouseEvent) => void;
  /** A key press on a button a run replaces continues in the message box. */
  keepKeyboardFocus: (event: React.MouseEvent) => void;
}

export function Composer(props: ComposerProps) {
  const { draft, onDraftChange, onSubmit, messageRef, createRef } = props;
  const { ready, busy, running, stopping, hasData, step2, firstPlot, hasPlot } = props;
  const { canCreate, plotAll, chatLocked, libraryCount, fanOutOpen, carryText } = props;
  const { pausedUntil, exampleOffer, exampleWorking, onExampleData } = props;
  const { gate, gateRef, onGoToGate, onStop, onCreate, onCarry, onPlotAll } = props;
  const { keepKeyboardFocus } = props;
  const carry = carryText !== null;

  // The composer's create action while `all` is pressed, for every library at once: the CTA
  // before the first plot, the quiet button otherwise, and before the confirmation a click
  // shows the notice. It waits while the panel is open.
  const plotAllButton = (
    <Box
      key="plot-all"
      component="button"
      type="button"
      ref={createRef}
      onClick={onPlotAll}
      disabled={fanOutOpen || (step2 ? !canCreate : !ready || busy)}
      aria-label="Plot in all libraries"
      aria-describedby={
        [
          step2 ? DATA_SUMMARY_ID : gate ? 'agent-create-gate' : null,
          chatLocked ? 'agent-create-line' : null,
        ]
          .filter(Boolean)
          .join(' ') || undefined
      }
      sx={firstPlot ? ctaButtonSx : actionButtonSx}
    >
      .plot_all()
    </Box>
  );

  return (
    <>
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
                disabled={step2 ? !canCreate : !ready || busy}
                aria-describedby={
                  step2
                    ? `${DATA_SUMMARY_ID}${firstPlot ? ' agent-create-line' : ''}`
                    : gate
                      ? 'agent-create-gate'
                      : undefined
                }
                // The library's name and the count make it long: it wraps at phone width.
                sx={{
                  ...(step2 ? ctaButtonSx : actionButtonSx),
                  whiteSpace: 'normal',
                  textAlign: 'left',
                  maxWidth: '100%',
                }}
              >
                {carryText}
              </Box>
            )}
            {/* Step 2 after a plot: start over from the catalogue plot with this data.
                Beside the offer: the plot from the catalogue code, without the carry. Step 1: the step is
                visible from the foot too, and a click says what comes first instead of
                calling the server. With `all`, `.plot_all()`. */}
            {hasData && plotAll && plotAllButton}
            {hasData && !plotAll && (
              <Box
                component="button"
                type="button"
                ref={carry ? undefined : createRef}
                onClick={onCreate}
                disabled={step2 ? !canCreate : !ready || busy}
                // Once this library has a plot, the button starts over from the
                // catalogue plot; `.send()` beside it changes the latest version.
                aria-label={hasPlot ? 'Start over' : 'Create plot'}
                title={hasPlot || carry ? START_OVER_HELP : undefined}
                aria-describedby={
                  [
                    hasPlot || carry ? START_OVER_HELP_ID : null,
                    step2 ? DATA_SUMMARY_ID : gate ? 'agent-create-gate' : null,
                  ]
                    .filter(Boolean)
                    .join(' ') || undefined
                }
                sx={actionButtonSx}
              >
                {hasPlot ? '.start_over()' : '.create_plot()'}
              </Box>
            )}
            {hasData && (hasPlot || carry) && !plotAll && (
              <Box component="span" id={START_OVER_HELP_ID} sx={visuallyHiddenSx}>
                {START_OVER_HELP}
              </Box>
            )}
            {/* Before the library's first plot the offer submits text; no `.send()` then. */}
            {!firstPlot && (
              <Box
                component="button"
                type="submit"
                onClick={keepKeyboardFocus}
                disabled={chatLocked || !draft.trim() || !ready || busy}
                aria-describedby={chatLocked ? 'agent-create-line' : undefined}
                sx={ghostButtonSx}
              >
                .send()
              </Box>
            )}
          </>
        )}
      </Box>
      {/* No role on the visible notice: the status box below speaks it, once. */}
      {gate && (
        <Box
          ref={gateRef}
          data-testid="create-gate"
          sx={{
            mt: -1,
            borderLeft: `3px solid ${colors.warning}`,
            pl: 1.5,
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            columnGap: 1,
            rowGap: 0.75,
          }}
        >
          <Box
            id="agent-create-gate"
            sx={{ ...labelSx, color: 'var(--ink)', flex: '1 1 220px', lineHeight: 1.6 }}
          >
            # {gate.text}
          </Box>
          <Box
            component="button"
            type="button"
            onClick={onGoToGate}
            aria-label={gate.action}
            sx={actionButtonSx}
          >
            .show()
          </Box>
        </Box>
      )}
      <Box role="status" data-testid="composer-status" sx={visuallyHiddenSx}>
        {gate ? gate.text : ''}
      </Box>
      {draft.length > MAX_MESSAGE_CHARS * 0.9 && (
        <Box sx={{ ...labelSx, mt: -1 }}>
          {draft.length} / {MAX_MESSAGE_CHARS}
        </Box>
      )}
    </>
  );
}
