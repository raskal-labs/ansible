# Operational Audit

You are auditing this repository as a principal infrastructure engineer.

## System Context

This repository is a configuration and deployment system for physical machines.

The current implementation targets one machine, but the architecture is intentionally designed to expand to additional machines.

The architectural model is:

CMS YAML -> Jinja/templates -> generated artifacts -> Ansible -> machine state

- CMS YAML is the configuration source of truth.
- Jinja/templates are the translation layer.
- Generated files are derived artifacts.
- Ansible is the execution/configuration layer.
- `agent.md` is the governing specification.
- `PROJECT.md` is the human-readable project map and readiness overview.

Treat the repository root as the complete project boundary.

Inspect the repository broadly enough to understand all dependencies. Do not assume that only YAML and Ansible files matter.

## Audit Priority

### 1. CRITICAL — Operational Readiness

First determine whether the router, networking, bootstrap path, and other critical infrastructure can actually be configured and operate successfully.

Trace important configuration paths end-to-end:

CMS data
-> template/translation
-> generated artifact
-> Ansible variable/inventory
-> task/role
-> intended machine state

Look for broken or missing:

- variables
- references
- transformations
- generated artifacts
- dependencies
- tasks
- handlers
- prerequisites
- ordering
- configuration relationships
- bootstrap requirements
- networking/router configuration

Check all of this against `agent.md`.

### 2. IMPORTANT — Complete System Correctness

Determine whether the rest of the currently implemented machine configuration is internally consistent and operationally viable.

Check:

- CMS integrity
- templates
- generated configuration
- inventory
- playbooks
- roles
- variables
- handlers
- services
- configuration files
- validation tooling
- generation/compilation tooling
- dependencies
- idempotency where relevant
- `agent.md` compliance

### 3. REPOSITORY QUALITY

Assess whether the repository is complete and understandable as a professional GitHub project.

Consider whether it needs useful files such as:

- `README.md`
- architecture documentation
- deployment instructions
- development/validation instructions
- examples
- `.gitignore`
- CI/validation configuration
- `LICENSE`, where appropriate
- other genuinely useful documentation or repository metadata

Do not create boilerplate merely because it is conventional.

Classify repository additions as:

- NECESSARY
- RECOMMENDED
- OPTIONAL

### 4. MULTI-MACHINE ARCHITECTURE

The system is intentionally designed to expand beyond the current machine.

Identify genuine architectural problems that would prevent or materially hinder that expansion.

Do not criticize abstractions merely because only one machine currently exists.

Do not demand premature generalization.

### 5. PERFECTION

This is the lowest priority.

Do not treat subjective style, cosmetic refactoring, theoretical best practices, or architectural preferences as defects unless they materially affect:

- operation
- data integrity
- `agent.md`
- the intended architecture

## Compiler / Data-Flow Audit

This is not merely an Ansible repository.

Investigate the actual relationship between:

- `compile.py`
- `tools/compile.py`
- `data/`
- `generated/`
- `ansible/data/`
- `ansible/generated/`
- `ansible/site.yml`
- `ansible/playbooks/site.yml`
- `ansible/tools/`
- Ansible roles

Do not assume that duplicated-looking files are defects.

Determine which are:

- authoritative
- generated
- compatibility layers
- wrappers
- obsolete
- competing sources of truth

Establish the actual data and control flow before reporting a problem.

## PROJECT.md

Use `PROJECT.md` as the declared project map.

Compare it against the actual repository.

For every significant listed component:

1. Verify that it exists.
2. Inspect its purpose.
3. Determine whether it is complete.
4. Determine whether it is operationally ready.
5. Check it against `agent.md`.
6. Provide a concise one-line description.
7. Assign exactly one status:

- ✅ Ready
- ⚠️ Needs attention
- ❌ Missing / broken

Do not mark something ✅ merely because it exists.

Also identify:

- repository items missing from `PROJECT.md`
- `PROJECT.md` entries missing from the repository
- important components that should exist but do not
- obsolete or misplaced entries

Do not modify `PROJECT.md` during this audit.

## Evidence Rules

Every substantive finding must identify:

- severity
- category
- exact file/path
- relevant key, variable, task, or dependency
- evidence
- impact
- confidence

Severity:

- CRITICAL
- HIGH
- MEDIUM
- LOW
- INFO

Categories:

- EXECUTION
- DATA-INTEGRITY
- AGENT.MD
- CONFIGURATION
- OPERATIONAL
- REPOSITORY
- DOCUMENTATION
- SCALABILITY
- BEST-PRACTICE

If the repository does not contain enough evidence to establish something, report `UNKNOWN`.

Do not guess.

## Final Report

Return:

1. Critical infrastructure verdict
2. Overall operational-readiness verdict
3. `agent.md` compliance verdict
4. Confirmed blockers
5. High-priority defects
6. Complete-system issues
7. Repository/documentation gaps
8. Multi-machine scalability concerns
9. Low-priority observations
10. Unknowns requiring verification
11. Recommended changes ordered by operational importance
12. Proposed `PROJECT.md` status updates

This is an audit.

Do not modify, create, delete, reformat, or fix anything.
