import { describe, expect, it } from 'vitest';

import { SpecTab } from 'src/sections/spec-detail/SpecTabs/SpecTab';
import { render, screen } from 'src/test-utils';

const baseProps = {
  title: 'Basic Scatter Plot',
  description: 'A scatter plot showing data points',
};

describe('SpecTab', () => {
  it('renders the title and description', () => {
    render(<SpecTab {...baseProps} />);
    expect(screen.getByText('Basic Scatter Plot')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByText('A scatter plot showing data points')).toBeInTheDocument();
  });

  it('renders backtick spans in the description as inline code', () => {
    render(<SpecTab {...baseProps} description="Uses `numpy` arrays" />);
    const code = screen.getByText('numpy');
    expect(code.tagName).toBe('CODE');
  });

  it('renders applications, data, and notes lists when provided', () => {
    render(
      <SpecTab
        {...baseProps}
        applications={['Data analysis']}
        data={['Random numeric data']}
        notes={['Use for small datasets']}
      />
    );

    expect(screen.getByText('Applications')).toBeInTheDocument();
    expect(screen.getByText('Data analysis')).toBeInTheDocument();
    expect(screen.getByText('Data')).toBeInTheDocument();
    expect(screen.getByText('Random numeric data')).toBeInTheDocument();
    expect(screen.getByText('Notes')).toBeInTheDocument();
    expect(screen.getByText('Use for small datasets')).toBeInTheDocument();
  });

  it('hides the optional sections when their props are absent or empty', () => {
    render(<SpecTab {...baseProps} applications={[]} />);
    expect(screen.queryByText('Applications')).not.toBeInTheDocument();
    expect(screen.queryByText('Data')).not.toBeInTheDocument();
    expect(screen.queryByText('Notes')).not.toBeInTheDocument();
  });
});
