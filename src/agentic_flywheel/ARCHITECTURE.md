# Agentic Flywheel Architecture

## Introduction

This document outlines the high-level architecture and core design principles of the Agentic Flywheel project. The Agentic Flywheel is a Python package designed to provide intelligent and dynamic management of FlowiseAI instances, particularly within a Multi-Agent Coordination Protocol (MCP) ecosystem. Its architecture emphasizes modularity, extensibility, and dynamic configuration to facilitate adaptive AI automation.

## High-Level Overview

The Agentic Flywheel operates as an intermediary layer between users/MCP agents and FlowiseAI instances. Its primary function is to intelligently route queries, manage Flowise configurations, and expose Flowise capabilities as discoverable services.

```mermaid
graph TD
    A[User/MCP Agent] -->|CLI Commands / MCP Calls| B(Agentic Flywheel)
    B -->|Query / Configure| C[FlowiseAI Instance]
    B -->|Loads / Saves| D[flow-registry.yaml]
    B -->|Admin Layer Intelligence| E[flowise_admin (External)]

    subgraph Agentic Flywheel Components
        B1[CLI Interface]
        B2[FlowiseManager]
        B3[MCP Servers]
        B4[Configuration Loader (Future)]
    end

    B1 --> B2
    B2 --> C
    B2 --> D
    B3 --> B2
    B3 --> D
    B3 --> E
```

## Core Components

### 1. CLI Interface (`agentic_flywheel.cli`)

*   **Purpose:** Provides a command-line interface for direct user interaction with the Agentic Flywheel. It allows users to query Flowise instances, list available flows, test connections, and manage flow configurations (via `agentic-flywheel-config`).
*   **Responsibilities:**
    *   Parsing user commands and arguments.
    *   Orchestrating calls to `FlowiseManager` and other internal components.
    *   Presenting results to the user.
*   **Key Design Principle:** User-friendly access to core functionalities.

### 2. FlowiseManager (`agentic_flywheel.flowise_manager`)

*   **Purpose:** The central component for abstracting interactions with FlowiseAI instances. It handles dynamic loading of flow configurations, intelligent intent classification, and adaptive querying of Flowise chatflows.
*   **Responsibilities:**
    *   Loading flow definitions from `flow-registry.yaml`.
    *   Managing Flowise API calls (prediction, configuration overrides).
    *   Classifying user intent based on configured keywords.
    *   Generating unique session IDs for conversation continuity.
*   **Key Design Principle:** Encapsulation of Flowise interaction logic, dynamic configurability.

### 3. MCP Servers (`agentic_flywheel.mcp_server`, `agentic_flywheel.intelligent_mcp_server`)

*   **Purpose:** Expose the functionalities of the Agentic Flywheel as services consumable by other MCP-compliant agents. They act as a bridge between the MCP and FlowiseAI.
*   **`agentic_flywheel.mcp_server`:** A foundational MCP server that directly loads flows from `flow-registry.yaml` and exposes basic Flowise query and configuration tools.
*   **`agentic_flywheel.intelligent_mcp_server`:** An enhanced MCP server that integrates with an external "admin layer intelligence" (e.g., `flowise_admin.config_sync`) for curated flow management and more sophisticated routing. It leverages `FlowiseManager` for its core Flowise interactions.
*   **Responsibilities:**
    *   Registering MCP tools and resources.
    *   Handling incoming MCP tool calls and resource requests.
    *   Translating MCP requests into FlowiseManager operations.
*   **Key Design Principle:** Interoperability with Multi-Agent Coordination Protocols.

### 4. Configuration Management (`flow-registry.yaml`)

*   **Purpose:** A YAML-based registry that defines all known Flowise chatflows, their metadata, configuration parameters, intent keywords, and operational status.
*   **Structure:** Organized into `metadata`, `operational_flows`, `routing_flows`, `session_management`, `intent_classification`, `environment`, and `integrations` sections.
*   **Loading Mechanism:** Supports a cascading load order (explicit path > project-local > user-specific > package-bundled) to allow for flexible overrides.
*   **Key Design Principle:** Externalized, human-readable, and dynamic configuration.

## Key Design Principles

*   **Dynamic Configuration:** All operational parameters, especially Flowise flow definitions and their settings, are externalized into `flow-registry.yaml` and loaded dynamically at runtime. This allows for flexible updates without code changes.
*   **Modularity and Extensibility:** Components are designed to be loosely coupled, allowing for easier maintenance, testing, and the integration of new features or Flowise instances.
*   **Intent-Driven Automation:** The system prioritizes understanding user intent (via keyword matching and future NLP enhancements) to intelligently route requests to the most appropriate Flowise chatflow.
*   **MCP Integration:** Native support for the Multi-Agent Coordination Protocol enables the Agentic Flywheel to function as a service provider within a larger ecosystem of AI agents.
*   **Domain Specialization:** The architecture supports injecting rich domain context into queries, allowing for highly tailored and relevant AI interactions.

## Future Architectural Considerations

*   **Centralized `ConfigurationLoader` Module:** A dedicated module to encapsulate the complex logic of finding, loading, merging, and validating `flow-registry.yaml` files from various locations (package, user, project). This will enhance robustness and simplify configuration access for all components.
*   **Interactive Configuration CLI (`agentic-flywheel-manage-flows`):** A new CLI tool to provide a user-friendly, interactive experience for managing `flow-registry.yaml` content, including adding, editing, and removing flows, and setting global/project-specific configurations.
*   **Schema Validation for `flow-registry.yaml`:** Implementing `jsonschema` validation to ensure the integrity and correctness of `flow-registry.yaml` content, preventing runtime errors due to malformed configurations.
*   **Enhanced Intent Classification:** Exploring more advanced NLP techniques for intent classification beyond keyword matching, potentially integrating with external NLU services.
*   **Multi-Flow Orchestration:** Developing capabilities to coordinate multiple Flowise flows for complex tasks that require sequential or parallel execution across different specialized agents.

This architecture aims to provide a flexible, powerful, and easily manageable system for leveraging FlowiseAI within advanced agentic workflows.
