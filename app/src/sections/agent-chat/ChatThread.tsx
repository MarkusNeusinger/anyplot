/**
 * The chat thread: first the start item (`StartItem`, what the chat adapts and what it needs),
 * which stays first and scrolls up with the talk, then the session in chapters
 * (`threadModel.ts`): a `# data` line where the talk turns to the data, a `# plot` line where it
 * turns to the plot (`ChapterLine`), and a new `# data` line when the data changes after a plot.
 * In them: the user's turns and the page's own (`.example_data()`, `.create_plot()`,
 * `.carry_plot()`), the attachments the user sent, the data versions, the assistant's replies,
 * the fixed refusal under a plain label (its code behind the label's ⓘ), errors with their code
 * and request id, a library switch as a line of its own that names the decisions the plot in the
 * new library keeps, and a result card per plot version, its label on its border naming what it
 * answered (`plotSummaries`), the open card naming the remembered decisions it kept and added. A
 * lost confirmation adds nothing here: the status line at the chat frame's foot names it.
 *
 * Questions (the v4 mock): a typed turn that changed nothing (`isQuestion` in `threadModel.ts`)
 * gets a small round `?` at its bubble's left, which a screen reader skips, and its bubble starts
 * with a hidden "Question:"; its reply has no card and starts with `? answer · nothing changed`.
 * Both come once the turn's `done` and the memory read after it settled that, a moment after the
 * reply's text, inside the elements already there: the polite log reads them as they come and
 * nothing remounts. Each bubble carries an id and takes the focus from code (`tabIndex` -1), for
 * the jump from its chapter line's count (`ChapterLine`).
 *
 * The remembered decisions stand on the chapter line that holds them (`decisionsAt`): its `3
 * decisions ▾` unfolds the list (`Remembered`) as the row right after the line, a row of the same
 * flat list, so a newer chapter's line takes it over without remounting it. Its removals are
 * announced outside the log, by the page. After a paste with other columns than the data the
 * latest plot drew, the new data's line holds them until the next plot, as `3 earlier decisions ▾
 * · .forget_all()` (`decisionsEarlier`).
 *
 * Versions: the live data card at the latest data version stays open in both steps, its label
 * `data v3 · made long · 48 rows × 4 cols`; every older data version folds to that label (`▸ data
 * v2 · sheet "2026" · 12 rows × 5 cols`, `FoldedData`), which opens it read-only. Every plot
 * version but the latest folds the same way (`▸ plot v1 · matplotlib · first plot`), each with its
 * own image and code a click away. The live card moves under its own id with every new version
 * (`placeData` in `useAgentSession.ts`): a turn's version stands right after the turn's message,
 * before its reply, as a plot card does; a version of the card's own controls goes to the
 * thread's end, before and after a plot alike; a paste brings a card of its own. The rows render
 * as one flat list keyed by item, so React moves the card's node and keeps its state (the notes
 * and the code it showed open).
 *
 * A turn's version arrives with its `done`, after the reply streamed in, so the card lands above
 * a reply the user may be reading. The thread holds that reply still (`HoldReadingPosition`): the
 * browser's own scroll anchoring did not, since it anchors on the user's message above the card.
 * The reply is then the first after the live card; held in view, its one scroll into view
 * (`followReply`) moves nothing.
 *
 * While a turn is in flight, the working line with the site's loader holds the assistant's slot
 * at the thread's foot (`WorkingLine`, `workingLine` in `steps.ts`): `drawing your plot · 0:42`
 * while a plot is drawn, the words of a turn without plot work until its reply, `writing the
 * reply` below a run's card. The log's own polite live region reads its words as they change,
 * never its clock, and the reply, or an error that ended the turn, takes its place.
 *
 * The page's own turns show as the button the user pressed (`.start_over()`, "plot in plotly with
 * your 3 decisions"), never as the action the page sends. The summary of the data after a paste
 * has no button and shows no line of its own: the card says what was sent, and the summary
 * follows it. Its item stays in the state, which the in-progress line reads. The first reply
 * after the latest data card comes into view as it arrives, when the user's focus is in the
 * composer (`followReply`): a tall card would leave it below the fold.
 */

