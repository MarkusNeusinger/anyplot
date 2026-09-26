import { afterEach, describe, expect, it, vi } from 'vitest';

import { ScrollToTopFab } from 'src/components/ScrollToTopFab';
import { act, fireEvent, render, screen, userEvent } from 'src/test-utils';

function setScrollY(y: number) {
  Object.defineProperty(window, 'scrollY', { value: y, configurable: true });
}

// By label, not role+name: a visibility:hidden element has no accessible name.
const getButton = () => screen.getByLabelText(/scroll to top/i);

describe('ScrollToTopFab', () => {
  afterEach(() => {
    setScrollY(0);
    vi.restoreAllMocks();
  });

  it('stays hidden near the top and fades in past the threshold', () => {
    setScrollY(0);
    render(<ScrollToTopFab />);
    expect(getButton()).not.toBeVisible();

    setScrollY(400);
    act(() => {
      fireEvent.scroll(window);
    });
    expect(getButton()).toBeVisible();

    setScrollY(100);
    act(() => {
      fireEvent.scroll(window);
    });
    expect(getButton()).not.toBeVisible();
  });

  it('shows at once when mounted on a restored scroll position', () => {
    setScrollY(400);
    render(<ScrollToTopFab />);
    expect(getButton()).toBeVisible();
  });

  it('scrolls smoothly back to the top on click', async () => {
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    setScrollY(400);
    const user = userEvent.setup();
    render(<ScrollToTopFab />);

    await user.click(getButton());
    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' });
  });
});
