### Fixed

- **The JavaScript render harness installs again on the Ubuntu 26.04 runner
  image.** GitHub moved `ubuntu-latest` to Ubuntu 26.04, and Playwright 1.55.1
  refused to install Chromium there, so every `impl-generate` and `impl-repair`
  run for Chart.js, D3, ECharts, Highcharts and MUI X failed in its setup step.
  Playwright moves to 1.64.1, which knows the new image and brings Chromium 156
  instead of 140; a sample of 17 catalogue snippets in both themes renders
  pixel-identical to the 1.55.1 renders. (#12259)
- **The lint job on `main` is green again after the move to Python 3.14.**
  `ruff format` now writes a multi-exception `except` without parentheses
  (PEP 758), and the two tokenizer fallbacks in `core/adaptability.py` and its
  mirror `automation/scripts/adaptability_check.py` still used the old form, so
  "CI: Lint and Format Check" failed on `main` and on every open PR's merge
  ref. Both now use the new form, with unchanged behavior. (#12259)
