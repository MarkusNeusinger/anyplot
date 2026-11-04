/**
 * The case detail's lines about the pipeline's rounds and the session's
 * latest run: closed codes and counts the agents service records, so a case
 * says why a round ended `render_failed` (`gates R1 · crash key`) and, on a
 * chat case that holds no version, whether the latest run stored a plot.
 */

import type { AgentCaseLastRun, AgentCaseRound } from 'src/lib/agent';

/** One round as a line: how it ended, where, and the closed ids of what failed (`gates R1 · crash key`). */
export function roundLine(round: AgentCaseRound): string {
  return [
    `round ${round.attempt}: ${round.outcome}${round.step ? ` at ${round.step}` : ''}`,
    round.findings ? `${round.findings} ${round.findings === 1 ? 'finding' : 'findings'}` : null,
    round.defects.length ? round.defects.join(' ') : null,
    round.gates_failed.length ? `gates ${round.gates_failed.join(' ')}` : null,
    round.sandbox_failures.length ? `crash ${round.sandbox_failures.join(' ')}` : null,
    round.shipped ? 'shipped' : null,
  ]
    .filter((part): part is string => !!part)
    .join(' · ');
}

/**
 * What the session held when the case was sent, and how its latest plot run
 * ended: on a chat case, the line that tells a plot the page missed from a run
 * that failed. `null` for a case from before the agents service sent them.
 */
export function sessionLine(
  versions: number | null | undefined,
  lastRun: AgentCaseLastRun | null | undefined
): string | null {
  if (versions === null || versions === undefined) return null;
  const held = `session: ${versions} ${versions === 1 ? 'version' : 'versions'}`;
  if (!lastRun) return `${held} · no plot run`;
  const ended = [lastRun.status, lastRun.reason].filter(Boolean).join(', ');
  const stored = lastRun.version !== null ? `stored v${lastRun.version}` : 'stored no version';
  const turn = lastRun.turn !== null ? ` (turn ${lastRun.turn})` : '';
  return `${held} · latest run${turn}: ${ended} · ${stored}`;
}
