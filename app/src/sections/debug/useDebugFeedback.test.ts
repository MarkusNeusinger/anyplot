import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as api from 'src/lib/api';

import { useDebugFeedback } from './useDebugFeedback';

vi.mock('src/lib/api', () => ({
  fetchWithAuth: vi.fn(),
}));

describe('useDebugFeedback', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches feedback data', async () => {
    vi.mocked(api.fetchWithAuth).mockImplementation(async url => {
      if (url.includes('reaction=thumbs_up')) {
        return new Response(JSON.stringify([{ path: '/up', count: 5 }]), { status: 200 });
      }
      if (url.includes('reaction=thumbs_down')) {
        return new Response(JSON.stringify([{ path: '/down', count: 3 }]), { status: 200 });
      }
      if (url.includes('messages')) {
        return new Response(JSON.stringify([{ id: 'msg1', status: 'new' }]), { status: 200 });
      }
      return new Response('{}', { status: 200 });
    });

    const { result } = renderHook(() => useDebugFeedback('token', false, 0));

    await waitFor(() => {
      expect(result.current.topThumbsUp.length).toBe(1);
    });

    expect(result.current.topThumbsDown.length).toBe(1);
    expect(result.current.feedbackMessages.length).toBe(1);
  });

  it('handles update status optimistically', async () => {
    vi.mocked(api.fetchWithAuth).mockImplementation(async url => {
      if (url.includes('messages')) {
        return new Response(JSON.stringify([{ id: 'msg1', status: 'new' }]), { status: 200 });
      }
      return new Response('[]', { status: 200 });
    });

    const { result } = renderHook(() => useDebugFeedback('token', false, 0));

    await waitFor(() => {
      expect(result.current.feedbackMessages.length).toBe(1);
    });

    vi.mocked(api.fetchWithAuth).mockResolvedValueOnce(new Response('{}', { status: 200 }));

    act(() => {
      result.current.updateFeedbackStatus('msg1', 'done');
    });

    // Optimistic update
    expect(result.current.feedbackMessages[0].status).toBe('done');
  });

  it('reverts optimistic update on failure', async () => {
    vi.mocked(api.fetchWithAuth).mockImplementation(async url => {
      if (url.includes('messages')) {
        return new Response(JSON.stringify([{ id: 'msg1', status: 'new' }]), { status: 200 });
      }
      return new Response('[]', { status: 200 });
    });

    const { result } = renderHook(() => useDebugFeedback('token', false, 0));

    await waitFor(() => {
      expect(result.current.feedbackMessages.length).toBe(1);
    });

    vi.mocked(api.fetchWithAuth).mockRejectedValueOnce(new Error('Update failed'));

    await act(async () => {
      await result.current.updateFeedbackStatus('msg1', 'done');
    });

    // Reverted update
    expect(result.current.feedbackMessages[0].status).toBe('new');
  });
});
