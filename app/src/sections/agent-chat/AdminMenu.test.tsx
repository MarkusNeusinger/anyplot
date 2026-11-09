import { describe, expect, it, vi } from 'vitest';

import { AgentApiError } from 'src/lib/agent';
import {
  AdminMenu,
  type AdminMenuProps,
  AdminMeters,
  AdminSection,
} from 'src/sections/agent-chat/AdminMenu';
import { render, screen, userEvent, waitFor, within } from 'src/test-utils';

const MENU = { name: 'Admin' } as const;
const button = () => screen.getByTestId('admin-menu');

function props(overrides: Partial<AdminMenuProps> = {}): AdminMenuProps {
  return {
    mode: 'admin',
    onViewAsVisitor: vi.fn(),
    fanOut: { libraries: 15, pressed: false, disabled: false, onChange: vi.fn() },
    save: { disabled: false, onSave: vi.fn(async () => undefined) },
    ...overrides,
  };
}

describe('AdminMenu', () => {
  it('holds the fan-out, .save() and "view as visitor" behind one button, folded until opened', async () => {
    const user = userEvent.setup();
    render(<AdminMenu {...props()} />);

    expect(button()).toHaveTextContent(/^admin ▾$/);
    expect(button()).toHaveAccessibleName('admin');
    expect(button()).toHaveAttribute('aria-haspopup', 'dialog');
    expect(button()).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('dialog', MENU)).not.toBeInTheDocument();

    await user.click(button());
    const menu = screen.getByRole('dialog', MENU);
    expect(within(menu).getByRole('button', { name: 'all 15 libraries' })).toHaveAttribute(
      'aria-pressed',
      'false'
    );
    expect(within(menu).getByRole('button', { name: 'Save' })).toBeEnabled();
    // Unticked, as the feedback form's box: the admin's chat is the visitors'.
    expect(within(menu).getByRole('checkbox', { name: '# include data.csv' })).not.toBeChecked();
    expect(within(menu).getByRole('button', { name: 'view as visitor' })).toHaveAttribute(
      'aria-pressed',
      'false'
    );
  });

  it('toggles the fan-out and closes, the focus back on its button', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const { rerender } = render(
      <AdminMenu
        {...props({ fanOut: { libraries: 2, pressed: false, disabled: false, onChange } })}
      />
    );
    await user.click(button());
    await user.click(screen.getByRole('button', { name: 'all 2 libraries' }));
    expect(onChange).toHaveBeenCalledWith(true);
    await waitFor(() => expect(screen.queryByRole('dialog', MENU)).not.toBeInTheDocument());
    await waitFor(() => expect(button()).toHaveFocus());

    rerender(
      <AdminMenu
        {...props({ fanOut: { libraries: 2, pressed: true, disabled: false, onChange } })}
      />
    );
    await user.click(button());
    const all = screen.getByRole('button', { name: 'all 2 libraries' });
    expect(all).toHaveAttribute('aria-pressed', 'true');
    await user.click(all);
    expect(onChange).toHaveBeenLastCalledWith(false);
  });

  it('holds the fan-out while something runs, and leaves out what the lane does not offer', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <AdminMenu
        {...props({
          fanOut: { libraries: 15, pressed: false, disabled: true, onChange: vi.fn() },
          save: { disabled: true, onSave: vi.fn(async () => undefined) },
        })}
      />
    );
    // The button itself never waits: the way back from the visitor's view stays reachable.
    expect(button()).toBeEnabled();
    await user.click(button());
    expect(screen.getByRole('button', { name: 'all 15 libraries' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'view as visitor' })).toBeEnabled();

    rerender(<AdminMenu {...props({ fanOut: null, save: null })} />);
    const menu = screen.getByRole('dialog', MENU);
    expect(within(menu).queryByRole('button', { name: /libraries/ })).not.toBeInTheDocument();
    expect(within(menu).queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
  });

  it("switches to the visitor's view and back, and says which one is on", async () => {
    const user = userEvent.setup();
    const onViewAsVisitor = vi.fn();
    const { rerender } = render(<AdminMenu {...props({ onViewAsVisitor })} />);
    await user.click(button());
    await user.click(screen.getByRole('button', { name: 'view as visitor' }));
    expect(onViewAsVisitor).toHaveBeenCalledWith(true);
    await waitFor(() => expect(screen.queryByRole('dialog', MENU)).not.toBeInTheDocument());

    // The public lane has no fan-out and no `.save()`: the page hands neither.
    rerender(
      <AdminMenu {...props({ mode: 'visitor', fanOut: null, save: null, onViewAsVisitor })} />
    );
    expect(button()).toHaveTextContent(/^admin · as visitor ▾$/);
    await user.click(button());
    const view = screen.getByRole('button', { name: 'view as visitor' });
    expect(view).toHaveAttribute('aria-pressed', 'true');
    await user.click(view);
    expect(onViewAsVisitor).toHaveBeenLastCalledWith(false);
  });

  it('says an expired admin session expired and links to /debug in a new tab', async () => {
    const user = userEvent.setup();
    render(
      <AdminMenu
        {...props({ mode: 'expired', failure: 'unreachable', fanOut: null, save: null })}
      />
    );
    expect(button()).toHaveTextContent(/^admin · expired ▾$/);
    await user.click(button());
    const menu = screen.getByRole('dialog', MENU);
    expect(within(menu).getByTestId('admin-expired')).toHaveTextContent(
      "the chat runs as a visitor's. sign in again on /debug, then reload this page."
    );
    const link = within(menu).getByRole('link', { name: '/debug' });
    expect(link).toHaveAttribute('href', '/debug');
    expect(link).toHaveAttribute('target', '_blank');
    expect(menu).toHaveTextContent('# the check answered unreachable');
    // Nothing to switch: the admin lane refuses until the next sign-in.
    expect(within(menu).queryByRole('button')).not.toBeInTheDocument();
  });

  it('shows the diagnostics and later extras inside the menu only', async () => {
    const user = userEvent.setup();
    render(
      <AdminMenu {...props({ diagnostics: ['not_enabled · AGENT_ENABLED is off'] })}>
        <AdminSection heading="later">a meter</AdminSection>
      </AdminMenu>
    );
    // Mounted while closed (for the data box), but out of sight and out of the accessibility tree.
    expect(screen.queryByRole('region', { name: 'diagnostics' })).not.toBeInTheDocument();
    await user.click(button());
    const menu = screen.getByRole('dialog', MENU);
    expect(within(menu).getByRole('region', { name: 'diagnostics' })).toHaveTextContent(
      'not_enabled · AGENT_ENABLED is off'
    );
    expect(within(menu).getByRole('region', { name: 'later' })).toHaveTextContent('a meter');
  });

  it('names the grid and the meters in its title, and says when it opens', async () => {
    const user = userEvent.setup();
    const onOpen = vi.fn();
    render(
      <AdminMenu {...props({ onOpen })}>
        <AdminSection heading="load · runs in flight, today's budget">
          <AdminMeters runs={2} share={62} />
        </AdminSection>
      </AdminMenu>
    );
    expect(button()).toHaveAttribute(
      'title',
      "admin only · the fan-out, .save(), the visitor's view, the progress grid and the meters"
    );
    expect(onOpen).not.toHaveBeenCalled();
    await user.click(button());
    expect(onOpen).toHaveBeenCalledTimes(1);
    const meters = within(screen.getByRole('dialog', MENU)).getByTestId('admin-meters');
    expect(meters).toHaveTextContent(/^now 2 runs · today 62 %$/);
  });

  it('reads the meters in counts, one run as one, and a dash for what is not read', () => {
    const { rerender } = render(<AdminMeters runs={1} share={0} />);
    expect(screen.getByTestId('admin-meters')).toHaveTextContent(/^now 1 run · today 0 %$/);
    rerender(<AdminMeters runs={null} share={null} />);
    expect(screen.getByTestId('admin-meters')).toHaveTextContent(/^now — · today —$/);
  });

  it('keeps the data box across closing and drops a failure line once it closes', async () => {
    const user = userEvent.setup();
    const onSave = vi
      .fn<(includeData: boolean) => Promise<void>>()
      .mockRejectedValue(new AgentApiError(413, 'too_large', 'r-big'));
    render(<AdminMenu {...props({ save: { disabled: false, onSave } })} />);
    await user.click(button());
    await user.click(screen.getByRole('checkbox', { name: '# include data.csv' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));
    expect(onSave).toHaveBeenCalledWith(true);
    expect(await screen.findByRole('alert')).toHaveTextContent('too large for one file');

    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog', MENU)).not.toBeInTheDocument());
    expect(button()).toHaveFocus();
    await user.click(button());
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: '# include data.csv' })).toBeChecked();
  });
});
