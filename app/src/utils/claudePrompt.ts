/**
 * Builds a Claude-Code-ready prompt from a feedback message. Pasted into the
 * CLI it gives Claude the page URL, the user's words, and a clear three-step
 * plan (analyse/reproduce → implement → open PR) so triage on /debug flows
 * straight into a working session.
 */
export function buildClaudePrompt(
  message: string,
  path: string | null,
  reaction: string | null,
): string {
  const origin = typeof window !== 'undefined' ? window.location.origin : '';
  const url = path ? `${origin}${path}` : origin || '(unknown URL)';
  const kind =
    reaction === 'bug' ? 'bug report'
    : reaction === 'idea' ? 'feature request'
    : reaction === 'thumbs_down' ? 'negative feedback'
    : reaction === 'thumbs_up' ? 'positive feedback'
    : 'feedback';
  const quoted = message.split('\n').map(line => `> ${line}`).join('\n');
  return `A user left the following ${kind} on ${url}:

${quoted}

Please:
1. Analyze the report and reproduce the issue locally (or scope the feature request).
2. Implement a fix or the requested change.
3. Open a pull request with the proposed solution.`;
}
