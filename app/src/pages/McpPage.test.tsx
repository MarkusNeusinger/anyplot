import { describe, expect, it, vi } from 'vitest';

import { McpPage } from 'src/pages/McpPage';
import { render, screen } from 'src/test-utils';

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('src/hooks', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: vi.fn(),
  }),
}));

describe('McpPage', () => {
  it('renders all section headings', () => {
    render(<McpPage />);

    const headings = screen.getAllByRole('heading');
    const headingTexts = headings.map(h => h.textContent);

    expect(headingTexts).toContain('what is mcp');
    expect(headingTexts).toContain('configuration');
    expect(headingTexts).toContain('available tools');
    expect(headingTexts).toContain('use cases');
    expect(headingTexts).toContain('resources');
  });

  it('renders the MCP endpoint URL', () => {
    render(<McpPage />);

    const endpoints = screen.getAllByText('https://api.anyplot.ai/mcp/');
    expect(endpoints.length).toBeGreaterThan(0);
  });

  it('renders the Claude Code configuration command', () => {
    render(<McpPage />);

    expect(screen.getByText(/claude mcp add anyplot/)).toBeInTheDocument();
  });

  it('renders all MCP tool names in the tools table', () => {
    render(<McpPage />);

    const toolNames = [
      'list_specs',
      'search_specs_by_tags',
      'get_spec_detail',
      'get_implementation',
      'list_libraries',
      'get_tag_values',
    ];
    for (const tool of toolNames) {
      expect(screen.getByText(tool)).toBeInTheDocument();
    }
  });

  it('renders use case subheadings', () => {
    render(<McpPage />);

    expect(screen.getByText('ai-assisted plot discovery')).toBeInTheDocument();
    expect(screen.getByText('code generation with ai')).toBeInTheDocument();
    expect(screen.getByText('comparing library implementations')).toBeInTheDocument();
  });

  it('renders link to MCP protocol site', () => {
    render(<McpPage />);

    const mcpLink = screen.getByRole('link', { name: /Model Context Protocol/ });
    expect(mcpLink).toHaveAttribute('href', 'https://modelcontextprotocol.io');
  });
});
