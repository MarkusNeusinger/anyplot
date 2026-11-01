### Fixed

- **Regenerations re-apply the plot title format.** The regeneration prompt now lists the title format (`{spec-id} · {language} · {library} · anyplot.ai`) under "Base style wins" and in its final check, so a regenerated implementation re-derives the title from the current rule instead of carrying over a predecessor's title that lacks the `{language}` segment. (#12500)
