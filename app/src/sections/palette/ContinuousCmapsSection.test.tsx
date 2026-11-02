import { describe, expect, it } from 'vitest';

import { ContinuousCmapsSection } from 'src/sections/palette/ContinuousCmapsSection';
import { render, screen } from 'src/test-utils';

describe('ContinuousCmapsSection', () => {
  it('renders sequential (imprint_seq) and diverging (imprint_div) colormaps with endpoint stops', () => {
    render(<ContinuousCmapsSection />);

    expect(screen.getByRole('heading', { name: /continuous cmaps/i })).toBeInTheDocument();
    expect(screen.getByText('imprint_seq')).toBeInTheDocument();
    expect(screen.getByText('single-polarity · density / magnitude')).toBeInTheDocument();
    expect(screen.getByText('#009E73 brand-green')).toBeInTheDocument();

    expect(screen.getByText('imprint_div')).toBeInTheDocument();
    expect(screen.getByText('diverging · correlations / signed deviations')).toBeInTheDocument();
    expect(screen.getByText('#AE3030 red')).toBeInTheDocument();
    expect(screen.getByText('theme-adaptive midpoint')).toBeInTheDocument();
    expect(screen.getAllByText('#4467A3 blue')).toHaveLength(2);
    expect(screen.getByText('#FAF8F1')).toBeInTheDocument();
    expect(screen.getByText('#1A1A17')).toBeInTheDocument();
  });
});
