/**
 * A chapter's line in the thread (`threadModel.ts`): `# data` where the talk turns to the data
 * (step 1), `# plot` where it turns to the plot (step 2), centred between two rules (the v4 mock,
 * kit 3 option C). The name is an `h3` heading, so a screen reader can walk the session by its
 * chapters; the `#` is the chat's comment mark and is not read out.
 *
 * The line is a flex row with its rules as pseudo-elements, and the heading holds the name alone:
 * what the chapter counts stands in the row beside the heading, between the name and the
 * right-hand rule, so a control never becomes part of the heading's name. First the remembered
 * decisions on the line that holds them (`3 decisions ▾ · full`, `Remembered.tsx`, which the
 * thread passes; on the new data's line after a paste with other columns `3 earlier decisions ▾ ·
 * .forget_all()`), then the chapter's questions (`· 2 questions`), nothing for none. Where the
 * words do not fit one line (a phone), they wrap between the rules, the heading first, each count
 * whole.
 *
 * The count of the questions is a button: a press moves the focus to the chapter's first question,
 * each further press to the next, and after the last back to the first. The target is the
 * question's bubble (`questionDomId`, `tabIndex` -1), which a ring and a tint mark for a moment
 * (`jumpTargetSx`, `JUMP_MS`); the page's `scroll-padding-top` keeps it clear of the site's sticky
 * masthead. The heading carries an id of its own, for a jump to it.
 */

import { type ReactNode, useRef } from 'react';

import Box from '@mui/material/Box';

import { countOf } from 'src/sections/agent-chat/countOf';
import { questionJumpName } from 'src/sections/agent-chat/messages';
import {
  CHAPTER_ROW_GAP,
  chapterControlSx,
  JUMP_MS,
  labelSx,
} from 'src/sections/agent-chat/styles';
import { type Chapter, questionDomId } from 'src/sections/agent-chat/threadModel';

/**
 * The rule on either side of the line's words, at the height of their first row: half the line's
 * height down, so a line whose counts wrap (a phone) keeps its rules beside the heading.
 */
const rule = {
  content: '""',
  flex: '1 1 0',
  minWidth: 16,
  mt: '0.8em',
  borderTop: '1px solid var(--rule)',
};

/** The highlight timers by target, so a second jump to the same bubble restarts its flash. */
const flashes = new WeakMap<HTMLElement, ReturnType<typeof setTimeout>>();

/** Mark `target` as a jump's target for `JUMP_MS` (`data-jump`, which `jumpTargetSx` styles). */
function flash(target: HTMLElement) {
  const running = flashes.get(target);
  if (running) clearTimeout(running);
  target.setAttribute('data-jump', '');
  flashes.set(
    target,
    setTimeout(() => {
      target.removeAttribute('data-jump');
      flashes.delete(target);
    }, JUMP_MS)
  );
}

const reducedMotion = () =>
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

/**
 * A count in the line, after its `·`, kept whole when the line wraps. The thread's log does not
 * read it out as it comes or changes (`aria-live="off"`): a question's reply says what the count
 * would, and a screen reader finds the count on the chapter's heading.
 */
function Count({ children }: { children: ReactNode }) {
  return (
    <Box
      component="span"
      aria-live="off"
      sx={{ display: 'inline-flex', alignItems: 'center', whiteSpace: 'nowrap' }}
    >
      <Box component="span" aria-hidden sx={{ mr: 1 }}>
        ·
      </Box>
      {children}
    </Box>
  );
}

/** The chapter's count of its questions, the button that jumps to them in turn. */
function QuestionJump({ questions }: { questions: readonly number[] }) {
  // The question the last press went to: the next press goes to the one after it, after the last
  // back to the first, also when a question came in meanwhile.
  const last = useRef<number | null>(null);
  const jump = () => {
    const at = last.current === null ? -1 : questions.indexOf(last.current);
    const id = questions[(at + 1) % questions.length];
    last.current = id;
    const target = document.getElementById(questionDomId(id));
    if (!target) return;
    target.scrollIntoView?.({ block: 'center', behavior: reducedMotion() ? 'auto' : 'smooth' });
    target.focus({ preventScroll: true });
    flash(target);
  };
  return (
    <Box
      component="button"
      type="button"
      data-testid="question-jump"
      onClick={jump}
      aria-label={questionJumpName(questions.length)}
      sx={chapterControlSx}
    >
      {countOf(questions.length, 'question')}
    </Box>
  );
}

export function ChapterLine({
  chapter,
  decisions,
  decisionsAction,
}: {
  chapter: Chapter;
  /** The remembered decisions' count and toggle, on the line that holds them (`Remembered.tsx`). */
  decisions?: ReactNode;
  /**
   * A control beside that count, as a count of its own that wraps whole: the new data's
   * `.forget_all()` after a paste with other columns (`ForgetEarlier`).
   */
  decisionsAction?: ReactNode;
}) {
  const asked = chapter.questions.length > 0;
  return (
    <Box
      data-testid="chapter-line"
      data-chapter={chapter.kind}
      sx={{
        ...labelSx,
        color: 'var(--ink-soft)',
        lineHeight: 1.6,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 1.25,
        minWidth: 0,
        '&::before': rule,
        '&::after': rule,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'center',
          columnGap: 1,
          rowGap: CHAPTER_ROW_GAP,
          minWidth: 0,
        }}
      >
        <Box
          component="h3"
          id={`agent-chapter-${chapter.index}`}
          sx={{ font: 'inherit', color: 'inherit', m: 0, whiteSpace: 'nowrap' }}
        >
          <Box component="span" aria-hidden>
            #{' '}
          </Box>
          {chapter.kind}
        </Box>
        {decisions && <Count>{decisions}</Count>}
        {decisions && decisionsAction && <Count>{decisionsAction}</Count>}
        {asked && (
          <Count>
            <QuestionJump questions={chapter.questions} />
          </Count>
        )}
      </Box>
    </Box>
  );
}
