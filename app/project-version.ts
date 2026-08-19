import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

/**
 * Read the project version from the repo-root `pyproject.toml`.
 *
 * `pyproject.toml` is the single source of truth for the release version: the
 * release flow (`agentic/commands/release.md`) bumps it, tags `vX.Y.Z`, and
 * publishes the matching GitHub release. Vite injects the value as
 * `__APP_VERSION__` so the frontend has an honest version at build time — with
 * no second version field anyone has to remember to bump.
 *
 * Used by `vite.config.ts` and `vitest.config.ts`; runs in Node at config time,
 * never in the browser bundle.
 */
export function readProjectVersion(): string {
  const path = fileURLToPath(new URL('../pyproject.toml', import.meta.url));
  // Line-anchored so `python_version = "3.13"` under [tool.mypy] can't match;
  // the `[project]` table's own key is the only one at column 0.
  const match = /^version\s*=\s*"([^"]+)"/m.exec(readFileSync(path, 'utf8'));
  if (!match) throw new Error(`No [project] version found in ${path}`);
  return match[1];
}
