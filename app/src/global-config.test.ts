import { describe, expect, it } from 'vitest';

import { CONFIG } from 'src/global-config';

describe('CONFIG.appVersion', () => {
  // The masthead renders this as its version whenever the GitHub releases
  // lookup has not answered or is unavailable, so an empty or placeholder value
  // is visible to visitors.
  //
  // It deliberately comes from app/package.json rather than the repo-root
  // pyproject.toml: the frontend image is built with
  // `docker build -f app/Dockerfile app`, so nothing above app/ exists at build
  // time. tests/unit/test_version_sync.py holds the two fields equal.
  it('is a semver triple, not a placeholder', () => {
    expect(CONFIG.appVersion).toMatch(/^\d+\.\d+\.\d+/);
  });
});
