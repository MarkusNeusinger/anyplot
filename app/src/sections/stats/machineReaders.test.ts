import { describe, expect, it } from 'vitest';

import { readMachineReaders } from 'src/sections/stats/machineReaders';

describe('readMachineReaders', () => {
  it('reads an ok answer and floors bad counts to zero', () => {
    const answer = readMachineReaders({
      status: 'ok',
      days: 28,
      points: [
        { date: '2026-11-09', for_person: 2, index_training: -1, search: '3', mcp: 4.7 },
        { nodate: true },
      ],
      totals: { for_person: 2, unverified: 26 },
      generated_at: '2026-11-09T13:50:00Z',
    });
    expect(answer?.points).toEqual([
      { date: '2026-11-09', for_person: 2, index_training: 0, search: 0, mcp: 4 },
    ]);
    expect(answer?.totals).toEqual({
      for_person: 2,
      index_training: 0,
      search: 0,
      mcp: 0,
      unverified: 26,
    });
  });

  it('refuses anything but an ok answer with days', () => {
    expect(readMachineReaders(null)).toBeNull();
    expect(readMachineReaders({ status: 'unavailable', points: [] })).toBeNull();
    expect(readMachineReaders({ status: 'ok', points: [] })).toBeNull();
    expect(readMachineReaders({ status: 'ok', points: 'nope' })).toBeNull();
  });
});
