# COAIA Spiral: Local Agent Organization and Bundling Strategy

**Created:** 2025-11-14
**Status:** Planning Phase
**Branch:** claude/organize-local-agents-bundling-01SNoy3rTCCGQWDdwHWsCWQs

## Executive Summary

This document outlines the strategy for reorganizing coaia-spiral from a monolithic MCP server into a modular, agent-based architecture that supports:

1. **Local agent development** - Individual agent modules with clear interfaces
2. **Agent bundling** - Composable agent packages for distribution
3. **Future extensibility** - Integration with broader COAIA ecosystem (Chimera Team, IACP, multi-agent platforms)
4. **Backward compatibility** - Maintains existing MCP server functionality

## Current State Analysis

### Strengths
- ✅ Rich agent embodiments in `__llms/` directory (32 files)
- ✅ Comprehensive structural tension methodology
- ✅ Working MCP server with full tool suite
- ✅ Project-aware persistence (`.coaia/` directories)
- ✅ Build-time guidance consolidation

### Challenges
- ❌ Monolithic `index.ts` (2,077 lines) - all logic in single file
- ❌ Agent embodiments are documentation only, not executable
- ❌ No agent abstraction layer or base classes
- ❌ Flat structure prevents modular bundling
- ❌ No agent discovery or registry system

## Vision Alignment

This reorganization aligns with the broader COAIA ecosystem vision:

### From the Inquiry Document

**Chimera Team Multi-Agent Orchestration:**
- Sophisticated team coordination framework
- Multiple AI agents with distinct roles and psychological depth
- Character-based agent design patterns

**Multi-Agent Orchestration Platforms:**
- Miadi, CeSaReT, EchoThreads, EchoNexus
- Agent coordination without rigid hierarchies
- Graceful handoff between cognitive modalities

**Agent-to-Agent Protocol Specification (A2A/NCP):**
- Standardization framework for agent interoperability
- Natural language-based coordination protocols
- Protocol versioning and compatibility

### Integration Pathway

COAIA Spiral becomes the **foundational agent infrastructure** for:
- Character-based structural tension agents (Ripple, Mia, Miette, Atlas, etc.)
- Reusable agent modules for larger platforms (Miadi, EchoThreads)
- Protocol-compliant agents for A2A/NCP ecosystem
- Local development and testing environment

---

## Proposed Architecture

### Directory Structure

