import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import { CONFIG } from 'src/global-config';

describe('CONFIG.appVersion', () => {
  it('matches the [project] version in the repo-root pyproject.toml', () => {
    // Vitest runs with cwd = app/; under jsdom `import.meta.url` is an http URL,
    // so it can't be resolved to a path here.
    const pyproject = readFileSync(resolve(process.cwd(), '../pyproject.toml'), 'utf8');
    const version = /^version\s*=\s*"([^"]+)"/m.exec(pyproject)?.[1];

    // Guards the injection wired up in vite.config.ts / vitest.config.ts. If
    // this fails, the masthead's fallback version is lying about the release.
    expect(version).toBeDefined();
    expect(CONFIG.appVersion).toBe(version);
  });

  it('is a semver triple, not a placeholder', () => {
    expect(CONFIG.appVersion).toMatch(/^\d+\.\d+\.\d+/);
  });
});
