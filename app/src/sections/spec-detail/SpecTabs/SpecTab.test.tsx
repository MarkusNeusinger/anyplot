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
    expect(screen.queryByText('Sources')).not.toBeInTheDocument();
  });

  describe('sources', () => {
    const sources = {
      data: 'computed' as const,
      inspired_by: [{ title: 'An example project', url: 'https://example.org/project' }],
      references: [
        {
          title: 'A paper',
          url: 'https://example.org/paper',
          doi: '10.1000/xyz123',
          isbn: null,
        },
        { title: 'A book', url: 'https://example.org/book', isbn: '978-3-16-148410-0' },
      ],
    };

    it('lists both groups with every title as a link to its address', () => {
      render(<SpecTab {...baseProps} sources={sources} />);
      expect(screen.getByRole('heading', { name: 'Sources' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'inspired by' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'references' })).toBeInTheDocument();
      const project = screen.getByRole('link', { name: 'An example project' });
      expect(project).toHaveAttribute('href', 'https://example.org/project');
      expect(project).toHaveAttribute('target', '_blank');
      expect(project).toHaveAttribute('rel', 'noopener noreferrer');
      expect(screen.getByRole('link', { name: 'A book' })).toHaveAttribute(
        'href',
        'https://example.org/book'
      );
    });

    it('links a DOI to its resolver and shows an ISBN as text', () => {
      render(<SpecTab {...baseProps} sources={sources} />);
      expect(screen.getByRole('link', { name: 'doi:10.1000/xyz123' })).toHaveAttribute(
        'href',
        'https://doi.org/10.1000/xyz123'
      );
      expect(screen.getByText('ISBN 978-3-16-148410-0').tagName).toBe('SPAN');
      expect(screen.queryByRole('link', { name: /ISBN/ })).not.toBeInTheDocument();
    });

    it('leaves out a group without entries', () => {
      render(
        <SpecTab {...baseProps} sources={{ inspired_by: [], references: sources.references }} />
      );
      expect(screen.getByRole('heading', { name: 'references' })).toBeInTheDocument();
      expect(screen.queryByRole('heading', { name: 'inspired by' })).not.toBeInTheDocument();
    });

    it('shows nothing for a spec that names no work', () => {
      for (const none of [null, { data: 'invented' as const, inspired_by: [], references: [] }]) {
        const { unmount } = render(<SpecTab {...baseProps} sources={none} />);
        expect(screen.queryByText('Sources')).not.toBeInTheDocument();
        unmount();
      }
    });
  });
});
