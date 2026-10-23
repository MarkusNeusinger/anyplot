### Changed

- **The frontend tests run on Vitest 5.** `vitest` and `@vitest/coverage-v8`
  in `app/` move from 4.1.11 to 5.0.5, which also resolves `@vitest/mocker`
  5.0.5, outside the range of the two open `@vitest/mocker` advisories. The
  suite needed no config or test changes: it still covers the same 117 files
  with the same 1,168 tests, and the production bundle is unchanged, since
  Vitest is a test-time dependency only. (#12249)
