import { describe, expect, it, vi } from 'vitest';

import { PAGE_FRAME_SIZES, PREVIEW_RELAY_URL } from 'src/lib/agent';
import { InteractivePreview } from 'src/sections/agent-chat/InteractivePreview';
import { fireEvent, render, screen } from 'src/test-utils';

describe('InteractivePreview', () => {
  it('frames the relay sandboxed to scripts and posts the page once, on its first load', () => {
    render(<InteractivePreview page="<p>page</p>" square={false} title="Interactive plot" />);
    const frame = screen.getByTitle('Interactive plot') as HTMLIFrameElement;
    expect(frame).toHaveAttribute('src', PREVIEW_RELAY_URL);
    expect(frame).toHaveAttribute('sandbox', 'allow-scripts');
    expect(frame).toHaveAttribute('referrerpolicy', 'no-referrer');
    const post = vi.spyOn(frame.contentWindow as Window, 'postMessage');

    fireEvent.load(frame);
    // A second load (the frame navigated) gets nothing.
    fireEvent.load(frame);

    expect(post.mock.calls).toEqual([['<p>page</p>', '*']]);
  });

  it("keeps the wrapper's own size and scales it to the card", () => {
    render(<InteractivePreview page="<p>page</p>" square title="Interactive plot" />);
    const frame = screen.getByTitle('Interactive plot');
    expect(frame.style.width).toBe(`${PAGE_FRAME_SIZES.square.width}px`);
    expect(frame.style.height).toBe(`${PAGE_FRAME_SIZES.square.height}px`);
    expect(frame.style.transformOrigin).toBe('0 0');
    expect(getComputedStyle(screen.getByTestId('interactive-preview')).aspectRatio).toBe(
      '1232/1232'
    );
  });
});
