# Raskal Labs Homelab IaC

Welcome to the **Raskal Labs** homelab Infrastructure as Code (IaC) repository. This repository is built from the ground up using a **Text-Driven GitOps** philosophy.

## Core Philosophy: Text-Driven GitOps

1. **Declarative & Plain-Text**: The master state of the infrastructure is defined entirely in plain-text, tool-agnostic YAML files.
2. **Source of Truth (SoT)**: The YAML files dictate reality. They use strict typing and dictionary-based schemas (key-value maps) to ensure Git diffs remain clean when adding or removing items.
3. **Separation of Concerns**: The repository is split into three distinct layers:
   - **Data Layer (`data/`)**: Pure YAML inventory files containing no execution logic.
   - **Validation & Transform Layer (`transforms/` & `schemas/`)**: JSON Schemas, dependency management, and scripts to translate the YAML into tool-specific formats (like Ansible dynamic JSON).
   - **Execution Layer (`automation/`)**: Ansible playbooks and roles that consume the transformed data to apply state.

## Directory Structure

- `data/`: Contains the pure YAML Source of Truth files.
- `schemas/`: Contains JSON Schema definitions to validate the structure of the data files.
- `transforms/`: Contains scripts and tools to validate the data and transform it into execution-ready formats.
- `automation/`: Contains Ansible playbooks, roles, and configuration to execute changes on the infrastructure.

## Getting Started

To bootstrap your local development environment and set up the required Git hooks and dependencies, run:
