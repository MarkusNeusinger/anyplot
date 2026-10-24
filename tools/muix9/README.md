# MUI X 9 migration tools (Gemini lane, issue #12296)

Working files for taking over Gemini's hand-overs on `gemini/12296-muix-9-remaining`
(draft PR #12304) and feeding them to the pipeline's adopt mode. This branch is never
merged; it exists so a session on another machine can resume. Everything here runs
from the repository root of a checkout with Node 24 (`source ~/.nvm/nvm.sh && nvm use 24`)
and `uv`.

## State on 2026-10-24 (hand-off)

- Done: Opus pilot (8), Gemini batch 1 (#12267, 20 files), chunk 1a (10 files, fixes on
  `claude/muix-9-c1a`), chunk 1b-1 (12 files, fixes on `claude/muix-9-c1b1`). 50 of 323
  muix files run on MUI X 9.
- Chunk 1 convention pass: Gemini redid the 76 held-back files (`lists/specs-drifted.txt`)
  in a fresh session, handed over at `5b2bcb3e5e4dc5b3685a669c07cf3ab1b9918f69`; all 76
  passed `conv-check.sh` and `acceptance2.sh` and were dispatched on 2026-10-24 at
  08:07:11 UTC (bulk run 40076791336) without a separate Claude review, because Gemini
  had applied the review findings from the PR comments. Collect the results with
  `START=2026-10-24T08:07:11Z tools/muix9/collect.sh <outdir>`, then site smoke and the
  ledger line. Chunk 1 (98 files) is then complete.
- Remaining: chunk 2 and chunk 3 (`lists/gemini-chunk-1`, `-2` hold 98 specs each;
  chunk 0 is done). Gemini continues on chunk 2 in the same branch; the owner restarts
  agy at each hand-over (about 25 files).
- Numbers so far: chunk 1a $1.60 per pair, first review mean 86.1, 5/10 without repair;
  chunk 1b-1 $1.48, 86.6, 7/12. Baselines: Gemini batch 1 $2.33, 83.0, 1/20; Opus pilot
  $3.15, 86, 2/8.

## Take-over procedure per hand-over

1. Read the hand-over SHA from the PR body (`gh pr view 12304 --json body --jq .body | grep -n SHA`)
   and the new spec list: `git fetch origin <sha> && git diff --name-only <previous-sha>..<sha> | sed -E 's#plots/([^/]+)/.*#\1#' | sort -u > /tmp/specs.txt`.
2. Worktree: `git worktree add --detach .claude/worktrees/gemini-12296 <sha>`, then `npm ci`
   inside it (Node 24). If the worktree exists, `git -C .claude/worktrees/gemini-12296 checkout --detach <sha>`.
3. Convention check first (cheap, catches drift): `tools/muix9/conv-check.sh <worktree> /tmp/specs.txt`.
   Every line must show `roles>=1 plot=1 col=0 DATA=0 sans=0`. Files that fail go back to
   Gemini as a PR comment; do not review or dispatch them.
4. Acceptance: `W=<worktree> LIST=/tmp/specs.txt OUT=/tmp/c<N> tools/muix9/acceptance2.sh`
   (renders both themes, canvas check, v7 grep, header check). Every line must show
   `light=0 dark=0 v7=0 headers=1` and both sizes on target. Look at the PNGs
   (`<OUT>/renders/<spec>/plot-{light,dark}.png`), a contact sheet is enough.
5. Independent review: run `tools/muix9/review-workflow.js` through the Workflow tool with
   `args: {"specs": [...]}`, after editing its two path constants (`S` = a directory with
   `acceptance.md` (the Constraints + Acceptance sections of issue #12296) and one
   `<spec>.diff` per spec from `git diff origin/main...<sha> -- <file>`; `W` = the worktree).
   Groups of 8 specs per Opus reviewer, verification capped at 24. Expect many medium
   findings; the ones that matter are "high" (render wrong, variant creep on `-basic`,
   dropped spec element, label contradicting data, chrome in palette colour, `t.amber`
   text on light, v7 class) and the recurring sweeps (dead guards, munged subtitles,
   typed scale maxima).
6. Fixes go on a Claude ref, never on Gemini's branch: in the worktree
   `git switch -c claude/muix-9-c<N>` from the hand-over SHA, one Opus delegate (brief
   pattern: confirmed findings + sweeps, Edit/Write only, one commit per spec, re-run
   acceptance, view renders, do not push), then push the ref and record its full SHA.
7. Dispatch from the full SHA, never a branch name:
   `gh workflow run bulk-generate.yml -f specification_id="$(tr '\n' ' ' < /tmp/specs.txt)" -f library=muix -f source_ref=<full sha> -f source_model=gemini-4-argon -f regen_gate=false`
   (`-f dry_run=true` first if unsure). Pacing is 180 s per pair; a bulk run holds about
   115 pairs, so a 98-spec chunk fits in one run.
8. Monitor: `START=<dispatch time ISO> tools/muix9/status.sh /tmp/specs.txt 560 3` (one line per
   cycle: merged count, runs, open PRs, failures). Merged check uses the PR search index,
   which lags by a few minutes.
9. After the merges: `START=<iso> tools/muix9/collect.sh /tmp/c<N>/eval` for costs and
   scores, `node scripts/site-smoke.mjs` (Node 24, `NODE_PATH` to a dir with playwright
   if the root `node_modules` is stale), a ledger line in `~/.claude/team-ledger.jsonl`
   (lane `gemini-interactive`), and a note in the Todoist task "Bulk-regenerate all 323
   MUI X implementations".
10. Feedback for Gemini goes as a comment on #12304 (Gemini reads it at its next session
    start; the owner restarts agy). Keep hand-overs at about 25 files per session.

## Close-out when all 294 are merged

Close #12304 without merging (comment with the pipeline PR range), close #12296, remove
the worktrees and local branches (`claude/muix-9-*` refs may stay on origin or be deleted),
write the final comparison into the Todoist task, re-enable daily-regen (Todoist task).
