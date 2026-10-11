import { describe, expect, it } from 'vitest';

import { StepHeader } from 'src/sections/agent-chat/StepHeader';
import { render, screen, within } from 'src/test-utils';

describe('StepHeader', () => {
  it('names both steps and marks the data step as current until the data is confirmed', () => {
    render(<StepHeader current={1} />);
    const steps = within(screen.getByRole('list', { name: 'Steps' })).getAllByRole('listitem');
    expect(steps.map(step => step.textContent)).toEqual(['1 data', '·2 plot']);
    expect(screen.getByText('1 data')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('2 plot')).not.toHaveAttribute('aria-current');
  });

  it('marks the plot step as current after the confirmation', () => {
    render(<StepHeader current={2} />);
    expect(screen.getByText('2 plot')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('1 data')).not.toHaveAttribute('aria-current');
  });
});
