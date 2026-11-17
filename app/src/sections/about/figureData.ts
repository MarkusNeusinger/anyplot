/**
 * The words and numbers of the about page's figures, apart from their components so each figure's
 * module exports only its component (Fast Refresh) and tests/unit/test_readme_claims.py can hold
 * the numbers in this file to their sources.
 */

/** A step of the catalogue pipeline: its name, what happens in it, and what I do in it. */
export interface PipelineStep {
  step: string;
  does: string;
  me?: string;
}

// The criteria and the repair count are the ones impl-review.yml applies; test_readme_claims.py
// holds both to their sources, so each detail stays in one string with its action.
export const PIPELINE_STEPS: readonly PipelineStep[] = [
  { step: 'idea', does: 'a github issue' },
  { step: 'spec', does: 'ai drafts', me: 'I approve' },
  { step: 'code', does: 'ai writes (per library)' },
  { step: 'review', does: 'ai scores (24 criteria)' },
  { step: 'fix', does: 'ai repairs (up to 4 times)' },
];

export const PIPELINE_RULES = { step: 'rules', me: 'I set and change them' } as const;

// The rubric's six parts in its order, each with its points, named as the review section names
// them. test_readme_claims.py holds the points to the table in prompts/quality-criteria.md and the
// caption's total and criteria to the criteria registry.
export const RUBRIC_PARTS: readonly (readonly [string, number])[] = [
  ['visual quality', 30],
  ['design', 20],
  ['spec compliance', 15],
  ['data quality', 15],
  ['code quality', 10],
  ['library mastery', 10],
];

export const RUBRIC_CAPTION = '// rubric · 100 points · 24 criteria';

/** Splits "ai scores (24 criteria)" into the action and the detail in brackets under it. */
export function splitDetail(does: string): [string, string | null] {
  const match = /^(.*?) (\(.+\))$/.exec(does);
  return match ? [match[1], match[2]] : [does, null];
}
