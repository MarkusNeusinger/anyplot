export type FeedbackStatus = 'new' | 'in_progress' | 'done' | 'wont_solve';
export type FeedbackMessageFilter = '' | 'open' | 'new' | 'in_progress' | 'done' | 'wont_solve';
export const FEEDBACK_STATUS_OPTIONS = ['new', 'in_progress', 'done', 'wont_solve'] as const;
