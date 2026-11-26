import { describe, expect, it } from 'vitest';

import { ContinuousCmapsSection } from 'src/sections/palette/ContinuousCmapsSection';
import {
  divStops,
  rampGradient,
  SEQ_STOPS,
  stopLabelStyle,
} from 'src/sections/palette/paletteHelpers';
import { render, screen } from 'src/test-utils';

describe('ContinuousCmapsSection', () => {
  it('renders the light theme stops of both ramps for fields and for marks', () => {
    render(<ContinuousCmapsSection isDark={false} />);

    expect(screen.getByRole('heading', { name: /continuous cmaps/i })).toBeInTheDocument();
    expect(screen.getAllByText('imprint_seq')).toHaveLength(2);
    expect(screen.getAllByText('imprint_div')).toHaveLength(2);
    expect(screen.getAllByText('fields · heatmaps / maps / filled contours')).toHaveLength(2);
    expect(screen.getAllByText('marks · points / lines / bars on the page')).toHaveLength(2);
    expect(screen.getByText(/shown here in the light theme/)).toBeInTheDocument();

    // pale mint starts the fields ramp; deep blue and dark violet end both sequential ramps
    expect(screen.getByText('#66E2B2')).toBeInTheDocument();
    expect(screen.getAllByText('#024582')).toHaveLength(2);
    expect(screen.getAllByText('#351E45')).toHaveLength(2);
    // the diverging midpoint: the page for fields, the muted ink for marks on light
    expect(screen.getByText('#FAF8F1')).toBeInTheDocument();
    expect(screen.getByText('#6B6A63')).toBeInTheDocument();
    expect(screen.queryByText('#404C02')).not.toBeInTheDocument();
  });

  it('switches to the dark theme stops', () => {
    render(<ContinuousCmapsSection isDark />);

    expect(screen.getByText(/shown here in the dark theme/)).toBeInTheDocument();
    expect(screen.getByText('#404C02')).toBeInTheDocument();
    expect(screen.getByText('#6F7E20')).toBeInTheDocument();
    expect(screen.getAllByText('#CDD9FF')).toHaveLength(2);
    expect(screen.getByText('#1A1A17')).toBeInTheDocument();
    // on dark the marks midpoint is the darker grey, not the muted ink, which would outshine the poles
    expect(screen.getByText('#686762')).toBeInTheDocument();
    expect(screen.queryByText('#A8A79F')).not.toBeInTheDocument();
    expect(screen.queryByText('#66E2B2')).not.toBeInTheDocument();
  });

  it('puts each colour label under its stop', () => {
    render(<ContinuousCmapsSection isDark={false} />);

    const labels = [...screen.getByTestId('imprint_seq-fields-labels').children] as HTMLElement[];
    expect(labels.map(label => label.textContent)).toEqual([
      '#66E2B2',
      '#009E73',
      '#024582',
      '#351E45',
    ]);
    expect(labels.map(label => [label.style.left, label.style.transform])).toEqual([
      ['0%', 'translateX(0%)'],
      ['36.9%', 'translateX(-50%)'],
      // close to the end: the label ends at its stop, clear of the end's label
      ['80.3%', 'translateX(-100%)'],
      ['100%', 'translateX(-100%)'],
    ]);
  });
});

describe('ramp helpers', () => {
  it('places every stop at its position in the gradient', () => {
    expect(rampGradient(SEQ_STOPS.fields.light)).toBe(
      'linear-gradient(to right, #66E2B2 0%, #009E73 36.9%, #024582 80.3%, #351E45 100%)'
    );
    expect(rampGradient(divStops('marks', 'dark'))).toBe(
      'linear-gradient(to right, #AE3030 0%, #686762 50%, #4467A3 100%)'
    );
  });

  it('aligns the end labels with the bar and centres the inner ones on their stop', () => {
    expect(stopLabelStyle(0)).toEqual({ left: '0%', transform: 'translateX(0%)' });
    expect(stopLabelStyle(0.32)).toEqual({ left: '32%', transform: 'translateX(-50%)' });
    expect(stopLabelStyle(0.5)).toEqual({ left: '50%', transform: 'translateX(-50%)' });
    expect(stopLabelStyle(1)).toEqual({ left: '100%', transform: 'translateX(-100%)' });
  });

  it('leans an inner label near an end away from the end label', () => {
    expect(stopLabelStyle(0.21)).toEqual({ left: '21%', transform: 'translateX(0%)' });
    expect(stopLabelStyle(0.803)).toEqual({ left: '80.3%', transform: 'translateX(-100%)' });
  });

  it('keeps one position per colour, from 0 to 1, in every ramp', () => {
    for (const use of ['fields', 'marks'] as const) {
      for (const theme of ['light', 'dark'] as const) {
        for (const { at, hex } of [SEQ_STOPS[use][theme], divStops(use, theme)]) {
          expect(at).toHaveLength(hex.length);
          expect(at[0]).toBe(0);
          expect(at[at.length - 1]).toBe(1);
          expect([...at].sort((a, b) => a - b)).toEqual(at);
        }
      }
    }
  });
});
