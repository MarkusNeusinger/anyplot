import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { BOT_CHECK_FAILED_TEXT, FeedbackWidget } from 'src/components/FeedbackWidget';
import { resetTurnstile, TURNSTILE_HEADER } from 'src/lib/turnstile';
import { render, screen, userEvent, waitFor } from 'src/test-utils';

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
      new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
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
      new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
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

  describe('the bot check', () => {
    beforeEach(() => vi.stubEnv('VITE_TURNSTILE_SITE_KEY', '1x00000000000000000000AA'));

    afterEach(() => {
      vi.unstubAllEnvs();
      resetTurnstile();
      delete window.turnstile;
    });

    function stubTurnstile(pass: boolean) {
      window.turnstile = {
        render: vi.fn((container: HTMLElement, options: Record<string, unknown>) => {
          renderedIn.push(container.parentElement);
          queueMicrotask(() =>
            pass
              ? (options.callback as (token: string) => void)('tok-w')
              : (options['error-callback'] as () => void)()
          );
          return 'w1';
        }),
        remove: vi.fn(),
      };
    }
    let renderedIn: (HTMLElement | null)[] = [];

    async function sendFullForm(text: string) {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
      render(<FeedbackWidget />);
      await user.click(screen.getByRole('button', { name: /open feedback/i }));
      await user.click(await screen.findByRole('button', { name: /open detailed feedback/i }));
      const textarea = await screen.findByRole('textbox', { name: /feedback message/i });
      const slot = screen.getByTestId('feedback-check-slot');
      await user.type(textarea, text);
      await user.click(screen.getByRole('button', { name: /^send$/i }));
      return { textarea, slot };
    }

    it('sends a fresh token, rendered inside the popover', async () => {
      renderedIn = [];
      stubTurnstile(true);
      const fetchSpy = vi
        .spyOn(globalThis, 'fetch')
        .mockResolvedValue(new Response(JSON.stringify({ status: 'ok' }), { status: 200 }));

      const { slot } = await sendFullForm('Looks great');

      await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
      const headers = (fetchSpy.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
      expect(headers[TURNSTILE_HEADER]).toBe('tok-w');
      expect(renderedIn[0]).toBe(slot);
    });

    it('says the check did not go through, keeps the text and sends nothing', async () => {
      renderedIn = [];
      stubTurnstile(false);
      const fetchSpy = vi.spyOn(globalThis, 'fetch');

      const { textarea } = await sendFullForm('try me');

      expect(await screen.findByRole('alert')).toHaveTextContent(BOT_CHECK_FAILED_TEXT);
      expect(textarea).toHaveValue('try me');
      expect(fetchSpy).not.toHaveBeenCalled();
    });

    it("reads the API's 403 as the same message", async () => {
      renderedIn = [];
      stubTurnstile(true);
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response(JSON.stringify({ status: 403, message: 'bot_check_failed' }), { status: 403 })
      );

      await sendFullForm('try me');

      expect(await screen.findByRole('alert')).toHaveTextContent(BOT_CHECK_FAILED_TEXT);
    });
  });

  it('reopening the mini-stack clears a lingering Thanks toast', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });

    render(<FeedbackWidget />);
    const fab = screen.getByRole('button', { name: /open feedback/i });
    await user.click(fab);
    await user.click(await screen.findByRole('button', { name: /quick thumbs up/i }));
    expect(await screen.findByText(/^Thanks!/)).toBeInTheDocument();

    // Toast and stack share the slot above the FAB — never both at once.
    await user.click(fab);
    expect(await screen.findByRole('button', { name: /quick thumbs up/i })).toBeInTheDocument();
    expect(screen.queryByText(/^Thanks!/)).toBeNull();
  });

  it('a second FAB click closes the mini-stack', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(<FeedbackWidget />);

    const fab = screen.getByRole('button', { name: /open feedback/i });
    await user.click(fab);
    expect(await screen.findByRole('button', { name: /quick thumbs up/i })).toBeInTheDocument();

    await user.click(fab);
    expect(screen.queryByRole('button', { name: /quick thumbs up/i })).toBeNull();
  });

  it('clicking outside the mini-stack closes it via ClickAwayListener', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(
      <div>
        <button type="button">outside</button>
        <FeedbackWidget />
      </div>
    );

    await user.click(screen.getByRole('button', { name: /open feedback/i }));
    expect(await screen.findByRole('button', { name: /quick thumbs up/i })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /outside/i }));
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /quick thumbs up/i })).toBeNull()
    );
  });

  it('quick-submit does not show Thanks when the server returns 500', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('boom', { status: 500 }));
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });

    render(<FeedbackWidget />);
    await user.click(screen.getByRole('button', { name: /open feedback/i }));
    await user.click(await screen.findByRole('button', { name: /quick thumbs up/i }));

    // Wait for the fetch to resolve, then assert no Thanks toast appeared.
    await waitFor(() => expect(screen.queryByText(/^Thanks!/)).toBeNull());
  });

  it('full-dialog submit sends the chosen reaction in the payload', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });

    render(<FeedbackWidget />);
    await user.click(screen.getByRole('button', { name: /open feedback/i }));
    await user.click(await screen.findByRole('button', { name: /open detailed feedback/i }));
    await user.click(screen.getByRole('button', { name: /^bug$/i }));
    await user.click(screen.getByRole('button', { name: /^send$/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
    const body = JSON.parse((fetchSpy.mock.calls[0][1] as RequestInit).body as string);
    expect(body.reaction).toBe('bug');
    expect(body.message).toBeNull();
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
