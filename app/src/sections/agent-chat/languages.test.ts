import { describe, expect, it } from 'vitest';

import { englishName, languageLabel, sameLanguage } from 'src/sections/agent-chat/languages';
import {
  languageAcceptedLine,
  languageOfferLine,
  languageSwitchLabel,
} from 'src/sections/agent-chat/messages';

describe('the language names', () => {
  it('names a language in its own words, as the chip does', () => {
    expect(languageLabel('de')).toBe('Deutsch');
    expect(languageLabel('DE')).toBe('Deutsch');
    expect(languageLabel('vi')).toBe('Tiếng Việt');
    expect(languageLabel('Klingon')).toBe('Klingon');
  });

  it('names a language in English: from the list, else the browser’s name for a code, else as stored', () => {
    expect(englishName('de')).toBe('German');
    expect(englishName('sv')).toBe('Swedish');
    expect(englishName('Klingon')).toBe('Klingon');
    expect(englishName('qq')).toBe('qq'); // a code no browser names
  });

  it('compares the stored forms without case', () => {
    expect(sameLanguage('de', 'DE')).toBe(true);
    expect(sameLanguage('de', 'en')).toBe(false);
  });
});

describe('the language line', () => {
  it('names where the language was found, and keeps the rest behind its ⓘ', () => {
    expect(languageOfferLine('de', 'message', 'en')).toEqual({
      text: 'German detected in your message',
      info: {
        label: 'About the language offer',
        heading: '# language',
        lines: [
          'replies and plot labels in German',
          'until then everything stays English',
          'the menu at the top changes it any time',
        ],
      },
    });
    // After German was taken, English may come back: everything stays German until then.
    expect(languageOfferLine('en', 'data', 'de')).toMatchObject({
      text: 'English detected in your data',
      info: { lines: expect.arrayContaining(['until then everything stays German']) },
    });
  });

  it('names the language it set once taken, and the next plot version when a plot is on screen', () => {
    expect(languageAcceptedLine('de', false)).toBe('replies and plot labels: Deutsch');
    expect(languageAcceptedLine('de', true)).toBe(
      'replies and plot labels: Deutsch · the next plot version uses it'
    );
    expect(languageSwitchLabel('fr')).toBe('Reply and label the plot in French');
  });
});
