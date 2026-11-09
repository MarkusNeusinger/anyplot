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

const commonLanguage = (language: string) =>
  COMMON_LANGUAGES.find(option => option.code === language.toLowerCase());

/** Whether two stored forms name the same language (`de` and `DE`; the server stores codes in lower case). */
export const sameLanguage = (a: string, b: string) => a.toLowerCase() === b.toLowerCase();

/**
 * How the page names a language in its own words: the endonym from the list, each word
 * capitalised as the language writes its own name (`Deutsch`, `Tiếng Việt`, `中文`), else the
 * value as the server stored it, which may be any language a visitor typed.
 */
export function languageLabel(language: string): string {
  const known = commonLanguage(language);
  if (!known) return language;
  return known.endonym
    .split(' ')
    .map(word => word.charAt(0).toLocaleUpperCase(known.code) + word.slice(1))
    .join(' ');
}

/**
 * The English name of a language, as the offer line names it (`German`): from the list, else the
 * browser's own name for a two-letter code (`sv` is `Swedish`), else the value as stored.
 */
export function englishName(language: string): string {
  const known = commonLanguage(language);
  if (known) return known.name;
  if (/^[a-z]{2}$/i.test(language) && typeof Intl !== 'undefined' && 'DisplayNames' in Intl) {
    try {
      const name = new Intl.DisplayNames(['en'], { type: 'language' }).of(language.toLowerCase());
      if (name && name.toLowerCase() !== language.toLowerCase()) return name;
    } catch {
      // A code the browser does not know: the value as stored.
    }
  }
  return language;
}