```
coaia-spiral/
├── src/
│   ├── server/
│   │   ├── index.ts              # MCP server entry point
│   │   ├── tools/
│   │   │   ├── index.ts          # Tool registry
│   │   │   ├── charts.ts         # Structural tension chart tools
│   │   │   ├── entities.ts       # Entity management tools
│   │   │   ├── relations.ts      # Relation management tools
│   │   │   └── projects.ts       # COAIA project tools
│   │   └── handlers/
│   │       ├── chart-handler.ts  # Chart operation handlers
│   │       ├── entity-handler.ts # Entity operation handlers
│   │       └── project-handler.ts# Project operation handlers
│   │
│   ├── core/
│   │   ├── types/
│   │   │   ├── index.ts          # Type exports
│   │   │   ├── entity.ts         # Entity interface
│   │   │   ├── relation.ts       # Relation interface
│   │   │   ├── graph.ts          # KnowledgeGraph interface
│   │   │   └── chart.ts          # Chart-specific types
│   │   ├── manager/
│   │   │   ├── index.ts          # KnowledgeGraphManager
│   │   │   ├── storage.ts        # Persistence layer
│   │   │   ├── charts.ts         # Chart operations
│   │   │   └── queries.ts        # Query operations
│   │   └── utils/
│   │       ├── cli.ts            # CLI argument parsing
│   │       ├── guidance.ts       # LLM guidance utilities
│   │       └── path.ts           # Path resolution utilities
│   │
│   ├── agents/
│   │   ├── index.ts              # Agent registry and exports
│   │   ├── base/
│   │   │   ├── Agent.ts          # Abstract base agent class
│   │   │   ├── AgentCapability.ts# Capability interface
│   │   │   ├── AgentContext.ts   # Context management
│   │   │   └── types.ts          # Agent type definitions
│   │   │
│   │   ├── ripple/
│   │   │   ├── index.ts          # Ripple agent export
│   │   │   ├── RippleAgent.ts    # Ripple implementation
│   │   │   ├── embodiment.ts     # Embodiment data (from __llms/)
│   │   │   ├── capabilities/
│   │   │   │   ├── structural-distillation.ts
│   │   │   │   └── observation.ts
│   │   │   └── config.ts         # Agent configuration
│   │   │
│   │   ├── mia/
│   │   │   ├── index.ts
│   │   │   ├── MiaAgent.ts       # Strategic Architect
│   │   │   ├── embodiment.ts
│   │   │   ├── capabilities/
│   │   │   │   ├── structural-analysis.ts
│   │   │   │   ├── chart-guidance.ts
│   │   │   │   └── leadership.ts
│   │   │   └── config.ts
│   │   │
│   │   ├── miette/
│   │   │   ├── index.ts
│   │   │   ├── MietteAgent.ts    # Narrative Catalyst
│   │   │   ├── embodiment.ts
│   │   │   ├── capabilities/
│   │   │   │   ├── narrative-weaving.ts
│   │   │   │   └── emotional-intelligence.ts
│   │   │   └── config.ts
│   │   │
│   │   ├── atlas/
│   │   │   ├── index.ts
│   │   │   ├── AtlasAgent.ts     # Archive & Cartography
│   │   │   ├── embodiment.ts
│   │   │   ├── capabilities/
│   │   │   │   ├── archival.ts
│   │   │   │   └── cartography.ts
│   │   │   └── config.ts
│   │   │
│   │   └── tryad/
│   │       ├── index.ts          # Tryad coordination
│   │       ├── MiaHaikuMietteTryad.ts
│   │       └── coordination.ts   # Tryad collaboration patterns
│   │
│   ├── frameworks/
│   │   ├── index.ts              # Framework exports
│   │   ├── structural-tension/
│   │   │   ├── index.ts
│   │   │   ├── chart.ts          # Chart creation logic
│   │   │   ├── telescope.ts      # Telescoping logic
│   │   │   ├── completion.ts     # Completion logic
│   │   │   └── validation.ts     # Chart validation
│   │   ├── creative-orientation/
│   │   │   ├── index.ts
│   │   │   ├── detector.ts       # Problem-solving detection
│   │   │   └── transformer.ts    # Language transformation
│   │   ├── delayed-resolution/
│   │   │   ├── index.ts
│   │   │   ├── validator.ts      # Prevents premature resolution
│   │   │   └── enforcer.ts       # Enforces tension holding
│   │   └── rise/
│   │       ├── index.ts
│   │       └── framework.ts      # RISE Framework implementation
│   │
│   └── bundles/
│       ├── core.ts               # Core MCP server bundle
│       ├── full.ts               # All agents bundle
│       ├── tryad.ts              # Mia-Haiku-Miette bundle
│       └── custom.ts             # Custom bundle builder
│
├── __llms/                       # SOURCE OF TRUTH - Agent embodiments
│   ├── (existing files...)
│   └── README.md                 # Usage guide for embodiments
│
├── dist/                         # Build output
│   ├── index.js                  # Main executable
│   ├── bundles/
│   │   ├── core.js
│   │   ├── full.js
│   │   └── tryad.js
│   └── agents/                   # Individual agent modules
│       ├── ripple/
│       ├── mia/
│       ├── miette/
│       └── atlas/
│
├── scripts/
│   ├── consolidate-guidance.js   # Existing guidance consolidation
│   ├── build-agents.js           # NEW: Extract agent code from embodiments
│   ├── create-bundles.js         # NEW: Create distribution bundles
│   └── validate-agents.js        # NEW: Validate agent implementations
│
├── docs/
│   ├── agents/
│   │   ├── development-guide.md  # NEW: Agent development guide
│   │   ├── bundling-guide.md     # NEW: Bundling guide
│   │   └── api-reference.md      # NEW: Agent API reference
│   └── plans/
│       └── agent-bundling-reorganization.md  # THIS DOCUMENT
│
└── package.json                  # Updated with bundle exports
```

