import { describe, expect, it } from 'vitest';

import { platformLabel, readSharedLinks } from 'src/sections/stats/sharedLinks';

const DAYS = Array.from({ length: 28 }, (_, index) => ({
  date: new Date(Date.UTC(2026, 9, 15 + index)).toISOString().slice(0, 10),
  shares: index === 27 ? 5 : 0,
}));

const ANSWER = {
  status: 'ok',
  window_days: 28,
  total: 5,
  days: DAYS,
  platforms: [
    { platform: 'whatsapp', shares: 3 },
    { platform: 'teams', shares: 2 },
  ],
  top: [
    { spec_id: 'scatter-basic', language: 'python', library: 'matplotlib', shares: 3 },
    { spec_id: 'scatter-basic', language: null, library: null, shares: 2 },
  ],
};

describe('readSharedLinks', () => {
  it('reads an ok answer as it is', () => {
    expect(readSharedLinks(ANSWER)).toEqual(ANSWER);
  });

  it.each([
    ['no body', null],
    ['a string', 'ok'],
    ['not configured', { ...ANSWER, status: 'not_configured' }],
    ['unavailable', { ...ANSWER, status: 'unavailable' }],
    ['no days', { ...ANSWER, days: [] }],
    ['days that are no list', { ...ANSWER, days: 'none' }],
    // The stats page's other answers, should one ever arrive under this address.
    ['another answer', { points: [{ date: '2026-11-11', visitors: 3 }] }],
  ])('refuses %s', (_, body) => {
    expect(readSharedLinks(body)).toBeNull();
  });

  it('turns a number that is none into zero and drops an entry without a name', () => {
    const answer = readSharedLinks({
      ...ANSWER,
      total: 'many',
      days: [{ date: '2026-11-11', shares: -4 }, { shares: 2 }, null],
      platforms: [
        { platform: 'slack', shares: 2.9 },
        { platform: '', shares: 4 },
        { shares: 4 },
        { platform: 'mastodon', shares: 0 },
      ],
      top: [
        { spec_id: 'heatmap-basic', language: '', library: '', shares: 1 },
        { language: 'python', shares: 9 },
      ],
    });

    expect(answer).toMatchObject({
      total: 0,
      days: [{ date: '2026-11-11', shares: 0 }],
      // A platform without a share is no entry: the line lists who shared.
      platforms: [{ platform: 'slack', shares: 2 }],
      // An empty language or library is none: the entry is the spec's hub.
      top: [{ spec_id: 'heatmap-basic', language: null, library: null, shares: 1 }],
    });
  });
});

describe('platformLabel', () => {
  it('names an app that signs as WhatsApp without its version for what it mostly is', () => {
    expect(platformLabel('whatsapp-lite')).toBe('signal & similar');
  });

  it('shows every other platform by its stored name', () => {
    expect(platformLabel('whatsapp')).toBe('whatsapp');
    expect(platformLabel('teams')).toBe('teams');
  });
});
