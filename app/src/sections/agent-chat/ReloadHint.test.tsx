import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';

const { reloadWithoutWarning } = vi.hoisted(() => ({ reloadWithoutWarning: vi.fn() }));
vi.mock('src/hooks/useLeaveWarning', () => ({ reloadWithoutWarning }));

describe('ReloadHint', () => {
  it('reloads past the leave warning: the user asked for this reload', () => {
    render(<ReloadHint code="session_expired" />);
    fireEvent.click(screen.getByRole('button', { name: 'reload' }));
    expect(reloadWithoutWarning).toHaveBeenCalledTimes(1);
    // Called without arguments: the click event is no stand-in for the reload.
    expect(reloadWithoutWarning).toHaveBeenCalledWith();
  });

  it('offers a plain reload after no answer, and renders nothing for other codes', () => {
    // `/agent` is not behind Access: a reload signs nobody in, it checks the admin anew.
    const { container, rerender } = render(<ReloadHint code="unreachable" />);
    expect(screen.getByRole('button', { name: 'reload' })).toBeInTheDocument();
    rerender(<ReloadHint code="capacity" />);
    expect(container).toBeEmptyDOMElement();
  });
});