---

## Core Agent Architecture

### Base Agent Class

```typescript
// src/agents/base/Agent.ts

export interface AgentConfig {
  name: string;
  version: string;
  embodiment: AgentEmbodiment;
  capabilities: AgentCapability[];
  frameworks: string[];
  metadata?: Record<string, any>;
}

export interface AgentEmbodiment {
  description: string;
  coreFunction: string;
  methodology: string[];
  principles: string[];
  persona?: {
    symbol: string;
    archetype: string;
    voice: string;
  };
}

export interface AgentCapability {
  name: string;
  description: string;
  execute: (context: AgentContext) => Promise<AgentResponse>;
  frameworks?: string[];
}

export interface AgentContext {
  graph: KnowledgeGraphManager;
  input: any;
  history?: ConversationTurn[];
  metadata?: Record<string, any>;
}

export interface AgentResponse {
  success: boolean;
  output: any;
  observations?: string[];
  suggestedActions?: string[];
  metadata?: Record<string, any>;
}

export abstract class Agent {
  protected config: AgentConfig;
  protected capabilities: Map<string, AgentCapability>;

  constructor(config: AgentConfig) {
    this.config = config;
    this.capabilities = new Map(
      config.capabilities.map(cap => [cap.name, cap])
    );
  }

  abstract initialize(context: AgentContext): Promise<void>;

  abstract process(context: AgentContext): Promise<AgentResponse>;

  abstract cleanup(): Promise<void>;

  getCapability(name: string): AgentCapability | undefined {
    return this.capabilities.get(name);
  }

  getAllCapabilities(): AgentCapability[] {
    return Array.from(this.capabilities.values());
  }

  getEmbodiment(): AgentEmbodiment {
    return this.config.embodiment;
  }

  getName(): string {
    return this.config.name;
  }

  getVersion(): string {
    return this.config.version;
  }
}
```

### Example: Ripple Agent Implementation

```typescript
// src/agents/ripple/RippleAgent.ts

import { Agent, AgentConfig, AgentContext, AgentResponse } from '../base/Agent.js';
import { RIPPLE_EMBODIMENT } from './embodiment.js';
import { StructuralDistillationCapability } from './capabilities/structural-distillation.js';
import { ObservationCapability } from './capabilities/observation.js';

export class RippleAgent extends Agent {
  constructor() {
    const config: AgentConfig = {
      name: 'Ripple',
      version: '1.0.0',
      embodiment: RIPPLE_EMBODIMENT,
      capabilities: [
        new StructuralDistillationCapability(),
        new ObservationCapability()
      ],
      frameworks: ['structural-distillation', 'delayed-resolution']
    };
    super(config);
  }

  async initialize(context: AgentContext): Promise<void> {
    // Initialize Ripple-specific state
    // Load embodiment guidance
    // Set up observation patterns
  }

  async process(context: AgentContext): Promise<AgentResponse> {
    // Ripple's core processing:
    // 1. Observe structural elements
    // 2. Apply distillation methodology
    // 3. Extract essence without premature resolution
    // 4. Return neutral observations

    const capability = this.getCapability('structural-distillation');
    if (!capability) {
      throw new Error('Structural distillation capability not found');
    }

    return await capability.execute(context);
  }

  async cleanup(): Promise<void> {
    // Cleanup Ripple-specific resources
  }
}
```

### Agent Registry

