import { describe, expect, it, vi } from 'vitest';

import { LibraryCard } from 'src/sections/libraries/LibraryCard';
import { render, screen, userEvent } from 'src/test-utils';

describe('LibraryCard', () => {
  it('renders the library name', () => {
    render(<LibraryCard name="matplotlib" onClick={vi.fn()} />);
    expect(screen.getByText('matplotlib')).toBeInTheDocument();
  });

  it('renders the description for a javascript library', () => {
    render(<LibraryCard name="echarts" language="javascript" onClick={vi.fn()} />);
    expect(screen.getByText(/Powerful interactive charts for the browser/i)).toBeInTheDocument();
  });

  it('renders the language chip in the corner when language is provided', () => {
    render(<LibraryCard name="ggplot2" language="r" onClick={vi.fn()} />);
    expect(screen.getByLabelText('Language: R')).toHaveTextContent('R');
  });

  it('renders an uppercased Python chip for python libraries', () => {
    render(<LibraryCard name="matplotlib" language="python" onClick={vi.fn()} />);
    expect(screen.getByLabelText('Language: PYTHON')).toHaveTextContent('PYTHON');
  });

  it('does not render a chip when language is missing', () => {
    render(<LibraryCard name="matplotlib" onClick={vi.fn()} />);
    expect(screen.queryByLabelText(/Language:/)).not.toBeInTheDocument();
  });

  it('renders the example count when provided', () => {
    render(<LibraryCard name="matplotlib" language="python" count={42} onClick={vi.fn()} />);
    expect(screen.getByText('42 examples')).toBeInTheDocument();
  });

  it.each([
    ['highcharts', 'free for non-commercial use'],
    ['muix', 'MIT · community'],
  ])('notes the licence of %s on its card', (name, note) => {
    render(<LibraryCard name={name} language="javascript" onClick={vi.fn()} />);
    expect(screen.getByLabelText(`License: ${note}`)).toHaveTextContent(note);
  });

  it.each(['highcharts', 'muix'])('puts the licence note of %s before .explore()', name => {
    // The note has its own line above .explore(), so .explore() stays on the card's
    // bottom line in step with the cards beside it.
    render(<LibraryCard name={name} language="javascript" onClick={vi.fn()} />);
    const note = screen.getByLabelText(/^License: /);
    const explore = screen.getByText('.explore()');
    expect(note.parentElement).toBe(explore.parentElement);
    expect(note.compareDocumentPosition(explore) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('shows no licence note for a library under an open licence', () => {
    render(<LibraryCard name="echarts" language="javascript" onClick={vi.fn()} />);
    expect(screen.queryByLabelText(/License:/)).not.toBeInTheDocument();
  });

  it('fires onClick when the card is clicked', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<LibraryCard name="matplotlib" language="python" onClick={onClick} />);

    await user.click(screen.getByRole('button', { name: /Browse matplotlib examples/i }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
