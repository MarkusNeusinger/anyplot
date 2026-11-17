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

/** A point of the origin timeline: its date (a month or a day), its release, and what it was. */
export interface OriginEvent {
  when: string;
  version?: string;
  what: string;
}

// The origin's points in date order. test_readme_claims.py holds each release to its heading in
// CHANGELOG.md (1.0.0 the oldest, so the first github release; 4.0.0 the release whose notes
// open with the public "use with my data" page) and the month to the origin's "it started in
// November 2025". Every dated point is a release, so each carries its version: the chat opened
// the evening before 4.0.0 came out, and the timeline shows the release.
export const ORIGIN_EVENTS: readonly OriginEvent[] = [
  { when: '2025-11', what: 'pyplots.ai' },
  { when: '2026-04-07', version: '1.0.0', what: 'first github release' },
  { when: '2026-04-23', version: '2.0.0', what: 'anyplot.ai' },
  { when: '2026-05-18', version: '2.4.0', what: 'r / ggplot2' },
  { when: '2026-06-10', version: '3.0.0', what: 'julia & javascript · 15 libraries' },
  { when: '2026-11-03', version: '4.0.0', what: 'use with my data' },
];

const MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];

/** How a point's date reads: a month as "nov 2025", a day as "2026-04-07 · 1.0.0" with its release. */
export function originDateLabel({ when, version }: OriginEvent): string {
  const [year, month, day] = when.split('-');
  const date = day ? when : `${MONTHS[Number(month) - 1]} ${year}`;
  return version ? `${date} · ${version}` : date;
}

/**
 * Splits a step's detail, such as "ai writes (per library)", into the action and the part in
 * brackets under it.
 */
export function splitDetail(does: string): [string, string | null] {
  const match = /^(.*?) (\(.+\))$/.exec(does);
  return match ? [match[1], match[2]] : [does, null];
}
