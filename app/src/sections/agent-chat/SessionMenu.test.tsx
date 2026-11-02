import { describe, expect, it, vi } from 'vitest';

import { SessionMenu } from 'src/sections/agent-chat/SessionMenu';
import { render, screen, userEvent, waitFor } from 'src/test-utils';

describe('SessionMenu', () => {
  it('holds .save() behind the "⋯" button, folded until it is opened', async () => {
    const user = userEvent.setup();
    render(<SessionMenu disabled={false} onSave={vi.fn(async () => undefined)} />);

    const button = screen.getByRole('button', { name: 'More actions' });
    expect(button).toHaveAttribute('aria-haspopup', 'dialog');
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();

    await user.click(button);
    expect(screen.getByRole('dialog', { name: 'Save the session' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
    expect(screen.getByRole('checkbox', { name: '# include data.csv' })).toBeChecked();
  });

  it('closes when something else starts, and waits until it ends', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn(async () => undefined);
    const { rerender } = render(<SessionMenu disabled={false} onSave={onSave} />);
    await user.click(screen.getByRole('button', { name: 'More actions' }));
    expect(screen.getByRole('dialog', { name: 'Save the session' })).toBeInTheDocument();

    rerender(<SessionMenu disabled onSave={onSave} />);
    await waitFor(() =>
      expect(screen.queryByRole('dialog', { name: 'Save the session' })).not.toBeInTheDocument()
    );
    expect(screen.getByTestId('session-menu')).toBeDisabled();
  });
});
