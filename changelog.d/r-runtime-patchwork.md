### Changed

- **The R pipeline runtime installs `patchwork`, and the ggplot2 prompt names it.**
  `.github/actions/setup-r/action.yml`, which `impl-generate` and `impl-repair`
  use, adds `patchwork` to the packages it installs, and
  `prompts/library/ggplot2.md` lists it for composing several ggplot objects
  into one mosaic or grid layout; `subplot-mosaic`, `upset-basic` and
  `waffle-basic` use it. The change arrived inside the `subplot-mosaic`
  implementation PR: a repair attempt edited both files beside the plot,
  although the repair prompt stages only the implementation file, and nothing
  in review, merge or the changelog gate refused a pipeline PR touching paths
  outside `plots/`. (#11725)
