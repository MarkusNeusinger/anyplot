import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../test-utils';
import { McpPage } from './McpPage';

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('../hooks', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: vi.fn(),
  }),
}));

describe('McpPage', () => {
  it('renders all section headings', () => {
    render(<McpPage />);

    const headings = screen.getAllByRole('heading');
    const headingTexts = headings.map((h) => h.textContent);

    expect(headingTexts).toContain('What is MCP?');
    expect(headingTexts).toContain('Configuration');
    expect(headingTexts).toContain('Available Tools');
    expect(headingTexts).toContain('Use Cases');
    expect(headingTexts).toContain('Resources');
  });

  it('renders anchor navigation links to all sections', () => {
    render(<McpPage />);

    const allLinks = screen.getAllByRole('link');
    const anchorLinks = allLinks.filter(
      (link) => link.getAttribute('href')?.startsWith('#')
    );

    expect(anchorLinks).toHaveLength(5);
    const hrefs = anchorLinks.map((a) => a.getAttribute('href'));
    expect(hrefs).toContain('#what-is-mcp');
    expect(hrefs).toContain('#configuration');
    expect(hrefs).toContain('#tools');
    expect(hrefs).toContain('#use-cases');
    expect(hrefs).toContain('#resources');
  });

  it('renders the MCP endpoint URL', () => {
    render(<McpPage />);

    const endpoints = screen.getAllByText('https://api.anyplot.ai/mcp/');
    expect(endpoints.length).toBeGreaterThan(0);
  });

  it('renders the Claude Code configuration command', () => {
    render(<McpPage />);

    expect(
      screen.getByText(/claude mcp add anyplot/)
    ).toBeInTheDocument();
  });

  it('renders all MCP tool names in the tools table', () => {
    render(<McpPage />);

    const toolNames = ['list_specs', 'search_specs_by_tags', 'get_spec_detail', 'get_implementation', 'list_libraries', 'get_tag_values'];
    for (const tool of toolNames) {
      expect(screen.getByText(tool)).toBeInTheDocument();
    }
  });

  it('renders use case subheadings', () => {
    render(<McpPage />);

    expect(screen.getByText('AI-Assisted Plot Discovery')).toBeInTheDocument();
    expect(screen.getByText('Code Generation with AI')).toBeInTheDocument();
    expect(screen.getByText('Comparing Library Implementations')).toBeInTheDocument();
  });

  it('renders breadcrumb navigation', () => {
    render(<McpPage />);

    expect(screen.getByRole('navigation', { name: 'breadcrumb' })).toBeInTheDocument();
  });

  it('renders link to MCP protocol site', () => {
    render(<McpPage />);

    const mcpLink = screen.getByRole('link', { name: /Model Context Protocol/ });
    expect(mcpLink).toHaveAttribute('href', 'https://modelcontextprotocol.io');
  });

  it('renders footer with github link', () => {
    render(<McpPage />);

    expect(screen.getByText('github')).toBeInTheDocument();
  });
});
