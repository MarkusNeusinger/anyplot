import { describe, expect, it } from 'vitest';

import { AgentApiError } from 'src/lib/agent';
import {
  applyPatch,
  DEFAULT_FILTERS,
  describeCaseError,
  describeFilters,
  filtersToQuery,
  type Triage,
} from 'src/sections/debug/triage';

const BEFORE: Triage = { status: 'new', tags: ['legend'], promoted_at: null, expected: null };

describe('filtersToQuery', () => {
  it('starts from the open queue and leaves every "any" out', () => {
    expect(filtersToQuery(DEFAULT_FILTERS)).toEqual({
      reaction: undefined,
      status: 'open',
      spec: undefined,
      library: undefined,
      model_version: undefined,
      tag: undefined,
      include_superseded: undefined,
    });
  });

  it('passes every set filter', () => {
    expect(
      filtersToQuery({
        reaction: 'bug',
        status: '',
        spec: 'scatter-basic',
        library: 'seaborn',
        model_version: 'm-1',
        tag: 'legend',
        include_superseded: true,
      })
    ).toMatchObject({
      reaction: 'bug',
      status: undefined,
      spec: 'scatter-basic',
      library: 'seaborn',
      model_version: 'm-1',
      tag: 'legend',
      include_superseded: true,
    });
  });
});

describe('describeFilters', () => {
  it('names the active filters for the empty list', () => {
    expect(describeFilters(DEFAULT_FILTERS)).toBe('status "open"');
    expect(describeFilters({ ...DEFAULT_FILTERS, status: '', tag: 'legend' })).toBe('tag "legend"');
    expect(describeFilters({ ...DEFAULT_FILTERS, status: '' })).toBe('');
  });
});

describe('applyPatch', () => {
  it('sets the status and sorts the tags without duplicates', () => {
    expect(applyPatch(BEFORE, 'bug', { status: 'done', tags: ['z', 'a', 'z'] })).toMatchObject({
      status: 'done',
      tags: ['a', 'z'],
    });
  });

  it('stamps a promotion once and fills the outcome from the reaction rule', () => {
    const promoted = applyPatch(BEFORE, 'thumbs_down', { promoted: true });
    expect(promoted.promoted_at).not.toBeNull();
    expect(promoted.expected).toBe('rejected');
    const again = applyPatch(
      { ...BEFORE, promoted_at: '2026-10-12T10:00:00Z', expected: 'accepted' },
      'thumbs_down',
      { promoted: true }
    );
    expect(again).toMatchObject({ promoted_at: '2026-10-12T10:00:00Z', expected: 'accepted' });
  });

  it('keeps the chosen outcome of a bug and clears a promotion with its outcome kept', () => {
    expect(applyPatch(BEFORE, 'bug', { promoted: true, expected: 'accepted' }).expected).toBe(
      'accepted'
    );
    expect(
      applyPatch({ ...BEFORE, promoted_at: 'x', expected: 'accepted' }, 'bug', { promoted: false })
    ).toMatchObject({ promoted_at: null, expected: 'accepted' });
  });
});

describe('describeCaseError', () => {
  it('reads a known code with its ref', () => {
    expect(describeCaseError(new AgentApiError(422, 'no_data', 'r-1'), 'x')).toBe(
      'this case has no data file; the harness cannot run it · ref r-1'
    );
    expect(describeCaseError(new AgentApiError(404, 'not_enabled'), 'x')).toBe(
      'agent chat is not enabled on this server'
    );
  });

  it('names an unknown code and falls back for anything else', () => {
    expect(describeCaseError(new AgentApiError(500, 'http_500'), 'x')).toBe(
      'request failed (http_500)'
    );
    expect(describeCaseError(new TypeError('no headers'), 'failed to load cases')).toBe(
      'failed to load cases'
    );
  });
});
