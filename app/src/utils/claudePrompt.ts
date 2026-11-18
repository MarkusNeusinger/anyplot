/**
 * Builds a Claude-Code-ready prompt from a feedback message. Pasted into the
 * CLI it gives Claude the page URL, the user's words, and a clear three-step
 * plan (analyse/reproduce → implement → open PR) so triage on /debug flows
 * straight into a working session.
 *
 * It carries three fields of a feedback entry only: the message, the page and
 * the reaction. The legal page's site feedback row (`app/src/pages/LegalPage.tsx`,
 * with its crawler copy in `api/routers/seo.py`) states exactly these as what
 * can go to the coding assistant, so a new field changes that row too.
 *
 * The repository is public, so the prompt asks Claude to keep the visitor's
 * quoted words out of commits, pull requests and issues.
 */
export function buildClaudePrompt(
  message: string,
  path: string | null,
  reaction: string | null
): string {
  const origin = typeof window !== 'undefined' ? window.location.origin : '';
  const url = path ? `${origin}${path}` : origin || '(unknown URL)';
  const kind =
    reaction === 'bug'
      ? 'bug report'
      : reaction === 'idea'
        ? 'feature request'
        : reaction === 'thumbs_down'
          ? 'negative feedback'
          : reaction === 'thumbs_up'
            ? 'positive feedback'
            : 'feedback';
  const quoted = message
    .split('\n')
    .map(line => `> ${line}`)
    .join('\n');
  return `A user left the following ${kind} on ${url}:

${quoted}

Please:
1. Analyze the report and reproduce the issue locally (or scope the feature request).
2. Implement a fix or the requested change.
3. Open a pull request with the proposed solution.

Do not quote the message in the repository, a commit, a pull request or an issue; describe the problem in your own words.`;
}
