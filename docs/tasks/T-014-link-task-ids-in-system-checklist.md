# T-014: Link Task IDs in System Checklist

## Metadata

- Status: `done`
- Created: `2026-03-09`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-014`
- Related Modules: `docs/system-checklist.md`, `docs/tasks/README.md`

## Context

The active backlog table in `docs/system-checklist.md` is frequently used for navigation.
Clickable task IDs improve speed and reduce friction when moving between backlog rows and detailed task docs.

## Scope

In scope:

- Convert each active backlog row `ID` cell to a clickable link pointing to that task's detailed markdown file in `docs/tasks/`.
- Keep table structure and existing task meaning unchanged.

Out of scope:

- Reworking task content itself.
- Closing task status or commit finalization (awaiting user verification).

## Acceptance Criteria

- [x] New `T-014` backlog item added and set to `in_progress`.
- [x] Active table task IDs are clickable links to detailed task files.
- [x] User confirms navigation works as expected.
- [x] Task is moved to `done` only on explicit user instruction.

## Implementation Notes

- This is a usability-only documentation improvement.
- Link targets use existing `docs/tasks/T-###-...md` files.

## Validation Evidence

- Command(s) run:
  - `ls -1 docs/tasks | sort`
  - `sed -n '1,200p' docs/system-checklist.md`
- Manual checks:
  - Verified linked ID format in active backlog table.
- Output summary:
  - Active backlog IDs are now direct navigation links.

## Change Log

- `2026-03-09` - Initial task file created and checklist ID-linking update applied.
- `2026-03-09` - Marked task done after user verification and explicit close instruction.