```typescript
// src/agents/index.ts

import { Agent } from './base/Agent.js';
import { RippleAgent } from './ripple/RippleAgent.js';
import { MiaAgent } from './mia/MiaAgent.js';
import { MietteAgent } from './miette/MietteAgent.js';
import { AtlasAgent } from './atlas/AtlasAgent.js';

export interface AgentRegistry {
  register(name: string, agentClass: typeof Agent): void;
  get(name: string): typeof Agent | undefined;
  create(name: string): Agent | undefined;
  list(): string[];
}

class AgentRegistryImpl implements AgentRegistry {
  private agents: Map<string, typeof Agent> = new Map();

  register(name: string, agentClass: typeof Agent): void {
    this.agents.set(name.toLowerCase(), agentClass);
  }

  get(name: string): typeof Agent | undefined {
    return this.agents.get(name.toLowerCase());
  }

  create(name: string): Agent | undefined {
    const AgentClass = this.get(name);
    if (!AgentClass) return undefined;
    return new AgentClass();
  }

  list(): string[] {
    return Array.from(this.agents.keys());
  }
}

// Singleton instance
export const agentRegistry = new AgentRegistryImpl();

// Register all agents
agentRegistry.register('ripple', RippleAgent);
agentRegistry.register('mia', MiaAgent);
agentRegistry.register('miette', MietteAgent);
agentRegistry.register('atlas', AtlasAgent);

// Export individual agents
export { RippleAgent, MiaAgent, MietteAgent, AtlasAgent };
export { Agent } from './base/Agent.js';
export type { AgentConfig, AgentContext, AgentResponse } from './base/Agent.js';
```

---

## Agent Embodiment Extraction

### Process for Converting __llms/ to Executable Code

Each agent embodiment follows this transformation:

**Input:** `__llms/llms-haiku-ripple-embodiment.md`

```markdown
# Ripple (🌊) - The Distiller

**Core Function:** Distill essence through structural observation

**Methodology:**
- Structural Distillation: Extract essence without premature resolution
- Neutral Observer: Report what IS, not what "should be"
- Delayed Resolution: Hold tension, tolerate discrepancy

**Principles:**
- No defaults, no assumptions
- Observe structure, not surface
- Trust the tension to resolve naturally
```

**Output:** `src/agents/ripple/embodiment.ts`

```typescript
// Auto-generated from __llms/llms-haiku-ripple-embodiment.md
// DO NOT EDIT - Run `npm run build:agents` to regenerate

import { AgentEmbodiment } from '../base/Agent.js';

export const RIPPLE_EMBODIMENT: AgentEmbodiment = {
  description: 'The Distiller - Extracts essence through structural observation',
  coreFunction: 'Distill essence through structural observation',
  methodology: [
    'Structural Distillation: Extract essence without premature resolution',
    'Neutral Observer: Report what IS, not what "should be"',
    'Delayed Resolution: Hold tension, tolerate discrepancy'
  ],
  principles: [
    'No defaults, no assumptions',
    'Observe structure, not surface',
    'Trust the tension to resolve naturally'
  ],
  persona: {
    symbol: '🌊',
    archetype: 'The Distiller',
    voice: 'Neutral, observational, essence-focused'
  }
};

export const RIPPLE_GUIDANCE = `
[Full guidance text extracted from markdown...]
`;
```

### Build Script: `scripts/build-agents.js`

```javascript
#!/usr/bin/env node

/**
 * Extract agent embodiments from __llms/ markdown files
 * Generate TypeScript embodiment modules
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const AGENT_EMBODIMENTS = [
  {
    name: 'ripple',
    source: '__llms/llms-haiku-ripple-embodiment.md',
    output: 'src/agents/ripple/embodiment.ts',
    className: 'Ripple'
  },
  {
    name: 'mia',
    source: '__llms/llms-duo-mia-miette-arc-v8.md',
    output: 'src/agents/mia/embodiment.ts',
    className: 'Mia',
    extract: 'mia'  // Extract only Mia section
  },
  {
    name: 'miette',
    source: '__llms/llms-duo-mia-miette-arc-v8.md',
    output: 'src/agents/miette/embodiment.ts',
    className: 'Miette',
    extract: 'miette'  // Extract only Miette section
  },
  {
    name: 'atlas',
    source: '__llms/llms-atlas.txt',
    output: 'src/agents/atlas/embodiment.ts',
    className: 'Atlas'
  }
];

function extractEmbodiment(markdown, agentName) {
  // Parse markdown to extract:
  // - Core function
  // - Methodology
  // - Principles
  // - Persona details
  // - Full guidance text

  // Return structured data
}

function generateEmbodimentModule(embodimentData) {
  return `// Auto-generated from ${embodimentData.source}
