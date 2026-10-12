/**
 * The language chip's list: the eight languages the fixed refusals have lines
 * for, plus Chinese and Japanese (the owner's ten). Any other language goes
 * through the chip's free-text field. `code` is what the chip sends and what
 * the server stores, `endonym` what the button shows, `name` its `aria-label`.
 */

export interface CommonLanguage {
  code: string;
  endonym: string;
  name: string;
}

export const COMMON_LANGUAGES: readonly CommonLanguage[] = [
  { code: 'en', endonym: 'english', name: 'English' },
  { code: 'de', endonym: 'deutsch', name: 'German' },
  { code: 'fr', endonym: 'français', name: 'French' },
  { code: 'es', endonym: 'español', name: 'Spanish' },
  { code: 'it', endonym: 'italiano', name: 'Italian' },
  { code: 'pt', endonym: 'português', name: 'Portuguese' },
  { code: 'nl', endonym: 'nederlands', name: 'Dutch' },
  { code: 'pl', endonym: 'polski', name: 'Polish' },
  { code: 'zh', endonym: '中文', name: 'Chinese' },
  { code: 'ja', endonym: '日本語', name: 'Japanese' },
];
