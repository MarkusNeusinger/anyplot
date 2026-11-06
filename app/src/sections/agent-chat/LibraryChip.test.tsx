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
    allPressed: false,
    disabled: false,
    onPick: vi.fn(async () => undefined),
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
  it('names the library in plain words, its language in the name, and is disabled while the page says so', () => {
    const { rerender } = render(<LibraryChip {...props({ disabled: true })} />);
    // `seaborn ▾` since the v4 frame: the language leaves the screen, the name keeps it.
    expect(chip()).toHaveTextContent(/^matplotlib ▾$/);
    expect(chip()).toBeDisabled();
    expect(chip()).toHaveAccessibleName('Library: matplotlib, Python. Change');
    expect(chip()).toHaveAttribute('aria-haspopup', 'dialog');

    rerender(<LibraryChip {...props({ library: 'ggplot2' })} />);
    expect(chip()).toHaveTextContent(/^ggplot2 ▾$/);
    expect(chip()).toHaveAccessibleName('Library: ggplot2, R. Change');
    expect(chip()).toBeEnabled();

    rerender(<LibraryChip {...props({ allPressed: true })} />);
    // The name holds the words on screen (WCAG 2.5.3, label in name).
    expect(chip()).toHaveTextContent(/^all 15 libraries ▾$/);
    expect(chip()).toHaveAccessibleName('Library: all 15 libraries. Change');
  });

  it('announces each change of the library or of the fan-out once, and nothing on mount', () => {
    const { rerender } = render(<LibraryChip {...props()} />);
    expect(screen.getByRole('status')).toHaveTextContent('');
    rerender(<LibraryChip {...props({ library: 'plotly' })} />);
    expect(screen.getByRole('status')).toHaveTextContent('library: plotly');
    rerender(<LibraryChip {...props({ library: 'plotly', allPressed: true })} />);
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
    // The libraries only: the fan-out's toggle is in the admin menu since 2026-11-06.
    expect(within(dialog()).getAllByRole('button')).toHaveLength(15);

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

  it('lets the library in use be picked while the fan-out is on, which the page reads as off', async () => {
    const user = userEvent.setup();
    const onPick = vi.fn(async () => undefined);
    render(<LibraryChip {...props({ allPressed: true, onPick })} />);

    await user.click(chip());
    const own = within(dialog()).getByRole('button', { name: 'matplotlib' });
    expect(own).toHaveAttribute('aria-pressed', 'false');
    expect(own).toBeEnabled();
    await user.click(own);
    expect(onPick).toHaveBeenCalledWith('matplotlib');
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('makes the other libraries links where there is no session to switch', async () => {
    const user = userEvent.setup();
    const onPick = vi.fn(async () => undefined);
    render(
      <LibraryChip
        {...props({
          libraries: ['matplotlib', 'seaborn', 'ggplot2'],
          hrefFor: lib => `/agent?spec=scatter-basic&library=${lib}`,
          onPick,
        })}
      />
    );
    await user.click(chip());
    expect(within(dialog()).getByRole('link', { name: 'ggplot2' })).toHaveAttribute(
      'href',
      '/agent?spec=scatter-basic&library=ggplot2'
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
    expect(chip()).toHaveTextContent(/^matplotlib … ▾$/);
    expect(chip()).toHaveAttribute('aria-disabled', 'true');
    expect(chip()).not.toBeDisabled();
    await user.click(chip());
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    gate.resolve();
    rerender(<LibraryChip {...props({ onPick, library: 'plotly' })} />);
    await waitFor(() => expect(chip()).not.toHaveAttribute('aria-disabled'));
    expect(chip()).toHaveTextContent(/^plotly ▾$/);
    expect(chip()).toHaveFocus();
    expect(onPick).toHaveBeenCalledTimes(1);
  });

  it('shows a failed switch under the chip with its ref, and clears it once something else runs', async () => {
    const user = userEvent.setup();
    const onPick = vi
      .fn<(library: string) => Promise<void>>()
      .mockRejectedValueOnce(new AgentApiError(422, 'not_eligible', 'ref-ne'))
      .mockRejectedValueOnce(new AgentApiError(404, 'session_expired', 'ref-gone'))
      .mockRejectedValueOnce(new AgentApiError(500, 'internal', 'ref-500'));
    const { rerender } = render(<LibraryChip {...props({ onPick })} />);

    // A refusal (4xx) names its cause and shows no ref; a fault of the server does.
    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: 'd3' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(
      /^could not switch: this plot cannot be adapted in that library$/
    );
    expect(chip()).toHaveTextContent(/^matplotlib ▾$/);

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: 'makie' }));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        /^could not switch: the session expired · reload$/
      )
    );
    expect(screen.getByRole('button', { name: 'reload' })).toBeInTheDocument();

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: 'd3' }));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        'could not switch: something went wrong on the server · ref ref-500'
      )
    );

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
