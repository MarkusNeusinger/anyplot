import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { FactTable } from 'src/components/FactTable';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('FactTable', () => {
  it('sets the label apart from the fact: weight and width go to the row header only', () => {
    render(
      <FactTable
        rows={[
          ['hosting', 'Google Cloud, europe-west4'],
          ['source', 'GitHub'],
        ]}
        labelWidth="30%"
      />
    );
    const label = screen.getByRole('rowheader', { name: 'hosting' });
    const fact = screen.getByRole('cell', { name: 'Google Cloud, europe-west4' });
    expect(getComputedStyle(label).fontWeight).toBe('500');
    expect(getComputedStyle(label).width).toBe('30%');
    expect(getComputedStyle(fact).fontWeight).not.toBe('500');
    expect(getComputedStyle(fact).width).not.toBe('30%');
  });

  it('logs nothing while it renders', () => {
    // Emotion reports a selector it cannot render on a server (such as `:first-child`) as a
    // console error on every page that shows the table. It does so when it first inserts a
    // style, so this table takes a width no other test here uses.
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(<FactTable rows={[['hosting', 'Google Cloud']]} labelWidth="27%" />);
    expect(error).not.toHaveBeenCalled();
  });
});
