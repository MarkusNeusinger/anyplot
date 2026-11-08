# Change an existing spec through an issue

Use this page when an audit finds that the spec itself causes a defect: it
asks for the defect, contradicts itself, or several libraries fail the same
bullet. The channel was found on 2026-11-08 and has **never run end to
end**. File the first issue of a round alone and follow it to
`spec-ready` before you file more.

## The channel

No workflow on `main` changes an existing spec by itself (`spec-update.yml`
was deleted on 2026-01-08, commit `a4ddea45d`). Two workflows on `main`,
used together, make one:

1. **An issue titled `[<spec-id>] …` with the label `spec-request`.** The
   create job of `spec-create.yml` skips an issue whose title starts with a
   spec id, so it writes nothing.
2. **The owner's `@claude` comment on the issue.** `util-claude.yml` runs
   Claude Code for an OWNER, MEMBER or COLLABORATOR. Its `gh` uses the Claude
   app's token, so the pull request it opens is authored by `claude[bot]`, on
   the branch `specification/<spec-id>`.
3. **CI on the pull request.** A spec PR runs the unit tests and the spec
   characteristic check; the changelog check passes it as `plots/`-only.
4. **The owner's `approved` label on the issue.** The merge job of
   `spec-create.yml` checks that the sender is the repository owner, that the
   one open PR from `specification/<spec-id>` was opened by the Claude app,
   targets `main`, references the issue, and changes only
   `plots/<spec-id>/specification.md` and `specification.yaml` (a modified
   file passes, `automation/scripts/spec_pr_guard.py`). It then merges,
   dispatches `sync-postgres.yml` and labels the issue `spec-ready`.

Not verified, because no run was made:

- That `claude-code-action` in tag mode lets Claude push a branch named
  `specification/<spec-id>` and run `gh pr create`. The action first makes its
  own `claude/issue-<n>-…` branch; the comment tells Claude to cut the other
  branch itself. If the action refuses, the merge job finds no PR and comments
  a refusal; nothing merges.
- That `sync-labels.yml` stays harmless. It runs on every push to `main` and
  gives the spec's original issue (`issue:` in `specification.yaml`)
  `spec-ready`; the comment therefore forbids touching `issue:`.

Two owner decisions are open: whether this combination is the accepted spec
channel (then a docs PR describes it in `docs/workflows/overview.md`), or a
`spec-change` mode gets built; and the `[spec-id]` title prefix, which
`CLAUDE.md` forbids for new specs and which this channel needs.

## What the skill does, and what the owner does

| Step | Who | Gate |
|---|---|---|
| Write the issue text and the `@claude` comment into `$ROUND/spec-<spec-id>.md` | Claude | none, it is a draft |
| File the issue (`gh issue create --title "[<spec-id>] …" --label spec-request --body-file …`) | Claude | the owner's OK for that issue, by spec id |
| Post the `@claude` comment | the owner, or Claude when he names that action | it starts a Claude run |
| Read the PR diff and CI | Claude | none |
| Add `approved` to the issue | the owner | a Todoist task with the issue link |
| Regenerate the implementations the change affects | Claude, through `dispatch.sh` | the owner's OK for the queue |

Nothing regenerates by itself after the merge. The implementations written
against the old text stay until a `regen` line (or an adopted fix) replaces
them; list them in the draft.

## Issue template

**Title:** `[<spec-id>] <what changes, as a sentence-case phrase>`

**Labels:** `spec-request`

**Body:**

````markdown
## What changes

<The bullet or section as it is, and why it causes the defect. Name the
audit finding (round date and id), never a visitor's message.>

The change, in `plots/<spec-id>/specification.md` only:

```text
<the exact new lines>
```

Nothing else changes: no other bullet, no other section, and `## What a good
version looks like` stays byte-identical. <Adjust this sentence when the change
is in that section.>

## Why

<What the audit saw across libraries: the renders, the review lines, the
finding ids.>

## How this issue is processed

This issue uses the spec-create merge job for an existing spec: the
`[<spec-id>]` title prefix makes the create job skip it, an `@claude` comment
writes the change on `specification/<spec-id>`, and `approved` on this issue
merges it and syncs PostgreSQL.
````

## The `@claude` comment

````markdown
@claude Make the change this issue describes and open the pull request for spec-create's merge job:

1. Work on a branch named exactly `specification/<spec-id>`, cut from the current main: `git fetch origin main && git checkout -B specification/<spec-id> origin/main`.
2. Edit `plots/<spec-id>/specification.md`: <the exact edit, quoting the lines from the issue>. Change nothing else in the file.
3. Edit `plots/<spec-id>/specification.yaml`: set `updated:` to the output of `date -u +"%Y-%m-%dT%H:%M:%SZ"`. Change no other field; keep `issue:`, `created:` and the tags.
4. Commit only those two files with the message `spec: <summary>`, and push with `git push -u origin specification/<spec-id>`.
5. Open the PR with `gh pr create --base main --head specification/<spec-id> --title "spec: <summary>"` and a body that starts with `Related to #<this issue's number>` and shows the changed lines. Add no labels, enable no auto-merge, and merge nothing.
6. Comment the PR link on this issue and stop. Change no other file, branch or issue.
````

## Rules for the spec text

- A Data bullet that stays optional keeps the word "optional": the role
  parser (`core/spec_roles.py`) makes a role without it required.
- No numeric thresholds and nothing that contradicts Description, Data or
  Notes (the spec rules in `docs/workflows/overview.md`).
- Political or other sensitive specs keep invented parties and data.
