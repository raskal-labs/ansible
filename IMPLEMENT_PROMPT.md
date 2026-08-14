# Implementation

Implement the approved changes identified by the audit.

## Architectural Constraints

This repository is a configuration/deployment system for physical machines.

The current implementation targets one machine, while the architecture is intentionally designed to expand to multiple machines.

The architecture is:

CMS YAML -> Jinja/templates -> generated artifacts -> Ansible -> machine state

- CMS YAML remains the source of truth.
- Jinja/templates remain the translation layer.
- Generated files remain derived artifacts.
- Ansible remains the execution layer.
- `agent.md` is authoritative.
- `PROJECT.md` documents the actual project structure and readiness.

## Priority

1. Fix confirmed CRITICAL/HIGH operational defects.
2. Fix confirmed data-integrity and configuration defects.
3. Fix confirmed `agent.md` violations.
4. Complete important repository/documentation gaps.
5. Fix genuine multi-machine architectural problems.
6. Ignore cosmetic perfection unless it materially matters.

## Rules

Do not redesign the architecture unnecessarily.

Do not create duplicate sources of truth.

Do not move logic between CMS, templates, generated artifacts, and Ansible merely for stylistic reasons.

Preserve intentional abstractions needed for future multi-machine deployment.

Do not introduce generic boilerplate simply because it is conventional for GitHub repositories.

Make the smallest coherent change that resolves each confirmed issue.

Do not fix findings that were classified as unknown without first obtaining evidence.

## PROJECT.md

Update `PROJECT.md` to reflect the actual post-change repository.

For every significant component:

- maintain a concise one-line description
- use exactly one status:
  - ✅ Ready
  - ⚠️ Needs attention
  - ❌ Missing / broken

Do not mark something ✅ merely because it exists.

Add important newly created files.

Flag remaining incomplete components.

Keep `PROJECT.md` concise.

## Repository Documentation

Where the audit identifies a genuine need, create or improve useful repository documentation such as:

- `README.md`
- architecture documentation
- deployment instructions
- development/validation instructions
- examples
- tooling documentation

Do not create documentation boilerplate without a purpose.

## Validation

After implementation, perform all applicable existing repository validation.

At minimum, check:

- YAML validity
- Jinja/template validity
- Ansible syntax
- generated artifacts
- variable/reference consistency
- repository tooling
- `agent.md` compliance
- documentation consistency

Do not claim verification unless it was actually performed.

Do not make unrelated changes.

## Final Response

Report:

1. Files changed
2. Purpose of each change
3. Validation actually performed
4. Remaining confirmed issues
5. Remaining unknowns
6. Final operational-readiness assessment
