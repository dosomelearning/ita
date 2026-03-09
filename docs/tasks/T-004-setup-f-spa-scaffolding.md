# T-004: Set Up Frontend Scaffolding in f-spa

## Metadata

- Status: `done`
- Created: `2026-03-08`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-004`
- Related Modules: `f-spa`, `docs/system-checklist.md`

## Context

The repository already contains the `f-spa` module directory. The next step is to establish a clean frontend scaffold that future feature tasks can build on.

## Scope

In scope:

- Initialize/standardize frontend project structure in existing `f-spa` directory.
- Define baseline app entry points and foundational layout files.
- Define module-level canonical commands in `f-spa/README.md` (`install`, `test`, `lint`, `run`) once tooling is chosen.
- Keep scaffold aligned with mobile-first SPA intent.

Out of scope:

- Implementing full upload/auth/state feature flows.
- Final UI/UX polish.
- End-to-end integration with backend services.

## Acceptance Criteria

- [x] `f-spa` contains an agreed baseline scaffold structure for iterative feature work.
- [x] `f-spa/README.md` documents canonical commands for this module.
- [x] Scaffold decisions are documented without introducing cross-module coupling.

## Implementation Notes

- Preserve existing project conventions.
- Keep scaffold minimal and reversible.
- Defer advanced frontend architecture decisions until feature requirements are finalized.

## Validation Evidence

- Command(s) run:
  - `bash -n f-spa/scripts/deploy_spa.sh`
  - `npm install` (user run)
  - `./scripts/deploy_spa.sh` (user run)
- Manual checks:
  - Verified SPA scaffold builds and deploys to web hosting bucket without auth wiring.
  - Verified deploy script can auto-resolve CloudFront distribution ID from `ita-infra` stack outputs.
  - Verified TypeScript node-build configuration issue was resolved.
- Output summary:
  - Initial deployment failed with TypeScript errors (`Set`/`Symbol` unresolved in Vite node types) due to incomplete `tsconfig.node.json`.
  - Fixed by updating node TS config (`target/lib`, node types, `noEmit`) and adding `@types/node`.
  - Deployment then completed successfully using default profile `dev` and web bucket `ita-web-pxuzz47kqx`.

## Change Log

- `2026-03-08` - Initial draft.
- `2026-03-09` - SPA scaffold implemented, deploy script aligned to infra outputs/defaults, and TypeScript node-config deployment issue documented and resolved.
