import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '../test-utils';
import { LibraryPills } from './LibraryPills';

const mockImplementations = [
  { library_id: 'matplotlib', library_name: 'Matplotlib', quality_score: 85 },
  { library_id: 'seaborn', library_name: 'Seaborn', quality_score: 90 },
  { library_id: 'plotly', library_name: 'Plotly', quality_score: 78 },
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
});
