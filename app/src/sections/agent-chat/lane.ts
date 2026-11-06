/**
 * The texts the chat shows every user about the assistant and what it keeps, on both lanes:
 * the admin's chat is the visitors' (owner, 2026-11-06), so nothing deep in the tree knows
 * which lane the page runs on. The lane only picks the API (`AgentChatPage`), and every admin
 * extra sits in the admin menu (`AdminMenu`).
 */

/**
 * The notice above the first input (`ExperimentalNotice`): one line, always in view, and the
 * lines its ⓘ button opens, above the link to the legal page. Each detail states what the legal
 * page's assistant section says ("memory", "feedback", "the model", "limits"): the hour is the
 * agents service's idle sweep (`AGENT_SESSION_IDLE_S`, 3600 s). The owner reads every
 * user-facing text: keep them in the PR's "Texts to read".
 */
export const EXPERIMENTAL_LINE = 'experimental AI · answers can be wrong';
export const EXPERIMENTAL_DETAILS = [
  'your chat and data live only in server memory, deleted after an hour idle',
  'nothing is saved unless you send feedback',
  'Claude by Anthropic, via Google Cloud Vertex AI in the EU · not used for training',
  "don't paste data you may not share",
  'daily limits apply',
] as const;

/**
 * The consent line under the feedback form, next to `# include data.csv`.
 * The owner reads every user-facing text: keep it in the PR's "Texts to read".
 */
export const FEEDBACK_CONSENT =
  'sending stores this chat, its plots and a 5-row sample of your data for 180 days, for the operator to read; tick the box to add the whole data file.';
