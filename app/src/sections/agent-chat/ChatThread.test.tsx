import { describe, expect, it, vi } from 'vitest';

import { type AgentSessionState, initialAgentState } from 'src/hooks/useAgentSession';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { render, screen } from 'src/test-utils';

const notReady = (reason: string): AgentSessionState => ({
  ...initialAgentState('matplotlib'),
  phase: 'ready',
  sessionId: 'S1',
  items: [
    { id: 1, kind: 'action', action: 'create_plot', library: 'matplotlib' },
    {
      id: 2,
      kind: 'plot_failed',
      result: {
        status: 'not_ready',
        reason,
        attempts: 0,
        artifacts: [],
        changes: [],
        residual_defects: [],
        version: null,
      },
    },
  ],
});

function renderThread(state: AgentSessionState) {
  render(
    <ChatThread
      state={state}
      specId="scatter-basic"
      language="python"
      onRequestTheme={vi.fn()}
      onFetchArtifact={vi.fn()}
      onTrack={vi.fn()}
    />
  );
}

describe('ChatThread', () => {
  it('reads a plot refused for unconfirmed data as a step to take', () => {
    renderThread(notReady('data_unconfirmed'));
    expect(screen.getByText('plot · not ready · data_unconfirmed')).toBeInTheDocument();
    expect(
      screen.getByText(
        'confirm your data first: check the preview and the bindings, then .confirm()'
      )
    ).toBeInTheDocument();
  });

  it('keeps a generic line for a reason it does not know', () => {
    renderThread(notReady('something_new'));
    expect(screen.getByText('no plot this time')).toBeInTheDocument();
  });

  it("shows the page's own turns: the summary without a library, create_plot with it", () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [
        { id: 1, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
        { id: 2, kind: 'assistant', text: '12 rows and 3 columns.' },
        { id: 3, kind: 'action', action: 'create_plot', library: 'seaborn' },
      ],
    });
    const log = screen.getByRole('log');
    expect(log.children[0]).toHaveTextContent(/^❯\.summarize_data\(\)$/);
    expect(log.children[1]).toHaveTextContent('12 rows and 3 columns.');
    expect(log.children[2]).toHaveTextContent(/^❯\.create_plot\(\)# seaborn$/);
  });
});
