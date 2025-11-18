# RISE Specification: Langflow Backend Adapter

**RISE Spec ID**: `langflow-backend-spec-v1`
**Task**: Task 1: Langflow Backend Adapter
**Author**: Gemini-Pro Subagent
**Date**: 2025-11-18

---

## 1. Desired Outcome Definition

Users of the Agentic Flywheel MCP want to **create a unified and seamless AI workflow orchestration experience, regardless of the underlying execution engine.**

Specifically, they want to be able to:
- **Execute any workflow** with a single, universal query, without needing to know if it's hosted on Langflow or Flowise.
- **Automatically discover** and catalog all available flows from their connected Langflow instances.
- **Intelligently route** their requests to the best-suited backend (including Langflow) based on flow capabilities, performance, and health.
- **Gain transparent insights** into the performance and behavior of their Langflow-hosted workflows.

This `LangflowBackend` adapter is the creative artifact that makes this unified experience possible for the Langflow ecosystem. It bridges the gap between the Agentic Flywheel's universal `FlowBackend` interface and the specific implementation of the Langflow platform.

---

## 2. Current Structural Reality

- The Agentic Flywheel currently possesses a `FlowiseBackend` adapter, making it a single-platform system.
- A universal `FlowBackend` abstract base class exists in `src/agentic_flywheel/backends/base.py`, defining a clear integration contract.
- The Langflow platform exists as an independent, external system with its own distinct REST API for flow management and execution.
- Preliminary research indicates the Langflow API is accessible and provides endpoints for core operations, but its structure is different from the Flowise API.
- There is no existing code that connects the Agentic Flywheel to Langflow.

---

## 3. Structural Tension

The primary structural tension exists between the **Current Reality** of a "Flowise-only system" and the **Desired Outcome** of a "unified, multi-backend orchestration platform."

This tension creates a natural impetus to build the `LangflowBackend` adapter. The existence of the `FlowBackend` interface acts as a powerful structural element that channels the resolution of this tension, guiding the implementation toward a form that integrates naturally with the existing system.

The implementation of this adapter is the primary action that will resolve this tension and move the system toward its desired state.

---

## 4. Natural Progression Patterns (Implementation Scenarios)

The implementation of the `LangflowBackend` will naturally progress by implementing each abstract method from the `FlowBackend` interface.

### Scenario 1: Connection and Health Check
A user wants to know if their Langflow instance is online and accessible.
1. The `LangflowBackend` is instantiated with a `base_url` and `api_key`.
2. The `connect()` method is called, which initializes an `httpx.AsyncClient` with the correct base URL and authentication headers (`x-api-key`).
3. The `health_check()` method is called, which makes a request to a known, lightweight Langflow endpoint (e.g., `/health` or `/v1/flows`).
4. A successful `200 OK` response indicates the backend is healthy and connected.

### Scenario 2: Flow Discovery
A user wants to see all the workflows available on their Langflow instance.
1. The `discover_flows()` method is called.
2. It makes a `GET` request to the `/api/v1/flows` endpoint.
3. It receives a JSON array of Langflow flow objects.
4. It iterates through the array, calling the `_transform_to_universal_flow()` helper method for each object.
5. This helper maps Langflow-specific fields (e.g., `id`, `name`, `description`, `data`) to the `UniversalFlow` dataclass. The `data` field likely contains graph nodes that can be analyzed to extract intent keywords.
6. The method returns a `List[UniversalFlow]`.

### Scenario 3: Flow Execution
A user wants to run a specific Langflow workflow.
1. The `execute_flow()` method is called with a `flow_id` and `input_data`.
2. It makes a `POST` request to the `/api/v1/run/{flow_id}` endpoint.
3. The `input_data` is formatted into the request body, likely under a key like `input_value`.
4. The response, containing the execution result, is received.
5. The `_transform_execution_result()` helper method parses the Langflow-specific output and maps it to a standardized dictionary format.
6. The method returns the formatted result dictionary.

---

## 5. API Mapping (Langflow -> Universal Interface)

This section maps the abstract methods of the `FlowBackend` interface to the anticipated Langflow REST API endpoints.

| `FlowBackend` Method            | HTTP Method | Langflow Endpoint              | Notes                                                               |
| ------------------------------- | ----------- | ------------------------------ | ------------------------------------------------------------------- |
| `health_check()`                | `GET`       | `/health` or `/api/v1/flows`   | Use a lightweight endpoint to check connectivity and auth.          |
| `discover_flows()`              | `GET`       | `/api/v1/flows`                | **Assumption**: This endpoint exists for listing all flows.         |
| `get_flow(flow_id)`             | `GET`       | `/api/v1/flows/{flow_id}`      | **Assumption**: This endpoint exists for fetching a single flow.    |
| `execute_flow(flow_id, ...)`    | `POST`      | `/api/v1/run/{flow_id}`        | Confirmed via research. The body structure needs to be verified.    |
| `stream_flow(flow_id, ...)`     | `POST`      | `/api/v1/run/{flow_id}`        | Needs investigation; likely requires a specific parameter like `stream=true`. |
| `create_session()` / `get_session()` | -         | -                              | **Assumption**: Langflow's execution may be stateless. If so, these methods can be implemented as no-ops that return a mock `UniversalSession`. |

---

## 6. Data Transformation

### Langflow Flow -> `UniversalFlow`
The `_transform_to_universal_flow` helper will perform this mapping:
- `UniversalFlow.id` <-- `flow.id`
- `UniversalFlow.name` <-- `flow.name`
- `UniversalFlow.description` <-- `flow.description`
- `UniversalFlow.backend_type` <-- `BackendType.LANGFLOW`
- `UniversalFlow.intent_keywords` <-- Analyze `flow.data` (the graph) to extract keywords from node names or descriptions.
- `UniversalFlow.raw_data` <-- `flow` (the full JSON object)

### Langflow Execution Result -> Standard Dictionary
The `_transform_execution_result` helper will parse the output from the `/run` endpoint. The structure needs to be verified, but it likely contains a primary output field.
- **Input**: `{ "results": { "chat_output": { "outputs": { "output": "This is the response." } } } }`
- **Output**: `{ "result": "This is the response.", "raw": { ... } }`

---

## 7. Error Handling

The `LangflowBackend` must be resilient and never crash the main MCP server.
- **Connection Errors**: All `httpx` requests must be wrapped in a `try...except httpx.RequestError`. On failure, log the error and return `None` or an empty list. The `health_check` should return `False`.
- **API Errors**: Check the status code of every response. For `4xx` or `5xx` errors, log the error details (status code, response body) and return an appropriate failure indicator.
- **Authentication Errors**: Specifically handle `401 Unauthorized` or `403 Forbidden` responses by logging a clear message about invalid API keys.
- **Graceful Degradation**: If the backend is unhealthy or misconfigured, it should cleanly report its status to the `BackendRegistry`, allowing the Universal Query router to bypass it.

---

## 8. Performance Considerations

- **HTTP Client**: A single `httpx.AsyncClient` instance should be created and reused for the lifetime of the `LangflowBackend` object to leverage connection pooling.
- **Caching**: The results of `discover_flows()` should be cached in memory for a short period (e.g., 60 seconds) to avoid excessive API calls. A simple `(timestamp, data)` tuple can manage this.
- **Timeouts**: All `httpx` requests must have a reasonable timeout configured (e.g., 30 seconds) to prevent the system from hanging on a slow or unresponsive Langflow instance.