/**
 * The language chip's list: the ten languages the site's visitors use most
 * (Plausible, owner's choice of 2026-10-12), in that order; the fixed refusals
 * have hand-written lines for each. Any other language goes through the chip's
 * free-text field. `code` is what the chip sends and what the server stores,
 * `endonym` what the button shows next to the code, `name` the English name its
 * accessible name adds after the visible text.
 */

export interface CommonLanguage {
  code: string;
  endonym: string;
  name: string;
}

export const COMMON_LANGUAGES: readonly CommonLanguage[] = [
  { code: 'en', endonym: 'english', name: 'English' },
  { code: 'zh', endonym: '中文', name: 'Chinese' },
  { code: 'de', endonym: 'deutsch', name: 'German' },
  { code: 'vi', endonym: 'tiếng việt', name: 'Vietnamese' },
  { code: 'es', endonym: 'español', name: 'Spanish' },
  { code: 'fr', endonym: 'français', name: 'French' },
  { code: 'nl', endonym: 'nederlands', name: 'Dutch' },
  { code: 'pt', endonym: 'português', name: 'Portuguese' },
  { code: 'ru', endonym: 'русский', name: 'Russian' },
  { code: 'it', endonym: 'italiano', name: 'Italian' },
];
