import { describe, expect, it, vi } from 'vitest';

import { AgentApiError } from 'src/lib/agent';
import { LibraryChip, type LibraryChipProps } from 'src/sections/agent-chat/LibraryChip';
import { groupByLanguage } from 'src/sections/agent-chat/libraryGroups';
import { render, screen, userEvent, waitFor, within } from 'src/test-utils';

function deferred() {
  let resolve!: () => void;
  let reject!: (err: unknown) => void;
  const promise = new Promise<void>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

/** Every library of the catalogue, in the order the agents service lists them. */
const ALL_FIFTEEN = [
  'matplotlib',
  'seaborn',
  'plotly',
  'bokeh',
  'altair',
  'plotnine',
  'pygal',
  'highcharts',
  'letsplot',
  'ggplot2',
  'makie',
  'chartjs',
  'd3',
  'echarts',
  'muix',
];

const chip = () => screen.getByTestId('library-chip');
const dialog = () => screen.getByRole('dialog', { name: 'Library of the plot' });

function props(overrides: Partial<LibraryChipProps> = {}): LibraryChipProps {
  return {
    library: 'matplotlib',
    libraries: ALL_FIFTEEN,
    offerAll: false,
    allPressed: false,
    disabled: false,
    onPick: vi.fn(async () => undefined),
    onAllChange: vi.fn(),
    ...overrides,
  };
}

describe('groupByLanguage', () => {
  it('groups the libraries by language in the catalogue order, each in the order given', () => {
    expect(groupByLanguage(ALL_FIFTEEN)).toEqual([
      {
        language: 'python',
        libraries: [
          'matplotlib',
          'seaborn',
          'plotly',
          'bokeh',
          'altair',
          'plotnine',
          'pygal',
          'letsplot',
        ],
      },
      { language: 'r', libraries: ['ggplot2'] },
      { language: 'julia', libraries: ['makie'] },
      { language: 'javascript', libraries: ['highcharts', 'chartjs', 'd3', 'echarts', 'muix'] },
    ]);
  });

  it('leaves a language without a library out', () => {
    expect(groupByLanguage(['seaborn', 'matplotlib'])).toEqual([
      { language: 'python', libraries: ['seaborn', 'matplotlib'] },
    ]);
  });
});

describe('LibraryChip', () => {
  it('names the library and its language, and is disabled while the page says so', () => {
    const { rerender } = render(<LibraryChip {...props({ disabled: true })} />);
    expect(chip()).toHaveTextContent(/^lib: matplotlib · python$/);
    expect(chip()).toBeDisabled();
    expect(chip()).toHaveAccessibleName('Library: matplotlib, Python. Change');
    expect(chip()).toHaveAttribute('aria-haspopup', 'dialog');

    rerender(<LibraryChip {...props({ library: 'ggplot2' })} />);
    expect(chip()).toHaveTextContent(/^lib: ggplot2 · r$/);
    expect(chip()).toBeEnabled();

    rerender(<LibraryChip {...props({ offerAll: true, allPressed: true })} />);
    expect(chip()).toHaveTextContent(/^lib: all · 15 libraries$/);
    expect(chip()).toHaveAccessibleName('Library: all 15 libraries. Change');
  });

  it('announces each change of the library or of all once, and nothing on mount', () => {
    const { rerender } = render(<LibraryChip {...props()} />);
    expect(screen.getByRole('status')).toHaveTextContent('');
    rerender(<LibraryChip {...props({ library: 'plotly' })} />);
    expect(screen.getByRole('status')).toHaveTextContent('library: plotly');
    rerender(<LibraryChip {...props({ library: 'plotly', offerAll: true, allPressed: true })} />);
    expect(screen.getByRole('status')).toHaveTextContent('library: all libraries');
  });

  it('opens the libraries grouped by language with the one in use pressed; Escape returns the focus', async () => {
    const user = userEvent.setup();
    const onPick = vi.fn(async () => undefined);
    render(<LibraryChip {...props({ onPick })} />);

    await user.click(chip());
    expect(chip()).toHaveAttribute('aria-expanded', 'true');
    const groups = within(dialog()).getAllByRole('group');
    expect(groups.map(group => group.getAttribute('aria-label'))).toEqual([
      'Python',
      'R',
      'Julia',
      'JavaScript',
    ]);
    expect(
      within(groups[3])
        .getAllByRole('button')
        .map(button => button.textContent)
    ).toEqual(['highcharts', 'chartjs', 'd3', 'echarts', 'muix']);
    // The library in use cannot be picked again.
    const own = within(groups[0]).getByRole('button', { name: 'matplotlib' });
    expect(own).toHaveAttribute('aria-pressed', 'true');
    expect(own).toBeDisabled();
    expect(within(groups[1]).getByRole('button', { name: 'ggplot2' })).toHaveAttribute(
      'aria-pressed',
      'false'
    );
    // Without the admin's offer there is no `all`.
    expect(within(dialog()).queryByRole('button', { name: 'All libraries' })).toBeNull();

    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    await waitFor(() => expect(chip()).toHaveFocus());
    expect(onPick).not.toHaveBeenCalled();
  });

  it('switches to a picked library and closes the menu, focus back on the chip', async () => {
    const user = userEvent.setup();
    const onPick = vi.fn(async () => undefined);
    render(<LibraryChip {...props({ onPick })} />);

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: 'ggplot2' }));
    expect(onPick).toHaveBeenCalledWith('ggplot2');
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    await waitFor(() => expect(chip()).toHaveFocus());
  });

  it('offers all to the admin as a toggle, after the libraries', async () => {
    const user = userEvent.setup();
    const onAllChange = vi.fn();
    const onPick = vi.fn(async () => undefined);
    const { rerender } = render(
      <LibraryChip {...props({ offerAll: true, onAllChange, onPick })} />
    );

    await user.click(chip());
    const admin = within(dialog()).getByRole('group', { name: 'Admin' });
    const all = within(admin).getByRole('button', { name: 'All libraries' });
    expect(all).toHaveTextContent('all libraries');
    expect(all).toHaveAttribute('aria-pressed', 'false');
    // After every language group.
    const groups = within(dialog()).getAllByRole('group');
    expect(groups[groups.length - 1]).toBe(admin);
    await user.click(all);
    expect(onAllChange).toHaveBeenCalledWith(true);
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());

    // Pressed: the library in use can be picked, which the page reads as `all` off.
    rerender(<LibraryChip {...props({ offerAll: true, allPressed: true, onAllChange, onPick })} />);
    await user.click(chip());
    expect(within(dialog()).getByRole('button', { name: 'All libraries' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    const own = within(dialog()).getByRole('button', { name: 'matplotlib' });
    expect(own).toHaveAttribute('aria-pressed', 'false');
    expect(own).toBeEnabled();
    await user.click(own);
    expect(onPick).toHaveBeenCalledWith('matplotlib');

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: 'All libraries' }));
    expect(onAllChange).toHaveBeenLastCalledWith(false);
  });

  it('makes the other libraries links where there is no session to switch', async () => {
    const user = userEvent.setup();
    const onPick = vi.fn(async () => undefined);
    render(
      <LibraryChip
        {...props({
          libraries: ['matplotlib', 'seaborn', 'ggplot2'],
          hrefFor: lib => `/debug/agent?spec=scatter-basic&library=${lib}`,
          onPick,
        })}
      />
    );
    await user.click(chip());
    expect(within(dialog()).getByRole('link', { name: 'ggplot2' })).toHaveAttribute(
      'href',
      '/debug/agent?spec=scatter-basic&library=ggplot2'
    );
    expect(within(dialog()).getByRole('link', { name: 'seaborn' })).toBeInTheDocument();
    expect(within(dialog()).getByRole('button', { name: 'matplotlib' })).toBeDisabled();
    expect(onPick).not.toHaveBeenCalled();
  });

  it('shows the switch in progress, keeps the focus and opens nothing meanwhile', async () => {
    const user = userEvent.setup();
    const gate = deferred();
    const onPick = vi.fn(() => gate.promise);
    const { rerender } = render(<LibraryChip {...props({ onPick })} />);
    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: 'plotly' }));
    // The page disables the chip while the switch runs (`libraryBusy`).
    rerender(<LibraryChip {...props({ onPick, disabled: true })} />);

    await waitFor(() => expect(chip()).toHaveFocus());
    expect(chip()).toHaveTextContent(/^lib: matplotlib · python …$/);
    expect(chip()).toHaveAttribute('aria-disabled', 'true');
    expect(chip()).not.toBeDisabled();
    await user.click(chip());
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    gate.resolve();
    rerender(<LibraryChip {...props({ onPick, library: 'plotly' })} />);
    await waitFor(() => expect(chip()).not.toHaveAttribute('aria-disabled'));
    expect(chip()).toHaveTextContent(/^lib: plotly · python$/);
    expect(chip()).toHaveFocus();
    expect(onPick).toHaveBeenCalledTimes(1);
  });

  it('shows a failed switch under the chip with its ref, and clears it once something else runs', async () => {
    const user = userEvent.setup();
    const onPick = vi
      .fn<(library: string) => Promise<void>>()
      .mockRejectedValueOnce(new AgentApiError(422, 'not_eligible', 'ref-ne'))
      .mockRejectedValueOnce(new AgentApiError(404, 'session_expired', 'ref-gone'));
    const { rerender } = render(<LibraryChip {...props({ onPick })} />);

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: 'd3' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'could not switch: this plot cannot be adapted in that library · ref ref-ne'
    );
    expect(chip()).toHaveTextContent(/^lib: matplotlib · python$/);

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: 'makie' }));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        'could not switch: the session expired · ref ref-gone'
      )
    );
    expect(screen.getByRole('button', { name: 'reload' })).toBeInTheDocument();

    rerender(<LibraryChip {...props({ onPick, disabled: true })} />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('closes an open menu when something else starts', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<LibraryChip {...props()} />);
    await user.click(chip());
    expect(dialog()).toBeInTheDocument();

    rerender(<LibraryChip {...props({ disabled: true })} />);
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(chip()).toHaveAttribute('aria-expanded', 'false');
  });
});
