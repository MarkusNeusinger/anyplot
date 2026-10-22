### Security

- **vitest 4.1.12 in the frontend test setup.** Raises `vitest` and
  `@vitest/coverage-v8` from 4.1.11 so `app/yarn.lock` resolves
  `@vitest/mocker` 4.1.12, which closes the two Dependabot advisories on
  4.1.11 (code injection through unauthenticated manual mock registration,
  and the Windows backslash traversal of the redirect allowlist). Test-time
  only; nothing ships to the site. (#12241)
