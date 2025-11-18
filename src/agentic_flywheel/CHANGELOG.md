# Changelog

## Version 1.1.0 (2025-09-24)

### ✨ Features

*   **Initial Release of Agentic Flywheel:** The project is now officially named and structured as `agentic-flywheel`.
*   **Dynamic Flowise Flow Management:** Introduced `flow-registry.yaml` for defining and managing Flowise chatflows, enabling dynamic loading and configuration.
*   **MCP Integration:** Core Flowise capabilities are now exposed as discoverable and callable tools within a Multi-Agent Coordination Protocol (MCP) environment.
*   **CLI for Flowise Interaction:** Provided command-line interface for querying Flowise instances, listing available flows, and testing connections.
*   **Basic `add-flow` Functionality:** CLI command to add new flow definitions to the `flow-registry.yaml`.

### 🚀 Improvements

*   **Refactored `FlowiseManager`:** The central `FlowiseManager` class now dynamically loads flow configurations from `flow-registry.yaml`, removing hardcoded definitions and enhancing flexibility.
*   **Updated CLI and MCP Servers:** All relevant CLI commands and MCP server components (`cli.py`, `config_manager.py`, `intelligent_mcp_server.py`) have been updated to correctly pass the `flow_registry_path` to `FlowiseManager` instances.
*   **Package Migration:** Successfully migrated the entire package from `jgt_flowise_mcp` to `agentic_flywheel`, including directory renaming, `pyproject.toml` updates, and internal import adjustments.
*   **Placeholder Scripts:** Created placeholder `gateway.py` and `init.py` scripts to ensure all defined entry points are functional.

### 🐛 Bug Fixes

*   **Resolved `ModuleNotFoundError`:** Addressed issues where Python modules were not found after the package migration and renaming.
*   **Fixed `TypeError` in `cli.py`:** Corrected the `TypeError` related to `click` command decoration by refactoring `browse_flow` to use programmatic alias assignment.
*   **Corrected `ImportError` in `config_manager.py`:** Fixed the `ImportError` for `cli_main` by updating the `pyproject.toml` entry point to `main` and ensuring `config_manager.py` imports `FlowiseManager` and `FlowConfig` from the central `flowise_manager` module.
*   **Addressed `RuntimeWarning` in `mcp_server.py`:** Resolved the `RuntimeWarning` for unawaited coroutine by updating the `pyproject.toml` entry point to point to the `cli` function.
*   **Fixed `IndentationError` in `flowise_manager.py`:** Corrected an indentation issue that caused a `SyntaxError` in the `adaptive_query` method.
