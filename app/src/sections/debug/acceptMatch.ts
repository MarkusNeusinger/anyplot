/**
 * The accept-match rule of the regression harness (`agents/evals/matrix.py`),
 * applied to a feedback case: does the owner's reaction agree with what the
 * pipeline did? A contradiction is the first of the three reasons to promote a
 * case (the promotion rule is guidance; nothing enforces it).
 */

import type { CaseExpected, FeedbackReaction } from 'src/lib/agent';

/** The outcome a reaction implies: thumbs up accepts, thumbs down rejects; a bug or an idea implies none. */
export function expectedFromReaction(reaction: FeedbackReaction | string): CaseExpected | null {
  if (reaction === 'thumbs_up') return 'accepted';
  if (reaction === 'thumbs_down') return 'rejected';
  return null;
}

/**
 * `true` when the reaction agrees with the pipeline (`ok` counts as accepted,
 * any other status as rejected), `false` when it contradicts it, `null` when
 * there is nothing to compare (a bug or an idea, or no pipeline status).
 */
export function acceptMatch(
  reaction: FeedbackReaction | string,
  pipelineStatus: string | null
): boolean | null {
  const expected = expectedFromReaction(reaction);
  if (expected === null || pipelineStatus === null) return null;
  return (expected === 'accepted') === (pipelineStatus === 'ok');
}
