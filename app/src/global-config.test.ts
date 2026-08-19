import { describe, expect, it } from 'vitest';

import { CONFIG } from 'src/global-config';

describe('CONFIG.appVersion', () => {
  // Guards the `__APP_VERSION__` injection wired up in vite.config.ts and
  // vitest.config.ts. Drop the define from either one and this fails loudly
  // rather than silently shipping an undefined version — which is what the
  // masthead falls back to whenever the GitHub releases API is blocked or
  // rate-limits the visitor.
  //
  // The value's provenance is guarded at build time instead of here:
  // readProjectVersion() (app/project-version.ts) throws when it cannot find
  // the [project] version in pyproject.toml, and the frontend has no second
  // version field left to drift from. Re-reading the file in this suite is not
  // an option either — the frontend does not depend on @types/node, and
  // `yarn type-check` type-checks the tests via tsconfig.test.json.
  it('is injected from pyproject.toml as a semver triple', () => {
    expect(CONFIG.appVersion).toMatch(/^\d+\.\d+\.\d+/);
  });
});
