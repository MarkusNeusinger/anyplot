"""The programs lets-plot's native ImageMagick can start, which no render may find on the sandbox's `PATH`.

lets-plot rasterises in its native bridge (`lets_plot_kotlin_bridge`), which links ImageMagick 7.
That ImageMagick is a zero-configuration build: it reads no `policy.xml` and no `MAGICK_*`
variable (measured on 2026-10-26, on a developer machine and in the renderer image), and its
delegate map, compiled in, starts the programs below by name from `PATH` through `execvp`,
`popen` and `system`. A native process start raises no audit event, so the harness's plot guard
cannot refuse one. The security review of 2026-10-26 found no route from code the validator
admits to a delegate; this module keeps a delegate from being there to start when the base image
or a dependency changes.

The renderer image's build runs it (`agents/renderer/Dockerfile`), so every build of the image
fails when one of the programs is on `SANDBOX_PATH`, the path every sandboxed run gets: the Cloud
Build deploy and the CI image job build the same file, and the CI job runs it once more in the
built image (`.github/workflows/ci-image.yml`). The list is the brief of that review (the
programs ImageMagick's delegates and fonts reach for) plus every other program the bridge's
delegate map names. `node` stays on it: the image ships Node at `/opt/node/bin/node`, which the
JavaScript row runs by its path (`commands.NODE_BINARY`) and `SANDBOX_PATH` does not carry.

    .venv/bin/python -m agents.renderer.delegates

exits 0 and prints one line when none is found, and exits 1 naming each one that is.
"""

import shutil

from .executor import SANDBOX_PATH


DELEGATE_PROGRAMS: tuple[str, ...] = (
    "gs",
    "ghostscript",
    "curl",
    "wget",
    "soffice",
    "libreoffice",
    "ffmpeg",
    "inkscape",
    "rsvg-convert",
    "fc-list",
    "fc-match",
    "magick",
    "convert",
    "identify",
    "dot",
    "java",
    "node",
    # The other programs of the bridge's compiled-in delegate map.
    "bpgdec",
    "bpgenc",
    "xdg-open",
    "uniconvertor",
    "ufraw-batch",
    "dvips",
    "xterm",
    "hp2xx",
    "html2ps",
    "ilbmtoppm",
    "ppmtoilbm",
    "lepton",
    "JxrDecApp",
    "JxrEncApp",
    "pcl6",
    "gxps",
    "xclip",
    "cwebp",
    "dwebp",
    "lpr",
    "mrsidgeodecode",
    "gimp",
)
"""Every program a render must not find on `SANDBOX_PATH`."""


def delegates_on_path(path: str = SANDBOX_PATH) -> dict[str, str]:
    """The delegate programs `path` resolves, by name: empty in a correct image."""
    found = {name: shutil.which(name, path=path) for name in DELEGATE_PROGRAMS}
    return {name: location for name, location in found.items() if location is not None}


def main() -> int:
    found = delegates_on_path()
    if found:
        listed = ", ".join(f"{name} ({location})" for name, location in sorted(found.items()))
        print(f"delegate programs on the sandbox PATH {SANDBOX_PATH}: {listed}")
        return 1
    print(f"OK: none of {len(DELEGATE_PROGRAMS)} delegate programs on {SANDBOX_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
