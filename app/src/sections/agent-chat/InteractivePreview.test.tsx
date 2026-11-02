import { afterEach, describe, expect, it, vi } from 'vitest';

import { pageFrameSize, PREVIEW_RELAY_READY, PREVIEW_RELAY_URL } from 'src/lib/agent';
import {
  InteractivePreview,
  RELAY_READY_TIMEOUT_MS,
} from 'src/sections/agent-chat/InteractivePreview';
import { act, fireEvent, render, screen } from 'src/test-utils';

const SQUARE_PAGE = '<style>.frame { width: 1200px; height: 1200px; }</style><p>page</p>';

/** A message as the window receives it, from `source`. */
function message(data: unknown, source: Window | null) {
  act(() => {
    window.dispatchEvent(new MessageEvent('message', { data, source }));
  });
}

function mount(page = '<p>page</p>') {
  const onUnavailable = vi.fn();
  const view = render(
    <InteractivePreview page={page} title="Interactive plot" onUnavailable={onUnavailable} />
  );
  const frame = screen.getByTitle('Interactive plot') as HTMLIFrameElement;
  const relay = frame.contentWindow as Window;
  const post = vi.spyOn(relay, 'postMessage');
  return { frame, relay, post, onUnavailable, view };
}

describe('InteractivePreview', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('frames the relay sandboxed to scripts and posts the page only on its ready signal, once', () => {
    const { frame, relay, post } = mount();
    expect(frame).toHaveAttribute('src', PREVIEW_RELAY_URL);
    expect(frame).toHaveAttribute('sandbox', 'allow-scripts');
    expect(frame).toHaveAttribute('referrerpolicy', 'no-referrer');

    // A load is no signal: a page standing in at the relay's URL loads too.
    fireEvent.load(frame);
    expect(post).not.toHaveBeenCalled();

    message(PREVIEW_RELAY_READY, relay);
    message(PREVIEW_RELAY_READY, relay);

    expect(post.mock.calls).toEqual([['<p>page</p>', '*']]);
  });

  it('ignores the signal from any other window and any other message from the relay', () => {
    const { relay, post } = mount();

    message(PREVIEW_RELAY_READY, window);
    message(PREVIEW_RELAY_READY, null);
    message('ready', relay);
    message({ ready: true }, relay);

    expect(post).not.toHaveBeenCalled();
  });

  it('reports the relay unavailable when no signal comes in time, and not after the page went out', () => {
    vi.useFakeTimers();
    const waiting = mount();
    act(() => {
      vi.advanceTimersByTime(RELAY_READY_TIMEOUT_MS);
    });
    expect(waiting.onUnavailable).toHaveBeenCalledWith('relay_unavailable');
    waiting.view.unmount();

    const answered = mount();
    message(PREVIEW_RELAY_READY, answered.relay);
    act(() => {
      vi.advanceTimersByTime(RELAY_READY_TIMEOUT_MS * 2);
    });
    expect(answered.onUnavailable).not.toHaveBeenCalled();
  });

  it('stops listening and waiting once unmounted', () => {
    vi.useFakeTimers();
    const { relay, post, onUnavailable, view } = mount();
    view.unmount();

    message(PREVIEW_RELAY_READY, relay);
    act(() => {
      vi.advanceTimersByTime(RELAY_READY_TIMEOUT_MS);
    });

    expect(post).not.toHaveBeenCalled();
    expect(onUnavailable).not.toHaveBeenCalled();
  });

  it('frames the wrapper at its own size, read from the page, and scales it to the card', () => {
    mount(SQUARE_PAGE);
    const frame = screen.getByTitle('Interactive plot');
    expect(frame.style.width).toBe('1232px');
    expect(frame.style.height).toBe('1232px');
    expect(frame.style.transformOrigin).toBe('0 0');
    expect(getComputedStyle(screen.getByTestId('interactive-preview')).aspectRatio).toBe(
      '1232/1232'
    );
  });
});

describe('pageFrameSize', () => {
  it("reads the wrapper's first frame rule, whatever the page inside holds, and falls back to landscape", () => {
    const wrapper =
      '<style>.frame { margin: 16px auto; overflow: hidden; }\n' +
      '  .frame { width: 1200px; height: 1200px; }\n' +
      '  @media (max-width: 1111px) { .frame { width: 1080px; height: 1080px; } }</style>' +
      "<iframe srcdoc='<p>.frame { width: 10px; height: 10px; }</p>'></iframe>";
    expect(pageFrameSize(wrapper)).toEqual({ width: 1232, height: 1232 });
    expect(pageFrameSize('<p>no rule</p>')).toEqual({ width: 1632, height: 932 });
  });
});
