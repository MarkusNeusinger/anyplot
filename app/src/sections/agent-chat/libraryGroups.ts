/**
 * The library menu's groups (`LibraryChip`): the libraries by the language
 * their code is written in, the catalogue's languages in its order.
 */

import { LIB_TO_LANG } from 'src/constants';

/** The menu's language groups, in the catalogue's order. */
const LANGUAGE_ORDER = ['python', 'r', 'julia', 'javascript'];

/** A library's language, Python for one the catalogue does not list (as the page reads it). */
export const languageOf = (library: string) => LIB_TO_LANG[library] ?? 'python';

export interface LibraryGroup {
  language: string;
  libraries: string[];
}

/**
 * The libraries by language: the four languages in the catalogue's order, the
 * libraries of each in the order given, a language without one left out.
 */
export function groupByLanguage(libraries: readonly string[]): LibraryGroup[] {
  const languages = [
    ...LANGUAGE_ORDER,
    ...new Set(libraries.map(languageOf).filter(lang => !LANGUAGE_ORDER.includes(lang))),
  ];
  return languages
    .map(language => ({
      language,
      libraries: libraries.filter(library => languageOf(library) === language),
    }))
    .filter(group => group.libraries.length > 0);
}
