### Removed

- **The unused `agents-eval` extra.** It installed `google-adk[eval]`, whose
  eval stack brought litellm and nltk into `uv.lock` (29 packages in all),
  and with them two Dependabot alerts: litellm's SSRF (no fixed version
  reachable on Python 3.13, because google-cloud-aiplatform caps it below
  1.86) and nltk's path check (no fixed version at all). No workflow, image
  or script used the extra: the evals under `agents/evals/` run on the
  `agents` extra. (#12146)
