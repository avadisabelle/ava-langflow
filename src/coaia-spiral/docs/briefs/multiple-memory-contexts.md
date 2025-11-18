# Technical Brief: Multiple Memory Contexts Implementation

## Overview

This document outlines the technical implementation plan for adding multiple memory contexts to the MCP Knowledge Graph server. This feature will allow users to define, manage, and switch between different memory files, supporting both static named contexts and dynamic project-based memory paths.

## Background

Currently, the MCP Knowledge Graph server uses a single memory file specified by the `--memory-path` parameter. Issue #6 requested the ability to define different memory files for different projects, allowing AI models to access project-based memory.

## User Personas

1. **Set-and-Forget Users**: Want a single memory file location configured once in their AI platform
2. **Multi-Context Users**: Need to switch between different memory contexts while using their AI platform
3. **Developers**: Comfortable with project-based approaches and explicit path management

## Implementation Details

### 1. Memory Context System

We will implement a "memory context" system that manages multiple memory files:

```typescript
interface MemoryContext {
  name: string;         // Human-readable name
  path: string | PathTemplate;  // File path (static or dynamic)
  description?: string; // Optional description
  isProjectBased: boolean;      // Whether to use project detection
  lastAccessed?: Date;  // When it was last used
  projectDetectionRules?: {     // Rules for detecting project directories
    markers: string[];          // Files that indicate a project root
    maxDepth: number;           // How far up to look for project markers
  };
}

type PathTemplate = string;  // e.g., "{projectDir}/.ai-memory.jsonl"

interface ContextsConfig {
  activeContext: string;
  contexts: MemoryContext[];
}
```

### 2. Configuration Parameters

We'll add the following configuration parameters:

- `--memory-path`: (Existing) Default memory file path
- `--contexts-directory`: Directory where memory context configurations are stored
- `--default-context`: Name of the default context to use if none is specified

### 3. New Tools for Context Management

We'll add these tools to manage memory contexts:

