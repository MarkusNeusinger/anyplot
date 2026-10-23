### Added

- **Adopt mode for the implementation pipeline: `source_ref` on
  `impl-generate.yml` and `bulk-generate.yml`.** With it set, impl-generate
  takes the implementation file from that branch, tag or commit SHA instead of
  running Claude, renders it in both themes with the generator's commands,
  checks the canvas with `core.canvas`, and runs every later step unchanged:
  metadata, PR, staging upload, review, repair and merge. It exists so code
  written outside the pipeline, such as a `gemini/*` branch that migrates the
  323 MUI X implementations to MUI X 9, reaches main only through the Opus
  review, with metadata, quality score, GCS promotion and labels still owned by
  the pipeline. An adopted run is always a forced regeneration (`regen:forced`),
  the routed model only runs repair, the PR body and the metadata
  (`generated_by: adopted:<ref>`) name the source, and a missing file or a
  failed render is reported once without a retry, because a retry would read
  the same file. Python and JavaScript only for now.
