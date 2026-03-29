import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent } from '@testing-library/react';
import { render, screen, userEvent } from '../test-utils';
import { Header } from './Header';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

describe('Header', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it('renders the pyplots.ai logo text', () => {
    render(<Header />);

    expect(screen.getByText('py')).toBeInTheDocument();
    expect(screen.getByText('plots')).toBeInTheDocument();
    expect(screen.getByText('.ai')).toBeInTheDocument();
  });

  it('renders tagline text', () => {
    render(<Header />);

    expect(screen.getByText(/ai-powered python/i)).toBeInTheDocument();
  });

  it('renders "get inspired" call to action', () => {
    render(<Header />);

    expect(screen.getByText(/get inspired/)).toBeInTheDocument();
  });

  it('renders stats tooltip content when stats provided', () => {
    render(<Header stats={{ specs: 254, plots: 1800, libraries: 9 }} />);

    expect(screen.getByText('✦')).toBeInTheDocument();
  });

  it('renders shuffle icon when onRandom is provided', () => {
    render(<Header onRandom={vi.fn()} />);

    expect(screen.getByRole('button', { name: /random filter/i })).toBeInTheDocument();
  });

  it('does not render shuffle icon when onRandom is not provided', () => {
    render(<Header />);

    expect(screen.queryByRole('button', { name: /random filter/i })).toBeNull();
  });

  it('calls onRandom with "click" when shuffle icon is clicked', async () => {
    const onRandom = vi.fn();
    const user = userEvent.setup();

    render(<Header onRandom={onRandom} />);

    await user.click(screen.getByRole('button', { name: /random filter/i }));
    expect(onRandom).toHaveBeenCalledWith('click');
  });

  it('navigates to "/" on single click of logo', () => {
    vi.useFakeTimers();
    render(<Header />);

    const logo = screen.getByRole('link');
    fireEvent.click(logo);

    // Wait for the 400ms debounce
    vi.advanceTimersByTime(400);

    expect(mockNavigate).toHaveBeenCalledWith('/');
    vi.useRealTimers();
  });

  it('navigates to "/debug" on triple click of logo', () => {
    vi.useFakeTimers();
    render(<Header />);

    const logo = screen.getByRole('link');
    fireEvent.click(logo);
    fireEvent.click(logo);
    fireEvent.click(logo);

    expect(mockNavigate).toHaveBeenCalledWith('/debug');
    vi.useRealTimers();
  });

  it('has a header element', () => {
    render(<Header />);

    expect(screen.getByRole('banner')).toBeInTheDocument();
  });

  it('renders heading as h1', () => {
    render(<Header />);

    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
  });
});
