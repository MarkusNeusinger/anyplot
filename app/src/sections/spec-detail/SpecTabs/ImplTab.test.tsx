import { describe, expect, it } from 'vitest';

import { ImplTab } from 'src/sections/spec-detail/SpecTabs/ImplTab';
import { render, screen } from 'src/test-utils';

const baseProps = {
  specId: 'scatter-basic',
  libraryId: 'matplotlib',
};

describe('ImplTab', () => {
  it('renders description, strengths, and weaknesses', () => {
    render(
      <ImplTab
        {...baseProps}
        imageDescription="A colorful scatter plot"
        strengths={['Clear layout']}
        weaknesses={['Missing legend']}
      />
    );

    expect(screen.getByText('A colorful scatter plot')).toBeInTheDocument();
    expect(screen.getByText('Strengths')).toBeInTheDocument();
    expect(screen.getByText('Clear layout')).toBeInTheDocument();
    expect(screen.getByText('Weaknesses')).toBeInTheDocument();
    expect(screen.getByText('Missing legend')).toBeInTheDocument();
  });

  it('shows the no-data message when no review data is present', () => {
    render(<ImplTab {...baseProps} />);
    expect(screen.getByText('No implementation review data available.')).toBeInTheDocument();
  });

  it('prefers generatedAt over updated and created in the metadata line', () => {
    render(
      <ImplTab
        {...baseProps}
        generatedAt="2025-01-15T00:00:00Z"
        updated="2025-02-20T00:00:00Z"
        created="2025-03-25T00:00:00Z"
      />
    );
    expect(screen.getByText(/scatter-basic · matplotlib · Jan 15, 2025/)).toBeInTheDocument();
  });

  it('falls back to updated, then created, for the metadata date', () => {
    const { rerender } = render(
      <ImplTab {...baseProps} updated="2025-02-20T00:00:00Z" created="2025-03-25T00:00:00Z" />
    );
    expect(screen.getByText(/scatter-basic · matplotlib · Feb 20, 2025/)).toBeInTheDocument();

    rerender(<ImplTab {...baseProps} created="2025-03-25T00:00:00Z" />);
    expect(screen.getByText(/scatter-basic · matplotlib · Mar 25, 2025/)).toBeInTheDocument();
  });

  it('omits the date from the metadata line when no date is available', () => {
    render(<ImplTab {...baseProps} />);
    expect(screen.getByText('scatter-basic · matplotlib')).toBeInTheDocument();
  });
});
