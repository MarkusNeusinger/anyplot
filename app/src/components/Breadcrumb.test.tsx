import { describe, it, expect } from 'vitest';
import { render, screen } from '../test-utils';
import { Breadcrumb } from './Breadcrumb';

describe('Breadcrumb', () => {
  it('renders breadcrumb items', () => {
    render(<Breadcrumb items={[{ label: 'pyplots.ai', to: '/' }, { label: 'catalog' }]} />);

    expect(screen.getByText('pyplots.ai')).toBeInTheDocument();
    expect(screen.getByText('catalog')).toBeInTheDocument();
  });

  it('renders linked items as links', () => {
    render(<Breadcrumb items={[{ label: 'pyplots.ai', to: '/' }, { label: 'catalog' }]} />);

    const link = screen.getByText('pyplots.ai');
    expect(link.closest('a')).toHaveAttribute('href', '/');
  });

  it('renders current page as plain text', () => {
    render(<Breadcrumb items={[{ label: 'pyplots.ai', to: '/' }, { label: 'catalog' }]} />);

    const current = screen.getByText('catalog');
    expect(current.closest('a')).toBeNull();
  });

  it('renders separator between items', () => {
    render(<Breadcrumb items={[{ label: 'pyplots.ai', to: '/' }, { label: 'catalog' }]} />);

    expect(screen.getByText('›')).toBeInTheDocument();
  });

  it('renders right action when provided', () => {
    render(
      <Breadcrumb
        items={[{ label: 'pyplots.ai', to: '/' }]}
        rightAction={<span>action</span>}
      />
    );

    expect(screen.getByText('action')).toBeInTheDocument();
  });

  it('has navigation aria-label', () => {
    render(<Breadcrumb items={[{ label: 'home', to: '/' }]} />);

    expect(screen.getByRole('navigation')).toHaveAttribute('aria-label', 'breadcrumb');
  });
});
