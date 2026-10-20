import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { BoxWorking } from 'src/sections/agent-chat/BoxWorking';
import { act, render, screen } from 'src/test-utils';

describe('BoxWorking', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('names the step at once and counts the seconds from the first one on', () => {
    render(<BoxWorking line='reading "meter.parquet" on the server' />);
    const line = screen.getByTestId('box-working');
    expect(line).toHaveTextContent(/^# reading "meter\.parquet" on the server …$/);
    expect(line).toHaveAttribute('aria-hidden', 'true');

    act(() => vi.advanceTimersByTime(3000));
    expect(line).toHaveTextContent('# reading "meter.parquet" on the server … · 3 s');
  });
});
