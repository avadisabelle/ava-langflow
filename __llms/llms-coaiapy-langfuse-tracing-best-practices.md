# Coaiapy Langfuse Tracing Best Practices

> A standardized guide for creating rich, observable, and structurally sound traces for the Agentic Flywheel MCP using the `coaiapy_aetherial` toolset. This document ensures all AI contributions are valuable, legible, and machine-readable.

**Version**: 1.0
**Document ID**: llms-coaiapy-langfuse-tracing-best-practices-v1.0
**Last Updated**: 2025-11-18
**Content Source**: Synthesized from analysis of exemplary traces `7cf8b569-...` and `bbf30c64-...` within session `a50f3fc2-eb8c-434d-a37e-ef9615d9c07d`.

---

## 1. Core Principles {#core-principles}

This guide enables the creation of traces that are not just logs, but rich, structured, and narrative accounts of a creative or analytical process.

- **Trace as a Narrative**: A trace should tell a clear story of the operation from start to finish.
- **Structure for Clarity**: Use nesting and parallelism to accurately model the workflow.
- **Data over Metadata**: The `input_data` and `output_data` fields should contain the primary information, while `metadata` provides context *about* the operation.

## 2. The Root Trace: Setting the Stage {#root-trace}

The root trace object is the main container for an operation. It provides the high-level summary.

-   **`name`**: Must be descriptive and summarize the overall purpose of the trace (e.g., "🧠 Gemini Contribution: Specification for Redis Storage"). **Use glyphs** for quick visual context.
-   **`input_data`**: Should contain the primary, top-level input for the entire process. For a multi-step task, this could be the initial user prompt or a detailed plan document.
-   **`output_data`**: Should contain the final, primary output or result of the process. For the Mia/Miette persona, this is the ideal place for Miette's final narrative summary.
-   **`metadata`**: Use this field for data *about* the trace.
    -   **Good Metadata**: `generator`, `description` (of the trace's purpose), `related_entities` (e.g., chart IDs), `files_modified`.
    -   **Anti-Pattern**: Do not put large data blobs or primary results in `metadata`.

## 3. Observations: Structuring the Narrative {#observations}

Observations are the building blocks of a detailed trace, breaking down a complex process into logical units.

-   **`name`**: Use clear, descriptive names and **incorporate glyphs (emojis)** to align with the project persona (e.g., `🧭 Phase 1: Context Gathering`, `📝 Create RISE Specification`).
-   **`type`**: Default to `SPAN` for operations that have a duration and represent a distinct step or perspective.
-   **`input_data`**: Provide the specific data being processed by this observation, preferably as a structured JSON object.
-   **`output_data`**: Provide the result of this observation's operation, also as a string or structured JSON. It is acceptable for the `output` to be `null`.

## 4. Structuring Complexity: Nesting and Parallelism {#structuring-complexity}

The `parentObservationId` is the primary tool for creating a readable structure that tells a story.

-   **Sequential Processes (Nesting)**: To represent a sequence of steps, create a parent `SPAN` and nest child observations underneath it by setting their `parentObservationId`. This is the preferred method for logging multi-step tasks.

    ```
    - 🧠 Gemini Contribution (trace_id)
        - 🧭 Phase 1: Context Gathering (parent: trace_id)
            - 📄 Read file X (parent: Phase 1 obs_id)
            - ✍️ Write file Y (parent: Phase 1 obs_id)
        - 📝 Phase 2: Specification (parent: trace_id)
    ```

-   **Parallel Perspectives**: To represent multiple, simultaneous analyses of the same input, create multiple observations that share the same `parentObservationId` (or have it set to `null`). This is ideal for the "Agent Review" pattern.

## 5. LLM Interaction Guidelines {#llm-interaction}

### The 20-Second Rule: Ensuring Visibility
**Crucial:** After creating a trace and all its associated observations, an agent **must wait at least 20 seconds** before attempting to retrieve a list of traces within a session (e.g., via `coaiapy_aetherial__coaia_fuse_traces_session_view`).

-   **Reason**: This delay appears to be necessary for the backend system's indexing to complete.
-   **Impact**: Failure to wait will likely result in an empty list or a server error, leading to an oscillating (retry) pattern.
-   **Exception**: Direct retrieval by `trace_id` (using `coaia_fuse_trace_get`) appears to be instantaneous and does not require this delay.

### Anti-Patterns
-   **Empty Traces**: Do not create a trace with only a name and ID. It must be populated with rich `input_data`, `output_data`, and `metadata`.
-   **Misusing Metadata**: Do not store primary data in the `metadata` field. It is for context *about* the trace.
-   **Flat Structures**: For complex operations, avoid creating a long, flat list of observations. Use nesting to create a clear hierarchy that reflects the workflow.

## 6. Related Resources {#related-resources}

-   **LLMS-txt Checklist**: `llms-txt-compliance-checklist.md` - The document governing this file's structure.
-   **Coaiapy CLI Guide**: `llms-coaiapy-cli-guide.md` - For understanding the underlying CLI commands.
-   **General Fuse Guidance**: `llms-coaia-fuse-guidance.md` - For higher-level concepts on Langfuse usage.