- `list_contexts`: List all available memory contexts
- `get_active_context`: Show which context is currently active
- `set_active_context`: Change the active context
- `add_context`: Add a new memory context
- `remove_context`: Remove a memory context (doesn't delete the file)

### 4. Path Resolution Logic

When a tool is called, we'll resolve the memory path using this logic:

```typescript
async function resolveMemoryPath(contextName?: string): Promise<string> {
  // Load contexts configuration
  const config = await loadContexts(CONTEXTS_FILE_PATH);

  // Get requested context or active context
  const contextToUse = contextName || config.activeContext || "default";
  const context = config.contexts.find(c => c.name === contextToUse);

  if (!context) {
    // Fall back to default if context not found
    return MEMORY_FILE_PATH;
  }

  // If it's a static path, return it directly
  if (!context.isProjectBased) {
    return context.path;
  }

  // For project-based paths, resolve the template
  const projectInfo = await detectProjectInfo();
  return resolvePathTemplate(context.path, projectInfo);
}
```

### 5. Project Detection

For project-based contexts, we'll implement project detection:

```typescript
async function detectProjectInfo(): Promise<ProjectInfo> {
  // Start at current directory
  let currentDir = process.cwd();
  const maxDepth = 5; // Default max depth

  for (let i = 0; i < maxDepth; i++) {
    // Check for project markers
    for (const marker of ['package.json', '.git', 'pyproject.toml']) {
      if (await fileExists(path.join(currentDir, marker))) {
        // Found a project marker
        return {
          directory: currentDir,
          name: path.basename(currentDir),
          marker: marker
        };
      }
    }

    // Move up one directory
    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) {
      // Reached root directory
      break;
    }
    currentDir = parentDir;
  }

  // No project detected, use current directory
  return {
    directory: process.cwd(),
    name: path.basename(process.cwd()),
    marker: null
  };
}
```

### 6. Context Configuration Management

We'll implement functions to load and save context configurations:

```typescript
async function loadContexts(contextsFilePath: string): Promise<ContextsConfig> {
  try {
    const data = await fs.readFile(contextsFilePath, "utf-8");
    return JSON.parse(data);
  } catch (error) {
    // If file doesn't exist or is invalid, create default
    const defaultConfig: ContextsConfig = {
      activeContext: "default",
      contexts: [{
        name: "default",
        path: MEMORY_FILE_PATH,
        isProjectBased: false,
        description: "Default memory context"
      }]
    };

    // Ensure directory exists
    await fs.mkdir(path.dirname(contextsFilePath), { recursive: true });

    // Write default config
    await fs.writeFile(contextsFilePath, JSON.stringify(defaultConfig, null, 2));
    return defaultConfig;
  }
}

async function saveContexts(contextsFilePath: string, config: ContextsConfig): Promise<void> {
  await fs.writeFile(contextsFilePath, JSON.stringify(config, null, 2));
}
```

### 7. Tool Interface Updates

All existing tools will be updated to support context specification:

```typescript
// Example tool schema update
{
  name: "create_entities",
  description: "Create multiple new entities in the knowledge graph",
  inputSchema: {
    type: "object",
    properties: {
      entities: {
        // existing schema
      },
      context: {
        type: "string",
        description: "Memory context to use (optional, defaults to active context)"
      }
    },
    required: ["entities"]
  }
}
```

### 8. KnowledgeGraphManager Updates

The `KnowledgeGraphManager` class will be updated to work with dynamic file paths:

```typescript
class KnowledgeGraphManager {
  private async loadGraph(filePath: string): Promise<KnowledgeGraph> {
    try {
      const data = await fs.readFile(filePath, "utf-8");
      // Rest of the method remains the same
    } catch (error) {
      // Error handling
    }
  }

  // Other methods would be updated similarly to accept a filePath parameter
}
```

## User Experience Improvements

1. **Visual Indicators**: When using tools, include the active context name in responses
2. **Confirmation Prompts**: When changing contexts, provide clear confirmation
3. **Context Status**: Add a way to query the current active context

## Safety Mechanisms

1. **Read-Only Mode**: Option to make certain contexts read-only
2. **Context Validation**: Verify contexts exist before switching
3. **Default Fallback**: If a context becomes invalid, fall back to the default
4. **Explicit Context Operations**: Require explicit context switching rather than passing paths to every operation

## Migration Path

For existing users:

1. The first time they run with the new version, their existing memory file becomes the "default" context
2. No changes to their workflow unless they want to use multiple contexts
3. Clear documentation on how to set up and use multiple contexts

## Configuration Examples

### Example Context Configuration

```json
{
  "activeContext": "work",
  "contexts": [
    {
      "name": "default",
      "path": "/Users/username/.ai-memory/default.jsonl",
      "isProjectBased": false,
      "description": "Default memory context"
    },
    {
      "name": "work",
      "path": "/Users/username/.ai-memory/work.jsonl",
      "isProjectBased": false,
      "description": "Work-related memories"
    },
    {
      "name": "project-specific",
      "path": "{projectDir}/.ai-memory.jsonl",
      "isProjectBased": true,
      "description": "Project-specific memories",
      "projectDetectionRules": {
        "markers": [".git", "package.json", "pyproject.toml"],
        "maxDepth": 3
      }
    }
  ]
}
```

### AI Platform Configuration Example

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory",
        "--contexts-directory",
        "/Users/username/.ai-memory/contexts",
        "--default-context",
        "personal"
      ]
    }
  }
}
```

## Implementation Plan

1. **Phase 1: Core Context System**
   - Implement context configuration loading/saving
   - Add context resolution logic
   - Update KnowledgeGraphManager to use dynamic paths

2. **Phase 2: Context Management Tools**
   - Implement list_contexts, get_active_context, set_active_context
   - Implement add_context, remove_context
   - Update existing tools to support context parameter

3. **Phase 3: Project-Based Contexts**
   - Implement project detection
   - Add path template resolution
   - Support project-specific context rules

4. **Phase 4: User Experience & Safety**
   - Add visual indicators for active context
   - Implement safety mechanisms
   - Add migration support for existing users

5. **Phase 5: Documentation & Testing**
   - Update README with context usage examples
   - Add configuration examples for different user personas
   - Comprehensive testing across different scenarios

## Benefits

1. **Flexibility**: Users can have separate memory files for different projects or contexts
2. **Backward Compatibility**: Existing usage with a single memory file still works
3. **Simplicity**: Clear context naming and management for non-developers
4. **Scalability**: Each project/context gets its own file, preventing one large memory file
5. **Safety**: Explicit context switching and validation prevents accidental data corruption
