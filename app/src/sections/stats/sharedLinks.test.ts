import { describe, expect, it } from 'vitest';

import {
  platformLabel,
  readSharedLinks,
  readSharedLinksDetail,
} from 'src/sections/stats/sharedLinks';

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
  top_specs: [{ spec_id: 'scatter-basic', shares: 5 }],
  top_libraries: [{ library: 'matplotlib', shares: 3 }],
};

describe('readSharedLinks', () => {
  it('reads an ok answer as it is', () => {
    expect(readSharedLinks(ANSWER)).toEqual(ANSWER);
  });

  it('reads an answer without the two lists as one with empty lists', () => {
    // An API revision older than the page: the bars and the platforms still show.
    const older = {
      status: ANSWER.status,
      window_days: ANSWER.window_days,
      total: ANSWER.total,
      days: ANSWER.days,
      platforms: ANSWER.platforms,
      top: [{ spec_id: 'scatter-basic', language: null, library: null, shares: 5 }],
    };
    expect(readSharedLinks(older)).toEqual({ ...ANSWER, top_specs: [], top_libraries: [] });
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
      top_specs: [
        { spec_id: 'heatmap-basic', shares: 1.5 },
        { shares: 9 },
        { spec_id: '', shares: 3 },
      ],
      top_libraries: [
        { library: 'ggplot2', shares: 2 },
        { library: 'plotly', shares: 0 },
        { spec_id: 'heatmap-basic', shares: 4 },
      ],
    });

    expect(answer).toMatchObject({
      total: 0,
      days: [{ date: '2026-11-11', shares: 0 }],
      // A platform without a share is no entry: the line lists who shared.
      platforms: [{ platform: 'slack', shares: 2 }],
      top_specs: [{ spec_id: 'heatmap-basic', shares: 1 }],
      top_libraries: [{ library: 'ggplot2', shares: 2 }],
    });
  });
});

describe('readSharedLinksDetail', () => {
  it('adds the plot pages one by one: an empty language or library is the hub', () => {
    const detail = readSharedLinksDetail({
      ...ANSWER,
      top: [
        { spec_id: 'heatmap-basic', language: '', library: '', shares: 1 },
        { spec_id: 'scatter-basic', language: 'python', library: 'matplotlib', shares: 3 },
        { language: 'python', shares: 9 },
      ],
      other: 7,
      verified: { teams: 2 },
    });

    expect(detail).toMatchObject({
      top_specs: ANSWER.top_specs,
      top: [
        { spec_id: 'heatmap-basic', language: null, library: null, shares: 1 },
        { spec_id: 'scatter-basic', language: 'python', library: 'matplotlib', shares: 3 },
      ],
      other: 7,
      verified: { teams: 2 },
    });
  });

  it('reads an answer without the pages as one with none', () => {
    expect(readSharedLinksDetail(ANSWER)).toMatchObject({ top: [], other: 0, verified: {} });
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
