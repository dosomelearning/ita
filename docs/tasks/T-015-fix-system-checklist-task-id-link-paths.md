# T-015: Fix System Checklist Task-ID Link Paths

## Metadata

- Status: `done`
- Created: `2026-03-09`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-015`
- Related Modules: `docs/system-checklist.md`, `docs/tasks/README.md`, `AGENTS.md`

## Context

Task ID links in `docs/system-checklist.md` were introduced with `docs/tasks/...` paths.
Because the checklist file itself is inside `docs/`, those links resolve incorrectly and break navigation.

## Scope

In scope:

- Correct `ID` column links in `docs/system-checklist.md` to use `tasks/...` relative paths.
- Correct task-workflow rules so future rows use the same correct relative path.

Out of scope:

- Reworking task contents unrelated to link-path correctness.
- Closing the task before user verification.

## Acceptance Criteria

- [x] `T-015` backlog item added and set to `in_progress`.
- [x] All active `ID` links in `docs/system-checklist.md` use `tasks/...` relative paths.
- [x] Workflow/rules docs explicitly describe the correct relative path pattern.
- [x] User confirms links now resolve correctly.
- [x] Task is moved to `done` only on explicit user instruction.

## Implementation Notes

- Link paths must be correct relative to `docs/system-checklist.md`, not repository root.
- Rule wording is updated to prevent recurrence.

## Validation Evidence

- Command(s) run:
  - `sed -n '20,80p' docs/system-checklist.md`
  - `ls -1 docs/tasks | sort`
  - `rg -n "docs/tasks/T-|tasks/T-|ID cell must be a clickable markdown link|relative to docs/system-checklist" docs/system-checklist.md docs/tasks/README.md AGENTS.md`
- Manual checks:
  - Confirmed previous path pattern was incorrect for checklist-relative navigation.
- Output summary:
  - Link targets and workflow rules updated to checklist-relative path semantics.

## Change Log

- `2026-03-09` - Initial task file created and path-fix implementation applied.
- `2026-03-09` - Marked done after user verification; prepared closure commit.
