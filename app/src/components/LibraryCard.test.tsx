import { describe, expect, it, vi } from 'vitest';

import { LibraryCard } from 'src/components/LibraryCard';
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

  it('fires onClick when the card is clicked', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<LibraryCard name="matplotlib" language="python" onClick={onClick} />);

    await user.click(screen.getByRole('button', { name: /Browse matplotlib examples/i }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
