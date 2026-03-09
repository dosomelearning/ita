# AGENTS Instructions for `4-ita`

These instructions apply to `/home/raven/data/sc/uni/4-ita` and override global defaults only where explicitly stated.
Global instructions from `/home/raven/.codex/AGENTS.md` are valid unless this file says otherwise.

## Session Start
- At the beginning of each session, read `docs/tasks/README.md` and `docs/system-checklist.md` before starting work.
- Treat those files as mandatory working context for task IDs, backlog status, and item lifecycle.

## Scope and Access
- Allowed read/write scope without extra approval:
  - `/home/raven/data/sc/uni/4-ita` (this project)
  - `/home/raven/.codex` (Codex config and skills)
- Any access outside those paths (for example `/etc`, `/var`, other home paths) requires explicit user approval first.
- Never run destructive commands unless explicitly requested.
- For shell commands, always show the exact command before execution.

## Environment
- OS baseline: Fedora 43 (or newer).
- IDEs in use: JetBrains PyCharm and WebStorm.
- Never use login shell for commands (`login=false`).

## Stack and Structure
- Frontend: React + TypeScript.
- Backend: Python 3.12 with AWS SAM.
- Infrastructure ownership model:
  - `b-infra` owns only shared/foundational platform resources.
  - Each backend microservice (`b-ms1-ingress`, `b-ms2-detection`, `b-ms3-faces`, `b-ms4-statemgr`) owns its own SAM template and service-owned resources.
  - Monorepo layout does not relax service isolation or autonomy.
- Python environment for agent-run Python commands:
  - Always use `conda run -n conda_py_env_312 ...`.
  - Do not assume shell activation.
- Canonical top-level directories are locked and must not be renamed without approval:
  - `b-infra`
  - `b-ms1-ingress`
  - `b-ms2-detection`
  - `b-ms3-faces`
  - `b-ms4-statemgr`
  - `f-spa`
  - `img`

## Architecture Source of Truth
- Root `README.md` contains the full project/system description and architecture overview.
- Each module/microservice/frontend must have its own detailed `README.md`.
- Keep README cross-links coherent:
  - Root `README.md` must link all module READMEs.
  - Module READMEs should link back to root `README.md` and peer module docs.
- Maintain a root "working map" in `README.md` with ordered reading flow:
  - root `README.md` -> module `README.md` files -> diagrams in `img/`.
- Architecture must align with diagram guidance in `img/` (currently `img/ita-arch-diag1.png`).
- If implementation/docs conflict with diagrams or architecture intent, stop and ask.
- Small architecture adjustments are allowed, but direction remains aligned with the diagram and project goals.

## Project-Specific Functional Constraints
- The app is a demo of resilient serverless architecture on AWS.
- Frontend is SPA, optimized for mobile photo capture/upload.
- Backend processes photos with Rekognition, extracts faces, and returns face images for frontend use.
- No Cognito auth in this project.
- A shared one-time password flow is required:
  - Instructor-defined shared password stored in SSM Parameter Store.
  - `b-ms1-ingress` issues presigned URL only when password matches.
  - Invalid password requests must be rejected before entering protected flow.
- All API Gateway endpoints must enforce rate limiting.

## AWS and SAM Guardrails
- AWS CLI defaults for scripted/project commands:
  - `--profile dev`
  - Region `eu-central-1`
  - `AWS_CLI_AUTO_PROMPT=off`
  - `AWS_PAGER=""`
  - `AWS_EC2_METADATA_DISABLED=true`
  - Always include `--no-cli-pager`
- Do not run AWS write operations (create/update/delete/modify), including `sam deploy`, without explicit per-command approval.
- For potentially destructive AWS actions, present exact command and request approval before execution.

## Coding and Documentation Rules
- Keep diffs minimal and focused; avoid unrelated refactors.
- Prefer explicit naming; avoid magic constants.
- Follow established project conventions; if none exist, use common standards and state assumptions.
- Task tracking policy is defined in `docs/tasks/README.md`; follow it for ID issuance, status updates, and backlog handling.
- On each new user-requested task, add/update the corresponding `T-###` item in `docs/system-checklist.md` per `docs/tasks/README.md`.
- In `docs/system-checklist.md` active backlog rows, keep the `ID` column as clickable links to the corresponding detailed task files in `docs/tasks/`.
- For detailed task files where architecture decisions are relevant, include an `AD Dependencies` section that lists related `AD-###` entries with short implementation-impact notes.
- Commit intent tags are mandatory for task-related commits:
  - `[checkpoint]` for partial/in-progress synchronization commits.
  - `[close]` for task-closure commits.
- A task may be set to `done` only on explicit user instruction.
- `[checkpoint]` commits are allowed for tasks in `todo`, `in_progress`, or `blocked`; task stays in active backlog.
- `[close]` commits are allowed only after explicit user instruction to set the task to `done`; closed task must be removed from active backlog in the same commit.
- All task-related commit messages must reference the relevant `T-###` ID(s).
- Public-repo privacy rule: never include PII in code, docs, examples, logs, screenshots, task trackers, or commit messages.
- Do not use private-environment identifiers (usernames, hostnames, local account handles, personal emails, or similar metadata) in repository content.
- Preserve service boundaries in code and docs:
  - Do not move service-owned resources into `b-infra`.
  - Do not create hidden runtime coupling between microservices unless explicitly documented and approved.
- As modules are created, define and document canonical `install`/`test`/`lint`/`run` commands in that module's `README.md`.
- Do not assume commands for a module until they are documented.
- Do not edit `.idea/` files unless explicitly requested.

## Testing and Git
- Do not skip tests unless explicitly instructed.
- Run relevant tests after changes; if tests do not exist yet, do minimal manual validation and report exactly what was validated.
- Git is a primary project tool for understanding and tracking work:
  - Use read-only git commands (`git status`, `git diff`, `git log`, `git show`) regularly to navigate progress and validate assumptions.
  - Prefer referring to concrete git diffs/history when summarizing what changed.
- Commit message style for this project:
  - Subject line in imperative mood.
  - Multi-line body built with one bullet per logical change and blank lines between bullets.
- Push workflow:
  - User pushes to remote repositories exclusively.
  - Agent may prepare commits and all local git operations only with explicit user approval.
- Do not commit unless explicitly approved by the user.
- Read-only git commands are allowed; destructive/history-rewriting commands are not allowed unless explicitly requested.
