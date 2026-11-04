import { describe, expect, it } from 'vitest';

import type { AgentCaseRound } from 'src/lib/agent';
import { roundLine, sessionLine } from 'src/sections/debug/caseRounds';

const round = (overrides: Partial<AgentCaseRound> = {}): AgentCaseRound => ({
  attempt: 1,
  outcome: 'ok',
  findings: 0,
  step: 'reviewing',
  shipped: false,
  defects: [],
  gates_failed: [],
  sandbox_failures: [],
  ...overrides,
});

describe('roundLine', () => {
  it('names a crashed round by its gate and its sandbox class', () => {
    expect(
      roundLine(
        round({
          outcome: 'render_failed',
          step: 'rendering',
          findings: 1,
          gates_failed: ['R1'],
          sandbox_failures: ['key'],
        })
      )
    ).toBe('round 1: render_failed at rendering · 1 finding · gates R1 · crash key');
  });

  it('names the rubric ids and the shipped round', () => {
    expect(
      roundLine(
        round({
          attempt: 2,
          outcome: 'review',
          findings: 2,
          defects: ['VQ-03', 'VQ-05'],
          gates_failed: ['G7', 'R3'],
          shipped: true,
        })
      )
    ).toBe('round 2: review at reviewing · 2 findings · VQ-03 VQ-05 · gates G7 R3 · shipped');
  });

  it('leaves out what a clean round lacks', () => {
    expect(roundLine(round({ step: null }))).toBe('round 1: ok');
  });
});

describe('sessionLine', () => {
  it('is null for a case from before the fields', () => {
    expect(sessionLine(undefined, undefined)).toBeNull();
    expect(sessionLine(null, null)).toBeNull();
  });

  it('says when the session ran no plot', () => {
    expect(sessionLine(0, null)).toBe('session: 0 versions · no plot run');
  });

  it('names the latest run and the version it stored', () => {
    expect(sessionLine(1, { status: 'ok', reason: null, version: 1, turn: 3, rounds: [] })).toBe(
      'session: 1 version · latest run (turn 3): ok · stored v1'
    );
    expect(
      sessionLine(2, { status: 'failed', reason: 'render', version: null, turn: null, rounds: [] })
    ).toBe('session: 2 versions · latest run: failed, render · stored no version');
  });
});