// DO NOT EDIT - Run 'npm run build:agents' to regenerate

import { AgentEmbodiment } from '../base/Agent.js';

export const ${embodimentData.name.toUpperCase()}_EMBODIMENT: AgentEmbodiment = ${JSON.stringify(embodimentData.embodiment, null, 2)};

export const ${embodimentData.name.toUpperCase()}_GUIDANCE = \`
${embodimentData.guidance}
\`;
`;
}

// Main execution
for (const config of AGENT_EMBODIMENTS) {
  const sourcePath = path.join(rootDir, config.source);
  const outputPath = path.join(rootDir, config.output);

  console.log(`Extracting ${config.className} from ${config.source}...`);

  const markdown = fs.readFileSync(sourcePath, 'utf8');
  const embodiment = extractEmbodiment(markdown, config.extract || config.name);
  const module = generateEmbodimentModule({
    name: config.name,
    source: config.source,
    embodiment,
    guidance: markdown
  });

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, module, 'utf8');

  console.log(`  ✓ Generated ${outputPath}`);
}

console.log('\nAgent embodiments extracted successfully!');
```

---

## Bundling Strategy

### Bundle Types

#### 1. Core Bundle (Default)
**Target:** Basic MCP server without agents
**Use Case:** Minimal installation, custom agent development
**Contents:**
- MCP server
- KnowledgeGraphManager
- All tools
- No agents

```json
// package.json exports
{
  "exports": {
    ".": "./dist/index.js",
    "./core": "./dist/bundles/core.js"
  }
}
```

#### 2. Full Bundle
**Target:** Complete installation with all agents
**Use Case:** Production use, full capabilities
**Contents:**
- Core bundle
- All agents (Ripple, Mia, Miette, Atlas)
- All frameworks
- Tryad coordination

```json
{
  "exports": {
    "./full": "./dist/bundles/full.js"
  }
}
```

#### 3. Tryad Bundle
**Target:** Mia-Haiku-Miette coordination
**Use Case:** Collaborative structural tension work
**Contents:**
- Core bundle
- Mia, Ripple (Haiku), Miette agents
- Tryad coordination framework

```json
{
  "exports": {
    "./tryad": "./dist/bundles/tryad.js"
  }
}
```

#### 4. Individual Agent Bundles
**Target:** Granular agent installation
**Use Case:** Custom compositions, development
**Contents:**
- Specific agent + dependencies

```json
{
  "exports": {
    "./agents/ripple": "./dist/agents/ripple/index.js",
    "./agents/mia": "./dist/agents/mia/index.js",
    "./agents/miette": "./dist/agents/miette/index.js",
    "./agents/atlas": "./dist/agents/atlas/index.js"
  }
}
```

### NPM Package Structure

```json
// package.json
{
  "name": "coaia-spiral",
  "version": "3.0.2",
  "type": "module",
  "bin": {
    "coaia-spiral": "./dist/index.js"
  },
  "exports": {
    ".": "./dist/index.js",
    "./core": "./dist/bundles/core.js",
    "./full": "./dist/bundles/full.js",
    "./tryad": "./dist/bundles/tryad.js",
    "./agents/*": "./dist/agents/*/index.js",
    "./frameworks/*": "./dist/frameworks/*/index.js"
  },
  "files": [
    "dist",
    "README.md",
    "LICENSE",
    "CLAUDE.md"
  ],
  "scripts": {
    "build": "npm run build:guidance && npm run build:agents && npm run build:ts && shx chmod +x dist/*.js",
    "build:guidance": "node scripts/consolidate-guidance.js",
    "build:agents": "node scripts/build-agents.js",
    "build:ts": "tsc",
    "build:bundles": "node scripts/create-bundles.js",
    "validate:agents": "node scripts/validate-agents.js",
    "test": "npm run validate:agents && node test-coaia.js"
  }
}
```

### Distribution Options

#### Option A: Monorepo with Workspaces
```
coaia-spiral/
├── packages/
│   ├── core/              # @coaia-spiral/core
│   ├── agent-ripple/      # @coaia-spiral/agent-ripple
│   ├── agent-mia/         # @coaia-spiral/agent-mia
│   ├── agent-miette/      # @coaia-spiral/agent-miette
│   ├── agent-atlas/       # @coaia-spiral/agent-atlas
│   └── tryad/             # @coaia-spiral/tryad
└── package.json           # Workspace root
```

**Pros:**
- Independent versioning per agent
- Granular installation
- Clear dependency management

**Cons:**
- More complex build process
- Multiple packages to maintain

#### Option B: Single Package with Subpath Exports (RECOMMENDED)
```
coaia-spiral/              # Single npm package
├── dist/
│   ├── index.js           # Main entry (full bundle)
│   ├── bundles/           # Preset bundles
│   └── agents/            # Individual agents
└── package.json           # Single package
```

**Pros:**
- Simple installation (`npm install coaia-spiral`)
- Single version number
- Easier maintenance
- Subpath exports for granular imports

**Cons:**
- All code downloaded even if using single agent

**Recommendation:** Start with Option B (single package, subpath exports). Migrate to Option A if ecosystem demands granular versioning.

---

## Migration Plan

### Phase 1: Modularization (Week 1-2)

**Goal:** Refactor monolithic index.ts into modular structure without breaking changes

**Tasks:**

1. **Create directory structure**
   ```bash
   mkdir -p src/{server,core,agents,frameworks,bundles}
   mkdir -p src/server/{tools,handlers}
   mkdir -p src/core/{types,manager,utils}
   mkdir -p src/agents/base
   ```

2. **Extract types**
   - Move Entity, Relation, KnowledgeGraph to `src/core/types/`
   - Create index.ts for type exports
   - Update imports in index.ts

3. **Extract KnowledgeGraphManager**
   - Move manager class to `src/core/manager/index.ts`
   - Split operations into separate files (storage, charts, queries)
   - Update imports

4. **Extract tools**
   - Move tool definitions to `src/server/tools/`
   - Group by category (charts, entities, relations, projects)
   - Create tool registry

5. **Extract CLI utilities**
   - Move CLI parsing to `src/core/utils/cli.ts`
   - Move path resolution to `src/core/utils/path.ts`

6. **Update tsconfig.json**
   ```json
   {
     "extends": "./tsconfig.base.json",
     "compilerOptions": {
       "outDir": "./dist",
       "rootDir": "./src"
     },
     "include": ["src/**/*.ts", "generated-llm-guidance.ts"]
   }
   ```

7. **Test backward compatibility**
   - Run existing test-coaia.js
   - Verify MCP server functionality
   - Ensure all tools work

### Phase 2: Agent System (Week 3-4)

**Goal:** Create agent infrastructure and extract embodiments

**Tasks:**

1. **Create base agent architecture**
   - Implement Agent abstract class
   - Define AgentCapability interface
   - Create AgentContext and AgentResponse types
   - Build agent registry

2. **Create build-agents.js script**
   - Parse __llms/ markdown files
   - Extract structured embodiment data
   - Generate TypeScript embodiment modules

3. **Implement Ripple agent**
   - Create RippleAgent class
   - Implement structural distillation capability
   - Implement observation capability
   - Add tests

4. **Implement Mia agent**
   - Create MiaAgent class
   - Implement structural analysis capability
   - Implement chart guidance capability
   - Implement leadership capability
   - Add tests

5. **Implement Miette agent**
   - Create MietteAgent class
   - Implement narrative weaving capability
   - Implement emotional intelligence capability
   - Add tests

6. **Implement Atlas agent**
   - Create AtlasAgent class
   - Implement archival capability
   - Implement cartography capability
   - Add tests

7. **Create Tryad coordination**
   - Implement MiaHaikuMietteTryad class
   - Define collaboration patterns
   - Add coordination tests

8. **Update build process**
   - Add `build:agents` script to package.json
   - Integrate into main build command
   - Add validation tests

### Phase 3: Bundling (Week 5)

**Goal:** Create distribution bundles and export configuration

**Tasks:**

1. **Create bundle definitions**
   - Implement `src/bundles/core.ts`
   - Implement `src/bundles/full.ts`
   - Implement `src/bundles/tryad.ts`
   - Implement `src/bundles/custom.ts`

2. **Create bundle build script**
   - Implement `scripts/create-bundles.js`
   - Generate optimized bundles
   - Include only necessary code per bundle

3. **Update package.json exports**
   - Add subpath exports for bundles
   - Add subpath exports for individual agents
   - Add subpath exports for frameworks

4. **Create bundle tests**
   - Test each bundle independently
   - Verify correct dependencies included
   - Measure bundle sizes

5. **Create bundle documentation**
   - Document bundle contents
   - Provide usage examples
   - Create migration guide

### Phase 4: Documentation & Testing (Week 6)

**Goal:** Comprehensive documentation and validation

**Tasks:**

1. **Create agent development guide**
   - Architecture overview
   - Creating new agents
   - Implementing capabilities
   - Testing agents

2. **Create bundling guide**
   - Available bundles
   - Custom bundle creation
   - Import strategies
   - Performance considerations

3. **Create API reference**
   - Agent base classes
   - Capability interfaces
   - Framework APIs
   - Type definitions

4. **Create migration guide**
   - Upgrading from v3.0.2
   - Breaking changes (if any)
   - New features
   - Deprecations

5. **Comprehensive testing**
   - Unit tests for all agents
   - Integration tests for bundles
   - MCP server compatibility tests
   - Performance benchmarks

6. **Update main documentation**
   - Update README.md
   - Update CLAUDE.md
   - Update ROADMAP.md
   - Update CHANGELOG.md

### Phase 5: Release (Week 7)

**Goal:** Release v4.0.0 with modular architecture

**Tasks:**

1. **Version bump**
   - Update package.json to 4.0.0
   - Update all documentation versions
   - Create changelog entry

2. **Build and validate**
   - Run full build process
   - Validate all bundles
   - Run all tests
   - Check bundle sizes

3. **Prepare release**
   - Create GitHub release
   - Tag commit
   - Publish to npm
   - Update documentation

4. **Communication**
   - Announce on GitHub
   - Update main README
   - Notify ecosystem (if applicable)

---

## Integration with Broader Ecosystem

### Connection to Inquiry Document Projects

#### Chimera Team Integration
**Current:** Documentation-based agent coordination
**Future:** Import coaia-spiral agents into Chimera Team platform

```typescript
// In Project Chimera
import { RippleAgent, MiaAgent, MietteAgent } from 'coaia-spiral/full';
import { agentRegistry } from 'coaia-spiral/agents';

