import { describe, expect, it, vi } from 'vitest';

import { QualityTab } from 'src/sections/spec-detail/SpecTabs/QualityTab';
import { render, screen, userEvent } from 'src/test-utils';

const criteriaChecklist = {
  visual_quality: {
    score: 18,
    max: 20,
    items: [
      {
        id: 'vq1',
        name: 'Color harmony',
        score: 9,
        max: 10,
        passed: true,
        comment: 'Great palette',
      },
    ],
  },
  accuracy: {
    score: 15,
    max: 20,
    items: [],
  },
};

describe('QualityTab', () => {
  it('shows the rounded score over 100', () => {
    render(
      <QualityTab qualityScore={87.4} expandedCategories={{}} onToggleCategory={() => undefined} />
    );
    expect(screen.getByText('87/100')).toBeInTheDocument();
  });

  it('shows N/A when the score is null', () => {
    render(
      <QualityTab qualityScore={null} expandedCategories={{}} onToggleCategory={() => undefined} />
    );
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('calls onToggleCategory when a category with items is clicked', async () => {
    const user = userEvent.setup();
    const onToggleCategory = vi.fn();
    render(
      <QualityTab
        qualityScore={90}
        criteriaChecklist={criteriaChecklist}
        expandedCategories={{}}
        onToggleCategory={onToggleCategory}
      />
    );

    await user.click(screen.getByText('visual quality'));
    expect(onToggleCategory).toHaveBeenCalledWith('visual_quality');
  });

  it('does not call onToggleCategory for categories without items', async () => {
    const user = userEvent.setup();
    const onToggleCategory = vi.fn();
    render(
      <QualityTab
        qualityScore={90}
        criteriaChecklist={criteriaChecklist}
        expandedCategories={{}}
        onToggleCategory={onToggleCategory}
      />
    );

    await user.click(screen.getByText('accuracy'));
    expect(onToggleCategory).not.toHaveBeenCalled();
  });

  it('renders item details when the category is expanded via props', () => {
    render(
      <QualityTab
        qualityScore={90}
        criteriaChecklist={criteriaChecklist}
        expandedCategories={{ visual_quality: true }}
        onToggleCategory={() => undefined}
      />
    );

    expect(screen.getByTestId('ExpandLessIcon')).toBeInTheDocument();
    expect(screen.getByText('Color harmony')).toBeInTheDocument();
    expect(screen.getByText('9/10')).toBeInTheDocument();
    expect(screen.getByText('Great palette')).toBeInTheDocument();
  });

  it('shows the collapsed expand icon when the category is not expanded', () => {
    render(
      <QualityTab
        qualityScore={90}
        criteriaChecklist={criteriaChecklist}
        expandedCategories={{}}
        onToggleCategory={() => undefined}
      />
    );

    expect(screen.getByTestId('ExpandMoreIcon')).toBeInTheDocument();
    expect(screen.queryByTestId('ExpandLessIcon')).not.toBeInTheDocument();
  });

  it('shows the no-data message only when score and checklist are missing', () => {
    const { rerender } = render(
      <QualityTab qualityScore={null} expandedCategories={{}} onToggleCategory={() => undefined} />
    );
    expect(screen.getByText('No quality data available.')).toBeInTheDocument();

    rerender(
      <QualityTab qualityScore={75} expandedCategories={{}} onToggleCategory={() => undefined} />
    );
    expect(screen.queryByText('No quality data available.')).not.toBeInTheDocument();
  });
});
