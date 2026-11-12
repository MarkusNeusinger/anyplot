import { describe, expect, it } from 'vitest';

import {
  byVerdict,
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
    { platform: 'whatsapp', shares: 3, verified: 0 },
    { platform: 'teams', shares: 2, verified: 2 },
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
      platforms: ANSWER.platforms.map(({ platform, shares }) => ({ platform, shares })),
      top: [{ spec_id: 'scatter-basic', language: null, library: null, shares: 5 }],
    };
    expect(readSharedLinks(older)).toEqual({
      ...ANSWER,
      // The same revision named no verdict either.
      platforms: ANSWER.platforms.map(entry => ({ ...entry, verified: null })),
      top_specs: [],
      top_libraries: [],
    });
  });

  it('reads a verified part as at most the shares, and anything but a number as no verdict', () => {
    const answer = readSharedLinks({
      ...ANSWER,
      platforms: [
        { platform: 'teams', shares: 5, verified: 9 },
        { platform: 'slack', shares: 3, verified: 1.8 },
        { platform: 'discord', shares: 2, verified: -1 },
        { platform: 'whatsapp', shares: 2, verified: 'none' },
        // An API revision older than the page names no verdict at all.
        { platform: 'telegram', shares: 1 },
      ],
    });

    expect(answer?.platforms).toEqual([
      { platform: 'teams', shares: 5, verified: 5 },
      { platform: 'slack', shares: 3, verified: 1 },
      { platform: 'discord', shares: 2, verified: 0 },
      { platform: 'whatsapp', shares: 2, verified: null },
      { platform: 'telegram', shares: 1, verified: null },
    ]);
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

describe('byVerdict', () => {
  it('gives every platform its verified part, largest first, and sums the rest', () => {
    expect(
      byVerdict([
        { platform: 'whatsapp', shares: 300, verified: 0 },
        { platform: 'slack', shares: 60, verified: 60 },
        { platform: 'teams', shares: 1200, verified: 1150 },
      ])
    ).toEqual({
      // WhatsApp has no verified share and so no entry; Teams leads by its verified part.
      verified: [
        { platform: 'teams', shares: 1150 },
        { platform: 'slack', shares: 60 },
      ],
      // WhatsApp's 300 and the 50 of Teams that came without a verdict.
      unverified: 350,
    });
  });

  it('keeps the answer’s order between platforms with the same part', () => {
    const lines = byVerdict([
      { platform: 'linkedin', shares: 4, verified: 4 },
      { platform: 'whatsapp', shares: 4, verified: 0 },
      { platform: 'discord', shares: 4, verified: 4 },
    ]);

    expect(lines?.verified.map(entry => entry.platform)).toEqual(['linkedin', 'discord']);
  });

  it('is no platform and no rest for a window without a share', () => {
    expect(byVerdict([])).toEqual({ verified: [], unverified: 0 });
  });

  it('is null as soon as one platform comes without a verdict', () => {
    expect(
      byVerdict([
        { platform: 'teams', shares: 2, verified: 2 },
        { platform: 'whatsapp', shares: 1, verified: null },
      ])
    ).toBeNull();
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
      other_verified: 2,
    });

    expect(detail).toMatchObject({
      top_specs: ANSWER.top_specs,
      top: [
        { spec_id: 'heatmap-basic', language: null, library: null, shares: 1 },
        { spec_id: 'scatter-basic', language: 'python', library: 'matplotlib', shares: 3 },
      ],
      other: 7,
      other_verified: 2,
    });
  });

  it('reads an answer without the pages as one with none', () => {
    expect(readSharedLinksDetail(ANSWER)).toMatchObject({
      top: [],
      other: 0,
      other_verified: null,
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
