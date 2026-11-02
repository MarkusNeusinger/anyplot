import { describe, expect, it, vi } from 'vitest';

import { LibraryPills, USE_MY_DATA_LABEL } from 'src/sections/spec-detail/LibraryPills';
import { render, screen, userEvent } from 'src/test-utils';

const mockImplementations = [
  { library_id: 'matplotlib', library_name: 'Matplotlib', language: 'python', quality_score: 85 },
  { library_id: 'seaborn', library_name: 'Seaborn', language: 'python', quality_score: 90 },
  { library_id: 'plotly', library_name: 'Plotly', language: 'python', quality_score: 78 },
];

describe('LibraryPills', () => {
  it('renders nothing for empty implementations', () => {
    const { container } = render(
      <LibraryPills implementations={[]} selectedLibrary="matplotlib" onSelect={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders selected library', () => {
    render(
      <LibraryPills
        implementations={mockImplementations}
        selectedLibrary="matplotlib"
        onSelect={vi.fn()}
      />
    );

    expect(screen.getAllByText('matplotlib').length).toBeGreaterThan(0);
  });

  it('calls onSelect when clicking a pill', async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();

    render(
      <LibraryPills
        implementations={mockImplementations}
        selectedLibrary="matplotlib"
        onSelect={onSelect}
      />
    );

    // Click the next arrow to navigate
    const buttons = screen.getAllByRole('button');
    await user.click(buttons[1]); // right arrow

    expect(onSelect).toHaveBeenCalled();
  });

  it('calls onSelect when clicking prev arrow', async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();

    render(
      <LibraryPills
        implementations={mockImplementations}
        selectedLibrary="matplotlib"
        onSelect={onSelect}
      />
    );

    const buttons = screen.getAllByRole('button');
    await user.click(buttons[0]); // left arrow

    expect(onSelect).toHaveBeenCalled();
  });

  it('handles single implementation', () => {
    render(
      <LibraryPills
        implementations={[mockImplementations[0]]}
        selectedLibrary="matplotlib"
        onSelect={vi.fn()}
      />
    );

    expect(screen.getAllByText('matplotlib').length).toBeGreaterThan(0);
  });

  it('handles two implementations', () => {
    render(
      <LibraryPills
        implementations={mockImplementations.slice(0, 2)}
        selectedLibrary="matplotlib"
        onSelect={vi.fn()}
      />
    );

    expect(screen.getAllByText('matplotlib').length).toBeGreaterThan(0);
  });

  it('shows .use_my_data() only when SpecPage passes onUseWithMyData', async () => {
    const onUseWithMyData = vi.fn();
    const user = userEvent.setup();
    const props = {
      implementations: mockImplementations,
      selectedLibrary: 'matplotlib',
      onSelect: vi.fn(),
      onAll: vi.fn(),
    };
    const { rerender } = render(<LibraryPills {...props} />);
    expect(screen.queryByRole('button', { name: USE_MY_DATA_LABEL })).not.toBeInTheDocument();
    expect(screen.queryByText('experimental')).not.toBeInTheDocument();

    rerender(<LibraryPills {...props} onUseWithMyData={onUseWithMyData} />);
    const action = screen.getByRole('button', { name: 'Use with my data (experimental)' });
    expect(action).toHaveTextContent('.use_my_data()');
    expect(screen.getByText('experimental')).toBeInTheDocument();
    await user.click(action);
    expect(onUseWithMyData).toHaveBeenCalledTimes(1);
    expect(props.onAll).not.toHaveBeenCalled();
  });

  it('opens .use_my_data() from the keyboard, after the carousel in the tab order', async () => {
    const onUseWithMyData = vi.fn();
    const user = userEvent.setup();
    render(
      <LibraryPills
        implementations={mockImplementations}
        selectedLibrary="matplotlib"
        onSelect={vi.fn()}
        onAll={vi.fn()}
        onUseWithMyData={onUseWithMyData}
      />
    );

    await user.tab();
    expect(screen.getByRole('button', { name: 'Back to library comparison' })).toHaveFocus();
    await user.tab();
    await user.tab();
    await user.tab();
    const action = screen.getByRole('button', { name: USE_MY_DATA_LABEL });
    expect(action).toHaveFocus();
    await user.keyboard('{Enter}');
    await user.keyboard(' ');
    expect(onUseWithMyData).toHaveBeenCalledTimes(2);
  });
});
