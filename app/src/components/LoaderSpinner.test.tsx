import { describe, it, expect } from 'vitest';
import { render } from '../test-utils';
import { LoaderSpinner } from './LoaderSpinner';

describe('LoaderSpinner', () => {
  it('renders without crashing', () => {
    const { container } = render(<LoaderSpinner />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('renders with small size', () => {
    const { container } = render(<LoaderSpinner size="small" />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('renders with large size by default', () => {
    const { container } = render(<LoaderSpinner />);
    expect(container.firstChild).toBeInTheDocument();
  });
});
