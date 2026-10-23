### Added

- **Adopt mode records who wrote the code: `source_model` on
  `impl-generate.yml` and `bulk-generate.yml`.** The optional input names the
  model that wrote an adopted implementation, such as `gemini-4-argon`, and
  becomes the metadata's `generated_by`; without it `generated_by` stays
  `adopted:<ref>`. Every adopted file's metadata also gets a new key,
  `adopted_from: <ref> (<sha>)`, so the source commit survives after the
  `gemini/*` branch is gone. The PR body's `**Generation:**` line, the adopt
  commit and the run notices name the model, and every retry forwards it like
  `source_ref`. The value is checked as a model name and ignored with a
  warning without `source_ref`. Both workflows now reject a malformed
  `source_ref` or `source_model` without echoing it, since a newline in a
  dispatch value would start a workflow command, and `bulk-generate.yml` does
  so before its first dispatch. (#12297)
