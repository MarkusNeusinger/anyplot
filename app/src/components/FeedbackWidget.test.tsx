import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, userEvent, waitFor } from '../test-utils';
import { FeedbackWidget } from './FeedbackWidget';

describe('FeedbackWidget', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('renders the floating button', () => {
    render(<FeedbackWidget />);
    expect(screen.getByRole('button', { name: /open feedback/i })).toBeInTheDocument();
  });

  it('opens the mini-stack of quick actions when the FAB is clicked', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(<FeedbackWidget />);

    await user.click(screen.getByRole('button', { name: /open feedback/i }));
    expect(await screen.findByRole('button', { name: /quick thumbs up/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /quick thumbs down/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /open detailed feedback/i })).toBeInTheDocument();
    // The full dialog should NOT be open yet.
    expect(screen.queryByRole('textbox', { name: /feedback message/i })).toBeNull();
  });

  it('submits a reaction-only entry when 👍 is clicked in the mini-stack', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    );
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });

    render(<FeedbackWidget />);
    await user.click(screen.getByRole('button', { name: /open feedback/i }));
    await user.click(await screen.findByRole('button', { name: /quick thumbs up/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
    const body = JSON.parse((fetchSpy.mock.calls[0][1] as RequestInit).body as string);
    expect(body.message).toBeNull();
    expect(body.reaction).toBe('thumbs_up');
    expect(typeof body.path).toBe('string'); // current URL is sent along

    // Thanks toast appears, mini-stack collapses.
    expect(await screen.findByText(/^Thanks!/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /quick thumbs up/i })).toBeNull();
  });

  it('expands the full dialog when 💬 is clicked', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(<FeedbackWidget />);

    await user.click(screen.getByRole('button', { name: /open feedback/i }));
    await user.click(await screen.findByRole('button', { name: /open detailed feedback/i }));

    expect(await screen.findByRole('textbox', { name: /feedback message/i })).toBeInTheDocument();
    expect(screen.getByText(/^Page:/)).toBeInTheDocument();
  });

  it('disables Send in the full dialog until message or reaction is provided', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(<FeedbackWidget />);

    await user.click(screen.getByRole('button', { name: /open feedback/i }));
    await user.click(await screen.findByRole('button', { name: /open detailed feedback/i }));

    const send = await screen.findByRole('button', { name: /^send$/i });
    expect(send).toBeDisabled();

    await user.click(screen.getByRole('button', { name: /^idea$/i }));
    expect(send).toBeEnabled();
  });

  it('POSTs full-form fields to /feedback and shows a thank-you on success', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    );
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });

    render(<FeedbackWidget />);
    await user.click(screen.getByRole('button', { name: /open feedback/i }));
    await user.click(await screen.findByRole('button', { name: /open detailed feedback/i }));
    await user.type(screen.getByRole('textbox', { name: /feedback message/i }), 'Looks great');
    await user.click(screen.getByRole('button', { name: /^send$/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toMatch(/\/feedback$/);
    const body = JSON.parse((init as RequestInit).body as string);
    expect(body.message).toBe('Looks great');
    expect(body.website).toBe(''); // honeypot must be empty for real users

    expect(await screen.findByText(/thanks/i)).toBeInTheDocument();
  });

  it('shows an error and keeps the full-form populated on failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('boom', { status: 429 }));
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });

    render(<FeedbackWidget />);
    await user.click(screen.getByRole('button', { name: /open feedback/i }));
    await user.click(await screen.findByRole('button', { name: /open detailed feedback/i }));
    const textarea = await screen.findByRole('textbox', { name: /feedback message/i });
    await user.type(textarea, 'try me');
    await user.click(screen.getByRole('button', { name: /^send$/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't send/i);
    expect(textarea).toHaveValue('try me');
  });

  it('honeypot input is hidden from assistive tech', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(<FeedbackWidget />);
    await user.click(screen.getByRole('button', { name: /open feedback/i }));
    await user.click(await screen.findByRole('button', { name: /open detailed feedback/i }));

    // The honeypot lives inside an aria-hidden wrapper, so it must not be discoverable
    // as a labelled form control to screen-reader queries.
    expect(screen.queryByLabelText(/website/i)).toBeNull();
  });
});
