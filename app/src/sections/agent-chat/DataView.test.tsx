import { describe, expect, it, vi } from 'vitest';

import { AgentApiError, type DatasetProfile } from 'src/lib/agent';
import DataView from 'src/sections/agent-chat/DataView';
import { render, screen, userEvent, waitFor, within } from 'src/test-utils';

const PROFILE: DatasetProfile = {
  rows: 3,
  columns: [
    { name: 'city', dtype: 'text', missing: 0, unique: 3 },
    { name: 'value', dtype: 'number', missing: 1, unique: 2 },
  ],
  source_format: 'csv',
  decimal: '.',
  warnings: [],
};
const CSV = 'city,value\n"Köln, Nord",1.50\nBonn,\n"two  spaces",10\n';

function renderView(load: (signal: AbortSignal) => Promise<string>, extra = {}) {
  const onClose = vi.fn();
  const onShown = vi.fn();
  render(
    <DataView
      profile={PROFILE}
      version={2}
      load={load}
      onClose={onClose}
      onShown={onShown}
      {...extra}
    />
  );
  return { onClose, onShown };
}

describe('DataView', () => {
  it('shows every value exactly as the file holds it, with the dtype in each header', async () => {
    const { onShown } = renderView(() => Promise.resolve(CSV));
    const dialog = await screen.findByRole('dialog', {
      name: /every row · 3 rows · 2 columns · version 2/,
    });
    const grid = await within(dialog).findByRole('grid');
    expect(within(grid).getByRole('columnheader', { name: /city\s*text/ })).toBeInTheDocument();
    expect(within(grid).getByRole('columnheader', { name: /value\s*number/ })).toBeInTheDocument();
    // `1.50` keeps its zero, the comma stays inside its cell, the empty cell stays empty.
    expect(within(grid).getByText('Köln, Nord')).toBeInTheDocument();
    expect(within(grid).getByText('1.50')).toBeInTheDocument();
    const bonn = within(grid).getByText('Bonn').closest('[role="row"]') as HTMLElement;
    expect(
      within(bonn)
        .getAllByRole('gridcell')
        .map(cell => cell.textContent)
    ).toEqual(['2', 'Bonn', '']);
    expect(onShown).toHaveBeenCalledTimes(1);
  });

  it('says so while it reads, and offers .retry() when the data cannot be read', async () => {
    const load = vi
      .fn<(signal: AbortSignal) => Promise<string>>()
      .mockRejectedValueOnce(new AgentApiError(422, 'no_dataset', 'ref-1'))
      .mockResolvedValueOnce(CSV);
    const { onShown } = renderView(load);
    expect(screen.getByRole('status')).toHaveTextContent('reading 3 rows');
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'could not show every row: parse the data first · ref ref-1'
    );
    expect(onShown).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button', { name: '.retry()' }));
    expect(await screen.findByRole('grid')).toBeInTheDocument();
    expect(load).toHaveBeenCalledTimes(2);
    expect(onShown).toHaveBeenCalledTimes(1);
  });

  it('refuses a file that is not the canonical CSV instead of showing something else', async () => {
    renderView(() => Promise.resolve('city,value\nBonn,"open\n'));
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'could not show every row: the file is not the CSV it should be (row 2: a quoted cell is never closed)'
    );
  });

  it('closes with .close() and with Escape', async () => {
    const { onClose } = renderView(() => Promise.resolve(CSV));
    await screen.findByRole('grid');
    await userEvent.click(screen.getByRole('button', { name: 'Close the data view' }));
    expect(onClose).toHaveBeenCalledTimes(1);
    await userEvent.keyboard('{Escape}');
    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(2));
  });

  it('lets Escape clear the search before it closes the view', async () => {
    const { onClose } = renderView(() => Promise.resolve(CSV));
    await screen.findByRole('grid');
    const search = screen.getByRole('searchbox', { name: 'Search every column' });
    await userEvent.type(search, 'bonn');
    await userEvent.keyboard('{Escape}');
    await waitFor(() => expect(search).toHaveValue(''));
    expect(onClose).not.toHaveBeenCalled();
  });

  it('searches every column without touching the cells', async () => {
    renderView(() => Promise.resolve(CSV));
    const grid = await screen.findByRole('grid');
    await userEvent.type(screen.getByRole('searchbox', { name: 'Search every column' }), 'nord');
    await waitFor(() => expect(within(grid).queryByText('Bonn')).not.toBeInTheDocument());
    expect(within(grid).getByText('Köln, Nord')).toBeInTheDocument();
  });

  it('reads the data again for a new version', async () => {
    const load = vi.fn<(signal: AbortSignal) => Promise<string>>().mockResolvedValue(CSV);
    const props = { version: 2, load, onClose: vi.fn() };
    const { rerender } = render(<DataView profile={PROFILE} {...props} />);
    await screen.findByRole('grid');
    load.mockResolvedValue('city,value\nBerlin,3\n');
    rerender(<DataView profile={{ ...PROFILE, rows: 1 }} {...props} version={3} />);
    expect(await screen.findByText('Berlin')).toBeInTheDocument();
    expect(load).toHaveBeenCalledTimes(2);
  });
});
