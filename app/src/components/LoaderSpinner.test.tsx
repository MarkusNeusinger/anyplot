import { describe, expect, it } from 'vitest';

import { LoaderSpinner } from 'src/components/LoaderSpinner';
import { render } from 'src/test-utils';

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