import { type ReactNode, useEffect, useId, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';

import {
  type AgentSessionState,
  type ChatItem,
  type DataSnapshot,
  type FeedbackInput,
  sessionBusy,
} from 'src/hooks/useAgentSession';
import { type ArtifactName, isPlotAction, type Theme } from 'src/lib/agent';
import { ChapterLine } from 'src/sections/agent-chat/ChapterLine';
import { countOf } from 'src/sections/agent-chat/countOf';
import { FoldedData } from 'src/sections/agent-chat/FoldedData';
import { HoldReadingPosition, REPLY_ATTRIBUTE } from 'src/sections/agent-chat/HoldReadingPosition';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import { LanguageOfferLine } from 'src/sections/agent-chat/LanguageOfferLine';
import {
  ANSWER_LABEL,
  ANSWER_LABEL_SPOKEN,
  ERROR_TEXT,
  localClock,
  NEW_DATA_PLOT,
  PLOT_FAILED_TEXT,
  QUESTION_WORD,
  refusalLabel,
} from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import {
  ForgetEarlier,
  Remembered,
  RememberedCount,
  type RememberedHandle,
} from 'src/sections/agent-chat/Remembered';
import { type CardOutcome, ResultCard } from 'src/sections/agent-chat/ResultCard';
import { runView, workingLine } from 'src/sections/agent-chat/steps';
import {
  bodyTextSx,
  CHAT_TEXT_MAX,
  inlineCodeSx,
  jumpTargetSx,
  labelSx,
  smallText,
  readableSx as textSx,
  THREAD_GAP,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { plotSummaries, questionDomId, threadModel } from 'src/sections/agent-chat/threadModel';
import { WorkingLine } from 'src/sections/agent-chat/WorkingLine';
import { colors, typography } from 'src/theme';

/** A passage of a reply in backticks, on one line: code, a column or a button the reply names. */
const INLINE_CODE = /`([^`\n]+)`/g;

/**
 * A passage of a reply between two pairs of asterisks, on one line: the assistant's Markdown for
 * strong text, which the page showed as asterisks. It opens after the line's start or a character
 * that is no letter, digit or asterisk, and closes before one, with no space inside its ends: so a
 * product such as `2**10` or `a ** b` stays as written, and so does a pair inside a word. A single
 * asterisk inside stays a character of the passage (`**Revenue = Quantity * Price**`).
 */
const STRONG =
  /(^|[^\p{L}\p{N}*])\*\*([^\s*](?:(?:[^*\n]|\*(?!\*))*[^\s*])?)\*\*(?![\p{L}\p{N}*])/gmu;

/** A passage of a reply outside backticks, with its strong passages set off and the asterisks gone. */
function strongParts(text: string, keyBase: number): ReactNode[] {
  const parts: ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(STRONG)) {
    const start = match.index + match[1].length;
    if (start > last) parts.push(text.slice(last, start));
    parts.push(<strong key={`strong-${keyBase}-${start}`}>{match[2]}</strong>);
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

/**
 * A reply's text with its passages in backticks set off as code, never with the backticks, and its
 * strong passages set off outside them: asterisks inside code stay code.
 */
function ReplyText({ text }: { text: string }) {
  const parts: ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(INLINE_CODE)) {
    if (match.index > last) parts.push(...strongParts(text.slice(last, match.index), last));
    parts.push(
      <Box component="code" key={match.index} sx={inlineCodeSx}>
        {match[1]}
      </Box>
    );
    last = match.index + match[0].length;
  }
  parts.push(...strongParts(text.slice(last), last));
  return <>{parts}</>;
}

/**
 * What the user's bubble of a page turn says: the button as it read when pressed (the page passes
 * it), else the button that sends the action; a carry the chat started has no button of its own.
 */
function actionText(item: Extract<ChatItem, { kind: 'action' }>): string {
  if (item.label) return item.label;
  if (item.action === 'plot_new_data') return NEW_DATA_PLOT;
  return item.action === 'carry_plot'
    ? `plot in ${item.library} with your decisions`
    : `.${item.action}()`;
}

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
  /**
   * The card at a `data` item, with the version it shows (`snapshot`), or at the `transcription`
   * item that waits (`DataPanel`).
   */
  renderData?: (part: 'data' | 'transcription', snapshot?: DataSnapshot) => React.ReactNode;
  /** Whether the first reply after a card may come into view: the user's focus is in the composer. */
  followReply?: () => boolean;
  /** The thread's first item, before every turn: the start item (`StartItem`). */
  start?: ReactNode;
  /**
   * The remembered decisions' removals (`Remembered`), on the chapter line that holds them;
   * without it the thread shows no decisions.
   */
  decisions?: ThreadDecisions;
  /** The `.switch()` of a language line (`LanguageOfferLine`); without it the line has no button. */
  onAcceptLanguage?: (offerId: number) => Promise<void>;
}

/** What the remembered decisions' list needs from the page (`RememberedProps`). */
export interface ThreadDecisions {
  /** Something is in flight: the server would refuse a removal. */
  disabled: boolean;
  onForget: (entryId: string) => Promise<void>;
  onForgetAll?: () => Promise<void>;
  /** Where the focus goes once the last decision is gone. */
  fallbackFocusRef?: React.RefObject<HTMLElement | null>;
  /** Say what a removal did, in the page's status region outside the thread's log. */
  onAnnounce: (text: string) => void;
}

/** The kinds of item that answer a turn: the first of them after the live card is its reply. */
const REPLY_KINDS: ReadonlySet<ChatItem['kind']> = new Set(['assistant', 'refusal', 'error']);

/** Where a user's turn stands: on the right, no wider than a readable line. */
const promptPlaceSx = {
  alignSelf: 'flex-end',
  maxWidth: { xs: '100%', sm: `min(85%, ${CHAT_TEXT_MAX})` },
} as const;

/** The bubble of a user's turn. */
const bubbleSx = {
  ...bodyTextSx,
  bgcolor: 'var(--bg-elevated)',
  border: '1px solid var(--rule)',
  borderRadius: 2,
  px: 1.5,
  py: 1,
} as const;

/**
 * The user's turns, on the right; like every text item of the thread (`textSx`), no wider than
 * a readable line since the column grows up to 1360 px (2026-11-02). The result cards take the
 * full width.
 */
const promptSx = { ...bubbleSx, ...promptPlaceSx } as const;

/** A question's mark, a small round `?` at its bubble's left (the v4 mock); a screen reader skips it. */
const questionMarkSx = {
  flex: 'none',
  width: 20,
  height: 20,
  borderRadius: '50%',
  border: '1px solid var(--rule)',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontFamily: typography.mono,
  fontSize: smallText,
  lineHeight: 1,
  color: 'var(--ink-soft)',
} as const;

function Item({
  item,
  props,
  latestVersion,
  waiting,
  summaries,
  question,
  answer,
}: {
  item: ChatItem;
  props: ChatThreadProps;
  latestVersion: number;
  /** This `transcription` item is the table read from text that waits for its decision. */
  waiting: boolean;
  /** What each plot version answered, for its card's label (`plotSummaries`). */
  summaries: ReadonlyMap<number, string | null>;
  /** This typed turn is a question (`isQuestion`): its bubble carries the `?` mark. */
  question: boolean;
  /** This reply answers a question (`ThreadModel.answers`): it starts with the answer label. */
  answer: boolean;
}) {
  switch (item.kind) {
    case 'paste':
      // The attachment as its chip named it: the user's turn, which the card answers.
      return (
        <Box data-testid="paste-item" sx={{ ...promptSx, fontFamily: typography.mono }}>
          <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', mr: 1 }}>
            ❯
          </Box>
          {item.text}
        </Box>
      );
    case 'data':
      return <>{props.renderData?.('data', item.snapshot)}</>;
    case 'data_stub':
      return <FoldedData item={item} />;
    case 'switch':
      // The library the plots are made in from here, and what the plot there keeps; never "0
      // decisions": a switch that carries none says only where the plots go.
      return (
        <Box data-testid="switch-line" sx={{ ...labelSx, ...textSx, color: 'var(--ink-soft)' }}>
          · plotting in {item.library} from here
          {item.decisions ? `, ${countOf(item.decisions, 'decision')} kept` : ''}
        </Box>
      );
    case 'transcription':
      // Only the table that waits shows its card; one a new paste or a switch dropped says so.
      return waiting ? (
        <>{props.renderData?.('transcription')}</>
      ) : (
        <Box sx={{ ...labelSx, ...textSx }}># table read from text · not used</Box>
      );
    case 'user':
      // The row and the bubble stay the same elements when the turn turns out a question: its
      // mark comes in beside the bubble, and the bubble, a jump's target, starts with the word.
      return (
        <Box
          data-testid="user-turn"
          sx={{ ...promptPlaceSx, display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}
        >
          {question && (
            <Box component="span" aria-hidden data-testid="question-mark" sx={questionMarkSx}>
              ?
            </Box>
          )}
          <Box
            id={questionDomId(item.id)}
            tabIndex={-1}
            sx={{ ...bubbleSx, ...jumpTargetSx, minWidth: 0 }}
          >
            {/* Read with the bubble, never announced as it comes: the reply's label says it. */}
            {question && (
              <Box component="span" aria-live="off" sx={visuallyHiddenSx}>
                {`${QUESTION_WORD} `}
              </Box>
            )}
            <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', mr: 1 }}>
              ❯
            </Box>
            {item.text}
          </Box>
        </Box>
      );
    case 'action':
      // The page's own turns as their buttons: `.example_data()` without data, the plot button
      // as it read (also for the carry after a library switch, since the button keeps its name)
      // or `.start_over()`. A plot names the library it is made in, which the text of a carry the
      // chat started (no button, no label) names already.
      return (
        <Box data-testid="action-item" sx={{ ...promptSx, fontFamily: typography.mono }}>
          <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', mr: 1 }}>
            ❯
          </Box>
          {actionText(item)}
          {isPlotAction(item.action) && (item.action !== 'carry_plot' || !!item.label) && (
            <Box component="span" sx={{ color: 'var(--ink-muted)', ml: 1 }}>
              # {item.library}
            </Box>
          )}
        </Box>
      );
    case 'assistant':
      // A question's reply has no card: it starts with the label that says the turn changed
      // nothing, which comes in once the turn's `done` (and its memory read) said so, inside the
      // same element, so the polite log reads the label alone: the mark is hidden, the bubble's
      // word and the chapter's count are no live text (`aria-live="off"`).
      return (
        <Box sx={{ ...bodyTextSx, ...textSx, borderLeft: '2px solid var(--rule)', pl: 1.5 }}>
          {answer && (
            <Box
              data-testid="answer-label"
              sx={{ ...labelSx, display: 'block', lineHeight: 1.6, whiteSpace: 'normal' }}
            >
              <span aria-hidden>{`? ${ANSWER_LABEL}`}</span>
              <Box component="span" sx={visuallyHiddenSx}>
                {ANSWER_LABEL_SPOKEN}
              </Box>
            </Box>
          )}
          <ReplyText text={item.text} />
        </Box>
      );
    case 'refusal':
      return (
        <Box
          sx={{ ...textSx, borderLeft: `2px solid ${colors.warning}`, pl: 1.5 }}
          data-testid="refusal"
        >
          {/* A plain label: the code is the service's word for the log, behind the ⓘ. The
              line height of the other ⓘ lines, so a label that wraps keeps its spacing. */}
          <Box sx={{ ...labelSx, lineHeight: 1.6 }}>
            {refusalLabel(item.code)}
            {/* The service's own text says 00:00 UTC: the page adds the user's own time. */}
            {item.until && localClock(item.until) ? ` · until ${localClock(item.until)}` : ''}
            <InfoPopover
              label="About this answer"
              heading="# a fixed answer of the service, not the assistant's"
              lines={[`reason: ${item.code}`]}
              testId="refusal-details"
            />
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
      // A quiet line; its details, where it has any, behind the ⓘ at its end. A lost
      // confirmation has none: the status line at the chat frame's foot names it.
      return (
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
    case 'language_offer':
      return (
        <LanguageOfferLine
          item={item}
          current={props.state.plotLanguage.language}
          busy={sessionBusy(props.state)}
          onAccept={props.onAcceptLanguage}
        />
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
          summary={summaries.get(version.number) ?? null}
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

/**
 * The id of the first reply after the live data card, or null while it has none yet: the summary
 * after a paste, the reply of the turn whose version the card shows (the card lands right before
 * it), or the first reply after a version of the card's own controls, which moved it to the end.
 * Each comes into view once, the first time it is that reply.
 */
function firstReplyId(items: ChatItem[]): number | null {
  let card = -1;
  for (let index = items.length - 1; index >= 0; index -= 1) {
    if (items[index].kind === 'data') {
      card = index;
      break;
    }
  }
  if (card < 0) return null;
  return items.slice(card + 1).find(item => REPLY_KINDS.has(item.kind))?.id ?? null;
}

export function ChatThread(props: ChatThreadProps) {
  const { items, versions } = props.state;
  const numbers = Object.keys(versions).map(Number);
  const latestVersion = numbers.length ? Math.max(...numbers) : 0;
  const summaries = useMemo(
    () =>
      plotSummaries(
        items,
        version => versions[version]?.library,
        version => versions[version]?.result.new_data
      ),
    [items, versions]
  );
  const { memoryTurn, memory } = props.state;
  const { rows, chapters, answers, decisionsAt, decisionsEarlier } = useMemo(
    () => threadModel(items, memoryTurn),
    [items, memoryTurn]
  );
  // The list's own `.forget_all()`, which the new data's line offers after a paste with other
  // columns (`ForgetEarlier`): the list shows its progress and a failure, so it opens for it.
  const rememberedRef = useRef<RememberedHandle>(null);
  const questions = useMemo(
    () => new Set(chapters.flatMap(chapter => chapter.questions)),
    [chapters]
  );
  // The remembered decisions: folded by default, and folded again once the memory is empty, so
  // the next decision starts as the first did. The thread holds the state, since the line that
  // shows it changes with the chapters.
  const [decisionsOpen, setDecisionsOpen] = useState(false);
  const decisionCount = memory?.entries.length ?? 0;
  if (decisionsOpen && decisionCount === 0) setDecisionsOpen(false);
  const decisionsId = useId();
  const decisionsHandoffRef = useRef(false);
  const { decisions } = props;
  const working = workingLine(props.state);
  const drawing = runView(props.state).drawing;
  const waitingId = props.state.transcription
    ? [...items].reverse().find(item => item.kind === 'transcription')?.id
    : undefined;
  // The first reply after a card comes into view once, as it arrives (C-08): below a tall card
  // it would land under the fold, while the user's eyes are on the composer.
  const replyId = firstReplyId(items);
  const replyRef = useRef<HTMLDivElement>(null);
  const logRef = useRef<HTMLDivElement>(null);
  // A reply that was there when the thread mounted has arrived already: only a new one moves it.
  const followed = useRef<number | null>(replyId);
  const { followReply } = props;
  useEffect(() => {
    if (replyId === null || followed.current === replyId) return;
    followed.current = replyId;
    if (followReply?.())
      replyRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' });
  }, [replyId, followReply]);
  return (
    <Box
      ref={logRef}
      role="log"
      aria-label="Conversation"
      sx={{ display: 'flex', flexDirection: 'column', gap: THREAD_GAP, minWidth: 0 }}
    >
      {props.start}
      {/* One flat list of chapter lines and items, never a box per chapter: a card that moves
          into a later chapter stays a child of the same parent, so React moves its node and
          keeps its state instead of mounting it anew. The hold keeps a reply still when the card
          lands above it, and adds no element. */}
      <HoldReadingPosition items={items} log={logRef}>
        {rows.flatMap((row): ReactNode[] => {
          if (row.kind === 'chapter') {
            const holds = !!decisions && row.chapter.index === decisionsAt;
            const line = (
              <ChapterLine
                key={`chapter-${row.chapter.index}`}
                chapter={row.chapter}
                // No count while the memory is empty or unknown: never "0 decisions".
                decisions={
                  holds && decisionCount > 0 ? (
                    <RememberedCount
                      memory={memory}
                      open={decisionsOpen}
                      listId={decisionsId}
                      onToggle={() => setDecisionsOpen(open => !open)}
                      handoffRef={decisionsHandoffRef}
                      earlier={decisionsEarlier}
                    />
                  ) : undefined
                }
                decisionsAction={
                  holds && decisionsEarlier && decisions.onForgetAll ? (
                    <ForgetEarlier
                      memory={memory}
                      disabled={decisions.disabled}
                      onForgetAll={() => {
                        setDecisionsOpen(true);
                        rememberedRef.current?.forgetAll();
                      }}
                    />
                  ) : undefined
                }
              />
            );
            if (!holds) return [line];
            // The list right after the line that holds it, as one keyed row of the same flat list:
            // a newer chapter's line takes it over and React moves its node, with its state, and
            // gives a focus inside it back after the move.
            return [
              line,
              <Remembered
                key="remembered"
                memory={memory}
                id={decisionsId}
                open={decisionsOpen}
                disabled={decisions.disabled}
                onForget={decisions.onForget}
                onForgetAll={decisions.onForgetAll}
                fallbackFocusRef={decisions.fallbackFocusRef}
                onAnnounce={decisions.onAnnounce}
                earlier={decisionsEarlier}
                handleRef={rememberedRef}
              />,
            ];
          }
          const { item } = row;
          // The page's summary turn has no button: its card says what was sent, and the summary
          // follows.
          if (item.kind === 'action' && item.action === 'summarize_data') return [];
          const node = (
            <Item
              key={item.id}
              item={item}
              props={props}
              latestVersion={latestVersion}
              waiting={item.id === waitingId}
              summaries={summaries}
              question={questions.has(item.id)}
              answer={answers.has(item.id)}
            />
          );
          // Every reply stands in the same wrapper, the first reply after the live card with the
          // ref that brings it into view: a reply that stops being the first one (the card moved
          // below it) keeps its element, so the polite log never reads it out a second time.
          if (!REPLY_KINDS.has(item.kind)) return [node];
          const first = item.id === replyId;
          return [
            <Box
              key={item.id}
              ref={first ? replyRef : undefined}
              data-testid={first ? 'first-reply' : undefined}
              {...{ [REPLY_ATTRIBUTE]: item.id }}
              sx={{ minWidth: 0 }}
            >
              {node}
            </Box>,
          ];
        })}
      </HoldReadingPosition>
      {/* The assistant's slot, in its style, in softer ink: provisional until the reply. One
          element from the turn's start to its end, so only its words change: the loader stays
          where it is, and the reply takes its place in the thread's gap, in its line height. */}
      {working && <WorkingLine line={working} drawing={drawing} />}
    </Box>
  );
}
