# Agentic Flywheel

[![PyPI - Version](https://img.shields.io/pypi/v/agentic-flywheel.svg)](https://pypi.org/project/agentic-flywheel/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/jgwill/agentic-flywheel/actions) <!-- Placeholder, replace with actual CI/CD badge -->

## Dynamic Flowise Automation with Intelligent Flow Management

The **Agentic Flywheel** is a Python package designed to streamline and enhance interactions with FlowiseAI instances, particularly within a Multi-Agent Coordination Protocol (MCP) ecosystem. It provides intelligent flow management, dynamic configuration capabilities, and domain specialization, enabling more adaptive and context-aware AI automation.

## ✨ Features

*   **Dynamic Flow Registry:** Manage Flowise chatflows through a centralized `flow-registry.yaml` file, allowing for easy definition, activation, and configuration of various AI agents.
*   **Intelligent Flow Selection:** Automatically routes user queries to the most appropriate Flowise chatflow based on intent classification and keyword matching.
*   **MCP Integration:** Exposes Flowise functionalities as discoverable and callable tools within an MCP environment, facilitating seamless multi-agent collaboration.
*   **Domain Specialization:** Supports injecting domain-specific context into queries, enabling highly specialized and accurate AI responses.
*   **Configurable Flow Parameters:** Dynamically adjust Flowise parameters like `temperature` and `maxOutputTokens` for fine-grained control over AI behavior.
*   **Interactive Configuration (Upcoming - Issue #619):** A user-friendly CLI tool (`agentic-flywheel-manage-flows`) for interactively adding, editing, listing, and removing flows from the `flow-registry.yaml`.

## 🚀 Installation

The Agentic Flywheel can be installed via `pip`:

```bash
pip install agentic-flywheel
```

For development or to install from a local source:

```bash
git clone https://github.com/jgwill/agentic-flywheel.git # Replace with actual repo URL
cd agentic-flywheel
pip install -e .
```

## 💡 Quick Start

Once installed, you can use the various CLI commands provided by the Agentic Flywheel:

### Querying a Flowise Instance

```bash
agentic-flywheel query "What is the creative orientation framework?" --intent creative-orientation
```

### Listing Available Flows

```bash
agentic-flywheel list-flows
agentic-flywheel list-flows --all # Show inactive flows
```

### Testing Connection to Flowise

```bash
agentic-flywheel test-connection --base-url https://your-flowise-instance.com
```

### Adding a New Flow (CLI - Non-Interactive)

```bash
agentic-flywheel add-flow \
    "your-flow-id-from-flowise" \
    "My New Agent" \
    "A description of what this agent does." \
    --keywords "new,agent,example" \
    --temperature 0.5
```

## ⚙️ Configuration

The core of the Agentic Flywheel's dynamic behavior is driven by the `flow-registry.yaml` file. This YAML file defines all available Flowise chatflows, their IDs, descriptions, intent keywords, and default configurations.

The system loads `flow-registry.yaml` in a cascading manner:
1.  **Explicit Path:** A path provided directly to a command or via an environment variable.
2.  **Project-Local:** `.agentic_flywheel/flow-registry.yaml` in your current project directory.
3.  **User-Specific:** `~/.agentic_flywheel/flow-registry.yaml` in your home directory.
4.  **Package-Bundled:** The `flow-registry.yaml` included with the installed package (default).

This allows for flexible overrides and customization.

## 🛠️ Interactive Configuration (Issue #619 - Coming Soon!)

We are developing an interactive CLI tool, `agentic-flywheel-manage-flows`, to simplify the management of your `flow-registry.yaml`. This tool will provide:

*   **`agentic-flywheel-manage-flows add`:** An interactive wizard to add new flows.
*   **`agentic-flywheel-manage-flows edit <flow_key>`:** Step-by-step editing of existing flow parameters.
*   **`agentic-flywheel-manage-flows list`:** Enhanced listing of flows with filtering options.
*   **`agentic-flywheel-manage-flows remove <flow_key>`:** Safely remove flows.
*   **`agentic-flywheel-manage-flows set-config`:** Manage global and project-specific settings.

Stay tuned for updates on this feature!

## 🤝 Contributing

We welcome contributions to the Agentic Flywheel! Please see our `CONTRIBUTING.md` for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

For questions, feedback, or support, please open an issue on our [GitHub Issues page](https://github.com/jgwill/agentic-flywheel/issues).