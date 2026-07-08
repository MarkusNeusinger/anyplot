# Catalog Status

Answer the recurring catalog questions from origin/main with one reproducible procedure,
instead of re-deriving ad-hoc pipelines each session: light/dark migration state, per-spec
library coverage, and open impl-PR classification.

## Instructions

- **Always `git fetch origin main` first** — every query below reads `origin/main`, and a
  stale fetch has produced wrong counts that the user had to correct.
- Counts drift with the pipeline — report the numbers WITH the fetch timestamp.
- The canonical library registry is `core/constants.py` (15 libraries, 4 languages);
  derive expected coverage from it, never from a hardcoded list.

## Run

1. `git fetch origin main`
2. **Light/dark migration state** (old single-image impls have `preview_url:`; migrated
   dual-theme impls have `preview_url_light:`):

```bash
git grep -lE '^preview_url:' origin/main -- 'plots/*/metadata/*' | sed 's|[^:]*:plots/\([^/]*\)/.*|\1|' | sort -u > /tmp/old_specs.txt
git grep -lE '^preview_url_light:' origin/main -- 'plots/*/metadata/*' | sed 's|[^:]*:plots/\([^/]*\)/.*|\1|' | sort -u > /tmp/new_specs.txt
echo "fully-old: $(comm -23 /tmp/old_specs.txt /tmp/new_specs.txt | wc -l)  partial: $(comm -12 /tmp/old_specs.txt /tmp/new_specs.txt | wc -l)  fully-migrated: $(comm -13 /tmp/old_specs.txt /tmp/new_specs.txt | wc -l)"
comm -23 /tmp/old_specs.txt /tmp/new_specs.txt   # the fully-old list
```

3. **Per-spec library coverage** (which of the 15 libs have an implementation file):

```bash
for spec in <spec-ids or all>; do
  n=$(git ls-tree -r --name-only origin/main "plots/$spec/implementations/" 2>/dev/null | wc -l)
  echo "$spec: $n/15"
done
```

For the missing-lib detail of one spec, list the files and diff against the registry in
`core/constants.py`.

4. **Open impl-PR classification** (spec, library, dual-theme vs old, blocking label):

```bash
gh pr list --label "ai-review-failed" --json number,title,labels --jq '.[] | "\(.number) \(.title) [\([.labels[].name] | join(","))]"'
gh pr list --search "is:open label:ai-rejected" --json number,title --jq '.[] | "\(.number) \(.title)"'
```

Impl-PR titles carry spec + library; map to issues via the `Fixes #N` in the PR body when
needed. Remediation paths (re-review vs fresh regen) are in the babysit-pipeline skill and
the light/dark migration memory.

## Report

Three short sections — migration counts (old/partial/migrated + the fully-old list),
coverage table for the queried specs, and open impl-PRs with their blocking state. Include
the fetch timestamp.