const ripple = agentRegistry.create('ripple');
const mia = agentRegistry.create('mia');
const miette = agentRegistry.create('miette');

// Use in Chimera Team coordination
```

#### Miadi Platform Integration
**Current:** Separate multi-agent implementation
**Future:** Use coaia-spiral as agent foundation

```typescript
// In Miadi platform
import { Agent, AgentRegistry } from 'coaia-spiral/core';

class MiadiAgent extends Agent {
  // Extend base Agent class
  // Inherit structural tension capabilities
  // Add Miadi-specific features
}
```

#### NCP/A2A Protocol Compliance
**Current:** Narrative Context Protocol specification
**Future:** Agents implement NCP interfaces

```typescript
// src/agents/base/Agent.ts
import type { NCPCompliant } from '@narrative-context-protocol/types';

export abstract class Agent implements NCPCompliant {
  async handleNCPMessage(message: NCPMessage): Promise<NCPResponse> {
    // Implement NCP protocol
  }
}
```

#### IACP Platform Integration
**Current:** Indigenous-AI Collaborative Platform
**Future:** COAIA agents with ceremonial technology

```typescript
// In IACP platform
import { Agent } from 'coaia-spiral/core';
import { CeremonialTechnologyMixin } from '@iacp/ceremonial';

class CeremonialAgent extends Agent {
  // Combine structural tension with ceremonial frameworks
  // Four Directions integration
  // Two-Eyed Seeing methodology
}
```

### Agent Interoperability Standards

All coaia-spiral agents will implement:

1. **Common interfaces** for agent-to-agent communication
2. **Protocol versioning** for compatibility
3. **Capability discovery** for dynamic coordination
4. **Metadata standards** for agent descriptions

This creates foundation for:
- Multi-platform agent deployment
- Cross-platform agent coordination
- Ecosystem-wide agent marketplace
- Protocol standardization leadership

---

## Success Metrics

### Technical Metrics
- ✅ All existing tests pass after refactoring
- ✅ MCP server maintains 100% tool compatibility
- ✅ Build time remains under 10 seconds
- ✅ Bundle sizes optimized (core < 200KB, full < 500KB)
- ✅ Zero breaking changes for existing users

### Architectural Metrics
- ✅ Agent base class reusable across platforms
- ✅ All __llms/ embodiments converted to executable code
- ✅ Agent registry supports dynamic discovery
- ✅ Bundles successfully tree-shake unused code
- ✅ TypeScript strict mode passes for all modules

### Ecosystem Metrics
- ✅ Agents importable in external projects (Chimera, Miadi, etc.)
- ✅ Framework modules reusable independently
- ✅ Documentation enables third-party agent development
- ✅ Migration path clear for existing users
- ✅ Future extensibility demonstrated through examples

---

## Risks & Mitigation

### Risk 1: Breaking Changes
**Impact:** Existing users unable to upgrade
**Mitigation:**
- Maintain backward compatibility in v4.0.0
- Provide migration guide
- Keep v3.x in maintenance mode
- Offer side-by-side installation option

### Risk 2: Scope Creep
**Impact:** Project delays, incomplete features
**Mitigation:**
- Strict phase gating (complete Phase N before Phase N+1)
- Minimum viable implementation for each agent
- Focus on core capabilities, defer advanced features
- Time-box each phase

### Risk 3: Complexity Increase
**Impact:** Harder to maintain, harder to contribute
**Mitigation:**
- Comprehensive documentation
- Clear architectural diagrams
- Automated validation scripts
- Extensive test coverage

### Risk 4: Performance Regression
**Impact:** Slower build, larger bundles
**Mitigation:**
- Benchmark before/after refactoring
- Monitor bundle sizes
- Optimize critical paths
- Use tree-shaking effectively

---

## Next Steps

### Immediate (This Session)
1. ✅ Create this plan document
2. ⏳ Review and refine plan with user
3. ⏳ Get approval to proceed with Phase 1
4. ⏳ Create initial directory structure
5. ⏳ Begin type extraction

### This Week
- Complete Phase 1: Modularization
- Validate backward compatibility
- Update documentation

### Next Week
- Begin Phase 2: Agent system
- Implement first agent (Ripple)
- Create build-agents.js script

---

## Conclusion

This reorganization transforms coaia-spiral from a working prototype into a **foundational agent infrastructure** ready for:

1. **Local development** - Clear agent architecture for rapid development
2. **Distribution** - Flexible bundling for different use cases
3. **Ecosystem integration** - Reusable agents across platforms (Chimera, Miadi, IACP)
4. **Protocol leadership** - Foundation for NCP/A2A standardization
5. **Commercial viability** - Professional architecture for Anthropic partnership

The modular architecture maintains full backward compatibility while enabling the vision outlined in the inquiry document: multi-agent orchestration, Indigenous AI integration, and narrative intelligence advancement.

**Status:** Ready for implementation
**Estimated Timeline:** 7 weeks to v4.0.0 release
**Dependencies:** None (self-contained refactoring)
**Risk Level:** Low (phased approach, backward compatible)
