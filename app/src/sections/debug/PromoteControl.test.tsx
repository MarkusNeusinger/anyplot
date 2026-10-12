import { describe, expect, it, vi } from 'vitest';

import type { FeedbackReaction } from 'src/lib/agent';
import { PromoteControl, PROMOTION_HINT } from 'src/sections/debug/PromoteControl';
import { render, screen, userEvent } from 'src/test-utils';

function setup(
  reaction: FeedbackReaction,
  props: Partial<{
    expected: 'accepted' | 'rejected' | null;
    promotedAt: string | null;
    includeData: boolean;
    busy: boolean;
  }> = {}
) {
  const onPatch = vi.fn();
  render(
    <PromoteControl
      reaction={reaction}
      expected={props.expected ?? null}
      promotedAt={props.promotedAt ?? null}
      includeData={props.includeData ?? true}
      busy={props.busy ?? false}
      onPatch={onPatch}
    />
  );
  return { onPatch, select: screen.getByLabelText('Expected outcome') };
}

describe('PromoteControl', () => {
  it('preselects the reaction rule for the thumbs and promotes with it', async () => {
    const user = userEvent.setup();
    const { onPatch, select } = setup('thumbs_down');
    expect(select).toHaveValue('rejected');
    await user.click(screen.getByRole('button', { name: 'Promote to an eval case' }));
    expect(onPatch).toHaveBeenCalledWith({ promoted: true, expected: 'rejected' });
  });

  it('needs a choice for a bug, then sends it with the promotion', async () => {
    const user = userEvent.setup();
    const { onPatch, select } = setup('bug');
    const promote = screen.getByRole('button', { name: 'Promote to an eval case' });
    expect(select).toHaveValue('');
    expect(promote).toBeDisabled();
    await user.selectOptions(select, 'accepted');
    // Changing the outcome alone stores it.
    expect(onPatch).toHaveBeenCalledWith({ expected: 'accepted' });
    expect(promote).toBeEnabled();
    await user.click(promote);
    expect(onPatch).toHaveBeenLastCalledWith({ promoted: true, expected: 'accepted' });
  });

  it('shows a promotion with its date and takes it back', async () => {
    const user = userEvent.setup();
    const { onPatch, select } = setup('idea', {
      expected: 'rejected',
      promotedAt: '2026-10-12T14:30:05Z',
    });
    expect(screen.getByText('promoted 2026-10-12 14:30:05 UTC')).toBeInTheDocument();
    // No empty choice once promoted.
    expect(Array.from((select as HTMLSelectElement).options).map(option => option.value)).toEqual([
      'accepted',
      'rejected',
    ]);
    await user.click(screen.getByRole('button', { name: 'Take back the promotion' }));
    expect(onPatch).toHaveBeenCalledWith({ promoted: false });
  });

  it('cannot promote a case without data and says why', () => {
    setup('thumbs_down', { includeData: false });
    expect(screen.getByRole('button', { name: 'Promote to an eval case' })).toBeDisabled();
    expect(screen.getByText('no data file: the harness cannot run this case')).toBeInTheDocument();
  });

  it('shows the promotion rule as guidance', () => {
    setup('thumbs_up');
    expect(screen.getByText(PROMOTION_HINT)).toBeInTheDocument();
  });
});
