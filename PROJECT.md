# Project

## Overview

Configuration and deployment system for physical infrastructure.

The current deployment target is one machine, while the architecture is designed to support multiple machines and network devices.

## Architecture

CMS / Source Data
        |
        v
    compile.py
        |
        v
Generated Configuration
        |
        v
     Ansible
        |
        v
Machine / Infrastructure State

### Governing Specification

`agent.md` defines the project's requirements, constraints, conventions, and architectural rules.

### Source of Truth

The files under `data/` are intended to be the authoritative configuration data. Generated files are derived artifacts and must not become competing sources of truth.

## Repository Map

Status is initially ⚠️ because components have not yet been audited.

Legend:

- ✅ Ready — verified complete and operational for its intended role
- ⚠️ Needs attention — incomplete, uncertain, inconsistent, or requires work
- ❌ Missing / broken — absent or substantially non-functional

| Path | Description | Status |
|---|---|---|
| `agent.md` | Governing project specification and implementation rules. | ⚠️ |
| `PROJECT.md` | Human-readable project map and readiness overview. | ⚠️ |
| `Makefile` | Project-level command interface. | ⚠️ |
| `compile.py` | Root configuration compiler/entry point. | ⚠️ |
| `data/` | Authoritative infrastructure configuration data. | ⚠️ |
| `data/environment.yaml` | Global environment configuration. | ⚠️ |
| `data/identities.yaml` | Identity definitions. | ⚠️ |
| `data/inventory/` | Network and infrastructure inventory data. | ⚠️ |
| `data/networks/` | Network and VLAN definitions. | ⚠️ |
| `data/nodes/` | Machine/node definitions. | ⚠️ |
| `data/services/` | Service definitions. | ⚠️ |
| `generated/` | Root generated deployment artifacts. | ⚠️ |
| `tools/` | Compilation, migration, and validation tooling. | ⚠️ |
| `ansible/` | Ansible configuration and deployment system. | ⚠️ |
| `ansible/ansible.cfg` | Ansible configuration. | ⚠️ |
| `ansible/data/` | Ansible-local data. | ⚠️ |
| `ansible/generated/` | Ansible-generated deployment artifacts. | ⚠️ |
| `ansible/group_vars/` | Ansible group variables and security configuration. | ⚠️ |
| `ansible/playbooks/` | Ansible deployment playbooks. | ⚠️ |
| `ansible/roles/` | Reusable Ansible system and service configuration roles. | ⚠️ |
| `ansible/tools/` | Ansible-specific validation and migration tooling. | ⚠️ |
| `README.md` | Human-facing project overview, architecture, usage, and deployment documentation. | ❌ |

## Repository Tree

.
├── Makefile
├── compile.py
├── data/
│   ├── environment.yaml
│   ├── identities.yaml
│   ├── inventory/
│   ├── networks/
│   ├── nodes/
│   └── services/
├── generated/
├── tools/
└── ansible/
    ├── ansible.cfg
    ├── data/
    ├── generated/
    ├── group_vars/
    ├── playbooks/
    ├── roles/
    ├── tools/
    └── site.yml

## Readiness

### 1. Critical Infrastructure

Status: ⚠️

Router, networking, DNS/DHCP, firewall, VPN, bootstrap, and other foundational infrastructure.

### 2. Complete System

Status: ⚠️

Correctness and operational readiness of the currently implemented system.

### 3. Configuration Pipeline

Status: ⚠️

Integrity of the source-data -> compiler -> generated-data -> Ansible pipeline.

### 4. Repository

Status: ⚠️

Documentation, tooling, structure, validation, and GitHub readiness.

### 5. Multi-Machine Architecture

Status: ⚠️

Ability of the configuration model and deployment system to support additional machines and infrastructure.

## Known Issues

_To be populated from verified findings._

## Unknowns

_To be populated from verified audit gaps._

## Next Actions

_To be populated from confirmed findings, ordered by operational importance._
