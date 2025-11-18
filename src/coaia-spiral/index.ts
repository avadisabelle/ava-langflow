#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { promises as fs } from 'fs';
import { existsSync } from 'fs';
import path from 'path';
import { LLM_GUIDANCE } from "./generated-llm-guidance.js";
import { fileURLToPath } from 'url';
import minimist from 'minimist';
import { isAbsolute } from 'path';

// Parse args and handle paths safely
const argv = minimist(process.argv.slice(2));

// Handle help command
if (argv.help || argv.h) {
  console.log(`
🧠 COAIA Spiral - Creative-Oriented AI Assistant Memory System v2.4.0
   Based on Robert Fritz's Structural Tension methodology
   Enhanced with .coaia project organization

DESCRIPTION:
   MCP server that extends knowledge graphs with structural tension charts for 
   creative-oriented spiral memory management. Supports advancing patterns, telescoping
   charts, and natural language interaction for AI assistants.
   
   Project Organization:
   • .coaia directories for project-specific structural tension charts
   • Organized chart collections (active, completed, archived)
   • Chart templates and patterns for common goals
   • Project-local vs global chart management

USAGE:
   coaia-spiral [OPTIONS]
   npx coaia-spiral [OPTIONS]

OPTIONS:
   --memory-path PATH    Custom path for memory storage (default: ./memory.jsonl)
   --help, -h           Show this help message

CORE FEATURES:
   
   📊 Structural Tension Charts
   • Create charts with desired outcomes, current reality, and action steps
   • Automatic due date distribution for strategic timing
   • Progress tracking and completion monitoring
   
   🔭 Telescoping Support  
   • Break down action steps into detailed sub-charts
   • Proper due date inheritance from parent steps
   • Navigate between overview and details seamlessly
   
   📈 Advancing Patterns
   • Completed actions flow into current reality automatically  
   • Success builds momentum for continued advancement
   • Prevents oscillating patterns through structural awareness

MCP TOOLS AVAILABLE:
   
   Chart Management (Common Workflow):
   • list_active_charts            - START HERE: See all charts and their progress
   • add_action_step               - Add strategic actions to existing charts  
   • telescope_action_step         - Break down action steps into detailed sub-charts
   • update_action_progress        - Track progress without completing actions
   • mark_action_complete          - Complete actions & update reality
   • update_current_reality        - Add observations directly to current reality
   • create_structural_tension_chart - Create new chart with outcome & reality
   
   Project Organization (.coaia directories):
   • initialize_coaia_project      - Set up .coaia directory for organized charts
   • list_coaia_projects           - Show project status and chart organization  
   • move_chart_to_completed       - Archive completed charts as learning examples
   
   Chart Analysis (Advanced):
   • get_chart_progress            - Detailed progress (redundant after list_active_charts)
   • open_nodes                    - Inspect specific chart components by exact name
   • read_graph                    - Dump all data (rarely needed)
   
   Knowledge Graph (Traditional):
   • create_entities               - Add entities (people, concepts, events)
   • create_relations              - Connect entities with relationships  
   • add_observations              - Record information about entities
   • search_nodes                  - Search across all stored information
   • read_graph                    - Export complete graph structure

EXAMPLE USAGE:

   # Start with custom memory path
   coaia-spiral --memory-path /path/to/my-charts.jsonl
   
   # Use in Claude Desktop (add to claude_desktop_config.json):
   {
     "mcpServers": {
       "my-spiral-project": {
         "command": "npx", 
         "args": ["-y", "coaia-spiral", "--memory-path", "./charts.jsonl"]
       }
     }
   }

   # Initialize project-local chart organization
   mkdir my-project && cd my-project
   git init  # or npm init, etc. (any project marker)
   # Then use initialize_coaia_project tool in your AI assistant

PROJECT ORGANIZATION PATTERNS:

   Project Structure:
   my-project/
   ├── .coaia/
   │   ├── active-charts.jsonl      # Current structural tension charts
   │   ├── completed-charts.jsonl   # Archived successful charts  
   │   └── templates/
   │       └── common-goals.jsonl   # Reusable patterns
   └── src/
   
   Benefits:
   • Separate active from completed charts
   • Learn from successful patterns
   • Project-specific goal organization
   • Templates for common desired outcomes

NATURAL LANGUAGE PATTERNS:

   Creating Charts:
   "I want to create a mobile app in 3 months"
   "My desired outcome is to establish a morning routine"
   
   Progress Tracking:
   "I completed the research phase yesterday"  
   "Show me progress on my Python learning goal"
   
   Telescoping:
   "Break down the Django tutorial step further"
   "I need more detail on the deployment action"

CREATIVE ORIENTATION PRINCIPLES:

   ✅ Focus on Creation (not problem-solving):
      • "I want to create..." vs "I need to fix..."
      • "My desired outcome..." vs "The problem is..."
   
   ✅ Structural Tension Awareness:
      • Always pair desired outcomes with current reality
      • Honest assessment creates productive tension
      • Action steps are strategic secondary action we choose todo to achive the primary goal
   
   ✅ Advancing Patterns:
      • Success builds on success
      • Completed actions become part of current reality
      • Momentum creates natural progression toward goals

PHILOSOPHY:
   COAIA Memory recognizes that structure determines behavior. By organizing
   memory around structural tension rather than problem-solving patterns, it
   naturally forms a structure that advances and helps build, not just the life you want, but the technologies to supports it's manifestation (hopefully!).

CREDITS:
   • Author: J.Guillaume D.-Isabelle <jgi@jgwill.com>
   • Methodology: Robert Fritz - https://robertfritz.com
   • Foundation: Shane Holloman (original mcp-knowledge-graph)
   • License: MIT

For more information, see: CLAUDE.md in the package directory
`);
  process.exit(0);
}

let memoryPath = argv['memory-path'];

// If a custom path is provided, ensure it's absolute
if (memoryPath && !isAbsolute(memoryPath)) {
    memoryPath = path.resolve(process.cwd(), memoryPath);
}

// Define the path to the JSONL file
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// COAIA Project Detection - look for common project markers
function findProjectRoot(startDir: string = process.cwd()): string | null {
  const projectMarkers = ['.git', 'package.json', 'pyproject.toml', 'Cargo.toml', 'go.mod'];
  let currentDir = startDir;
  const maxDepth = 5;

  for (let i = 0; i < maxDepth; i++) {
    // Check for project markers
    for (const marker of projectMarkers) {
      if (existsSync(path.join(currentDir, marker))) {
        return currentDir;
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

  return null;
}

// COAIA-specific storage management for structural tension charts with flexible contexts
// Priority: 1) Configured --memory-path, 2) Project .coaia directory, 3) Default
function getCoaiaStoragePath(context?: string): string {
  const filename = context ? `charts-${context}.jsonl` : 'charts.jsonl';
  
  // FIRST PRIORITY: Use configured --memory-path (AIM philosophy)
  if (memoryPath) {
    // If memoryPath points to a directory, use it as base for chart files
    if (memoryPath.endsWith('/') || !memoryPath.endsWith('.jsonl')) {
      const dir = memoryPath.endsWith('/') ? memoryPath : memoryPath + '/';
      return path.join(dir, filename);
    }
    
    // If memoryPath is a specific file, use it for default context or create contextual version
    if (context) {
      const dir = path.dirname(memoryPath);
      const name = path.basename(memoryPath, '.jsonl');
      return path.join(dir, `${name}-${context}.jsonl`);
    }
    return memoryPath;
  }
  
  // SECOND PRIORITY: Check for project .coaia directory
  const projectRoot = findProjectRoot();
  if (projectRoot) {
    const coaiaDir = path.join(projectRoot, '.coaia');
    if (existsSync(coaiaDir)) {
      return path.join(coaiaDir, filename);
    }
  }
  
  // THIRD PRIORITY: Default fallback
  return path.join(__dirname, 'memory.jsonl');
}

// Use the custom path or default to the installation directory
const MEMORY_FILE_PATH = getCoaiaStoragePath();

// We are storing our memory using entities, relations, and observations in a graph structure
// Extended for Creative Orientation AI Assistant (COAIA) with structural tension support
interface Entity {
  name: string;
  entityType: string;
  observations: string[];
  metadata?: {
    dueDate?: string;
    chartId?: string;
    phase?: 'germination' | 'assimilation' | 'completion';
    completionStatus?: boolean;
    parentChart?: string;
    parentActionStep?: string;
    level?: number;
    context?: string;
    createdAt?: string;
    updatedAt?: string;
  };
}

interface Relation {
  from: string;
  to: string;
  relationType: string;
  metadata?: {
    createdAt?: string;
    strength?: number;
  };
}

interface KnowledgeGraph {
  entities: Entity[];
  relations: Relation[];
}

// The KnowledgeGraphManager class contains all operations to interact with the knowledge graph
class KnowledgeGraphManager {
  private async loadGraph(): Promise<KnowledgeGraph> {
    try {
      const data = await fs.readFile(MEMORY_FILE_PATH, "utf-8");
      const lines = data.split("\n").filter(line => line.trim() !== "");
      return lines.reduce((graph: KnowledgeGraph, line) => {
        const item = JSON.parse(line);
        if (item.type === "entity") graph.entities.push(item as Entity);
        if (item.type === "relation") graph.relations.push(item as Relation);
        return graph;
      }, { entities: [], relations: [] });
    } catch (error) {
      if (error instanceof Error && 'code' in error && (error as any).code === "ENOENT") {
        return { entities: [], relations: [] };
      }
      throw error;
    }
  }

  // Helper function to extract current reality from user context
  // Maintains structural tension by requiring explicit assessment
  private extractCurrentRealityFromContext(userInput: string, actionStepTitle: string): string | null {
    // Common patterns that indicate current reality assessment
    const realityPatterns = [
      /(?:currently|right now|at present|today)\s+(.{10,})/i,
      /(?:i am|we are|the situation is)\s+(.{10,})/i,
      /(?:i have|we have|there is|there are)\s+(.{10,})/i,
      /(?:my current|our current|the current)\s+(.{10,})/i
    ];

    for (const pattern of realityPatterns) {
      const match = userInput.match(pattern);
      if (match && match[1]) {
        return match[1].trim();
      }
    }

    // If no explicit current reality found, require assessment
    return null;
  }

  // Helper method to determine if we should use COAIA context-aware persistence
  private shouldUseCoaiaPersistence(): boolean {
    // If --memory-path is configured, always use COAIA persistence for context support
    if (memoryPath) {
      return true;
    }
    
    // Otherwise, check for project .coaia directory
    const projectRoot = findProjectRoot();
    return projectRoot !== null && existsSync(path.join(projectRoot, '.coaia'));
  }

  // Helper method to save graph using appropriate persistence method
  private async saveGraphAppropriate(graph: KnowledgeGraph, context?: string): Promise<void> {
    if (this.shouldUseCoaiaPersistence()) {
      await this.saveCoaiaGraph(graph, context);
    } else {
      await this.saveGraph(graph);
    }
  }

  // COAIA context-aware methods (similar to AIM approach but for structural tension charts)
  private async loadCoaiaGraph(context?: string): Promise<KnowledgeGraph> {
    const filePath = getCoaiaStoragePath(context);
    try {
      const data = await fs.readFile(filePath, "utf-8");
      const lines = data.split("\n").filter(line => line.trim() !== "" && !line.startsWith("#"));
      return lines.reduce((graph: KnowledgeGraph, line) => {
        const item = JSON.parse(line);
        if (item.type === "entity") graph.entities.push(item as Entity);
        if (item.type === "relation") graph.relations.push(item as Relation);
        return graph;
      }, { entities: [], relations: [] });
    } catch (error) {
      if (error instanceof Error && 'code' in error && (error as any).code === "ENOENT") {
        return { entities: [], relations: [] };
      }
      throw error;
    }
  }

  private async saveCoaiaGraph(graph: KnowledgeGraph, context?: string): Promise<void> {
    const filePath = getCoaiaStoragePath(context);
    const lines = [
      ...graph.entities.map(e => JSON.stringify({ type: "entity", ...e })),
      ...graph.relations.map(r => JSON.stringify({ type: "relation", ...r })),
    ];
    
    // Ensure directory exists
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.writeFile(filePath, lines.join("\n"));
  }

  // Legacy saveGraph method for backward compatibility
  private async saveGraph(graph: KnowledgeGraph): Promise<void> {
    const lines = [
      ...graph.entities.map(e => JSON.stringify({ type: "entity", ...e })),
      ...graph.relations.map(r => JSON.stringify({ type: "relation", ...r })),
    ];
    await fs.writeFile(MEMORY_FILE_PATH, lines.join("\n"));
  }

  async createEntities(entities: Entity[]): Promise<Entity[]> {
    const graph = this.shouldUseCoaiaPersistence() ? await this.loadCoaiaGraph() : await this.loadGraph();
    const newEntities = entities.filter(e => !graph.entities.some(existingEntity => existingEntity.name === e.name));
    graph.entities.push(...newEntities);
    await this.saveGraphAppropriate(graph);
    return newEntities;
  }

  async createRelations(relations: Relation[]): Promise<Relation[]> {
    const graph = this.shouldUseCoaiaPersistence() ? await this.loadCoaiaGraph() : await this.loadGraph();
    const newRelations = relations.filter(r => !graph.relations.some(existingRelation =>
      existingRelation.from === r.from &&
      existingRelation.to === r.to &&
      existingRelation.relationType === r.relationType
    ));
    graph.relations.push(...newRelations);
    await this.saveGraphAppropriate(graph);
    return newRelations;
  }

  async addObservations(observations: { entityName: string; contents: string[] }[]): Promise<{ entityName: string; addedObservations: string[] }[]> {
    const graph = await this.loadGraph();
    const results = observations.map(o => {
      const entity = graph.entities.find(e => e.name === o.entityName);
      if (!entity) {
        throw new Error(`Entity with name ${o.entityName} not found`);
      }
      const newObservations = o.contents.filter(content => !entity.observations.includes(content));
      entity.observations.push(...newObservations);
      return { entityName: o.entityName, addedObservations: newObservations };
    });
    await this.saveGraph(graph);
    return results;
  }

  async deleteEntities(entityNames: string[]): Promise<void> {
    const graph = await this.loadGraph();
    graph.entities = graph.entities.filter(e => !entityNames.includes(e.name));
    graph.relations = graph.relations.filter(r => !entityNames.includes(r.from) && !entityNames.includes(r.to));
    await this.saveGraph(graph);
  }

  async deleteObservations(deletions: { entityName: string; observations: string[] }[]): Promise<void> {
    const graph = await this.loadGraph();
    deletions.forEach(d => {
      const entity = graph.entities.find(e => e.name === d.entityName);
      if (entity) {
        entity.observations = entity.observations.filter(o => !d.observations.includes(o));
      }
    });
    await this.saveGraph(graph);
  }

  async deleteRelations(relations: Relation[]): Promise<void> {
    const graph = await this.loadGraph();
    graph.relations = graph.relations.filter(r => !relations.some(delRelation =>
      r.from === delRelation.from &&
      r.to === delRelation.to &&
      r.relationType === delRelation.relationType
    ));
    await this.saveGraph(graph);
  }

  async readGraph(): Promise<KnowledgeGraph> {
    return this.loadGraph();
  }

  // Very basic search function
  async searchNodes(query: string): Promise<KnowledgeGraph> {
    const graph = await this.loadGraph();

    // Filter entities
    const filteredEntities = graph.entities.filter(e =>
      e.name.toLowerCase().includes(query.toLowerCase()) ||
      e.entityType.toLowerCase().includes(query.toLowerCase()) ||
      e.observations.some(o => o.toLowerCase().includes(query.toLowerCase()))
    );

    // Create a Set of filtered entity names for quick lookup
    const filteredEntityNames = new Set(filteredEntities.map(e => e.name));

    // Filter relations to only include those between filtered entities
    const filteredRelations = graph.relations.filter(r =>
      filteredEntityNames.has(r.from) && filteredEntityNames.has(r.to)
    );

    const filteredGraph: KnowledgeGraph = {
      entities: filteredEntities,
      relations: filteredRelations,
    };

    return filteredGraph;
  }

  async openNodes(names: string[]): Promise<KnowledgeGraph> {
    const graph = await this.loadGraph();

    // Filter entities
    const filteredEntities = graph.entities.filter(e => names.includes(e.name));

    // Create a Set of filtered entity names for quick lookup
    const filteredEntityNames = new Set(filteredEntities.map(e => e.name));

    // Filter relations to only include those between filtered entities
    const filteredRelations = graph.relations.filter(r =>
      filteredEntityNames.has(r.from) && filteredEntityNames.has(r.to)
    );

    const filteredGraph: KnowledgeGraph = {
      entities: filteredEntities,
      relations: filteredRelations,
    };

    return filteredGraph;
  }

  // COAIA-specific methods for structural tension charts and creative processes

  async createStructuralTensionChart(
    desiredOutcome: string,
    currentReality: string,
    dueDate: string,
    actionSteps?: string[]
  ): Promise<{ chartId: string; entities: Entity[]; relations: Relation[] }> {
    // Educational validation for creative orientation
    const problemSolvingWords = ['fix', 'solve', 'eliminate', 'prevent', 'stop', 'avoid', 'reduce', 'remove'];
    const detectedProblemWords = problemSolvingWords.filter(word => 
      desiredOutcome.toLowerCase().includes(word)
    );
    
    if (detectedProblemWords.length > 0) {
      throw new Error(`🌊 CREATIVE ORIENTATION REQUIRED

Desired Outcome: "${desiredOutcome}"

❌ **Problem**: Contains problem-solving language: "${detectedProblemWords.join(', ')}"
📚 **Principle**: Structural Tension Charts use creative orientation - focus on what you want to CREATE, not what you want to eliminate.

🎯 **Reframe Your Outcome**:
Instead of elimination → Creation focus

✅ **Examples**:
- Instead of: "Fix communication problems"
- Use: "Establish clear, effective communication practices"

- Instead of: "Reduce website loading time"  
- Use: "Achieve fast, responsive website performance"

**Why This Matters**: Problem-solving creates oscillating patterns. Creative orientation creates advancing patterns toward desired outcomes.

💡 **Tip**: Run 'init_llm_guidance' for complete methodology overview.`);
    }
    
    // Educational validation for current reality
    const readinessWords = ['ready to', 'prepared to', 'all set', 'ready for', 'set to'];
    const detectedReadinessWords = readinessWords.filter(phrase => 
      currentReality.toLowerCase().includes(phrase)
    );
    
    if (detectedReadinessWords.length > 0) {
      throw new Error(`🌊 DELAYED RESOLUTION PRINCIPLE VIOLATION

Current Reality: "${currentReality}"

❌ **Problem**: Contains readiness assumptions: "${detectedReadinessWords.join(', ')}"
📚 **Principle**: "Tolerate discrepancy, tension, and delayed resolution" - Robert Fritz

🎯 **What's Needed**: Factual assessment of your actual current state (not readiness or preparation).

✅ **Examples**:
- Instead of: "Ready to learn Python"
- Use: "Never programmed before, interested in web development"

- Instead of: "Prepared to start the project"
- Use: "Have project requirements, no code written yet"

**Why This Matters**: Readiness assumptions prematurely resolve the structural tension needed for creative advancement.

💡 **Tip**: Run 'init_llm_guidance' for complete methodology overview.`);
    }

    const chartId = `chart_${Date.now()}`;
    const timestamp = new Date().toISOString();
    
    // Create chart, desired outcome, and current reality entities
    const entities: Entity[] = [
      {
        name: `${chartId}_chart`,
        entityType: 'structural_tension_chart',
        observations: [`Chart created on ${timestamp}`],
        metadata: {
          chartId,
          dueDate,
          level: 0,
          createdAt: timestamp,
          updatedAt: timestamp
        }
      },
      {
        name: `${chartId}_desired_outcome`,
        entityType: 'desired_outcome',
        observations: [desiredOutcome],
        metadata: {
          chartId,
          dueDate,
          createdAt: timestamp,
          updatedAt: timestamp
        }
      },
      {
        name: `${chartId}_current_reality`,
        entityType: 'current_reality',
        observations: [currentReality],
        metadata: {
          chartId,
          createdAt: timestamp,
          updatedAt: timestamp
        }
      }
    ];

    // Add action steps if provided
    if (actionSteps && actionSteps.length > 0) {
      const stepDueDates = this.distributeActionStepDates(new Date(), new Date(dueDate), actionSteps.length);
      
      actionSteps.forEach((step, index) => {
        entities.push({
          name: `${chartId}_action_${index + 1}`,
          entityType: 'action_step',
          observations: [step],
          metadata: {
            chartId,
            dueDate: stepDueDates[index].toISOString(),
            completionStatus: false,
            createdAt: timestamp,
            updatedAt: timestamp
          }
        });
      });
    }

    // Create relations
    const relations: Relation[] = [
      {
        from: `${chartId}_chart`,
        to: `${chartId}_desired_outcome`,
        relationType: 'contains',
        metadata: { createdAt: timestamp }
      },
      {
        from: `${chartId}_chart`,
        to: `${chartId}_current_reality`,
        relationType: 'contains',
        metadata: { createdAt: timestamp }
      },
      {
        from: `${chartId}_current_reality`,
        to: `${chartId}_desired_outcome`,
        relationType: 'creates_tension_with',
        metadata: { createdAt: timestamp }
      }
    ];

    // Add action step relations
    if (actionSteps && actionSteps.length > 0) {
      actionSteps.forEach((_, index) => {
        const actionName = `${chartId}_action_${index + 1}`;
        relations.push(
          {
            from: `${chartId}_chart`,
            to: actionName,
            relationType: 'contains',
            metadata: { createdAt: timestamp }
          },
          {
            from: actionName,
            to: `${chartId}_desired_outcome`,
            relationType: 'advances_toward',
            metadata: { createdAt: timestamp }
          }
        );
      });
    }

    // Save to graph
    await this.createEntities(entities);
    await this.createRelations(relations);

    return { chartId, entities, relations };
  }

  async telescopeActionStep(
    actionStepName: string,
    newCurrentReality: string,
    initialActionSteps?: string[]
  ): Promise<{ chartId: string; parentChart: string }> {
    const graph = this.shouldUseCoaiaPersistence() ? await this.loadCoaiaGraph() : await this.loadGraph();
    const actionStep = graph.entities.find(e => e.name === actionStepName && e.entityType === 'action_step');
    
    if (!actionStep || !actionStep.metadata?.chartId) {
      throw new Error(`Action step ${actionStepName} not found or not properly configured`);
    }

    const parentChartId = actionStep.metadata.chartId;
    const inheritedDueDate = actionStep.metadata.dueDate || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
    const desiredOutcome = actionStep.observations[0]; // Use the action step description as the new desired outcome

    const result = await this.createStructuralTensionChart(
      desiredOutcome,
      newCurrentReality,
      inheritedDueDate,
      initialActionSteps
    );

    // Update the new chart's metadata to reflect telescoping relationship
    const newChart = this.shouldUseCoaiaPersistence() ? await this.loadCoaiaGraph() : await this.loadGraph();
    const chartEntity = newChart.entities.find(e => e.name === `${result.chartId}_chart`);
    if (chartEntity && chartEntity.metadata) {
      chartEntity.metadata.parentChart = parentChartId;
      chartEntity.metadata.parentActionStep = actionStepName;
      chartEntity.metadata.level = (actionStep.metadata.level || 0) + 1;
      chartEntity.metadata.updatedAt = new Date().toISOString();
    }

    await this.saveGraphAppropriate(newChart);

    return { chartId: result.chartId, parentChart: parentChartId };
  }

  async markActionStepComplete(actionStepName: string): Promise<void> {
    const graph = this.shouldUseCoaiaPersistence() ? await this.loadCoaiaGraph() : await this.loadGraph();
    // An "action step" can be a 'desired_outcome' of a sub-chart, or a simple 'action_step' entity.
    const actionStep = graph.entities.find(e => e.name === actionStepName && (e.entityType === 'action_step' || e.entityType === 'desired_outcome'));

    if (!actionStep) {
      throw new Error(`Action step ${actionStepName} not found`);
    }

    const chartId = actionStep.metadata?.chartId;
    if (!chartId) {
      throw new Error(`Chart ID not found for action step ${actionStepName}`);
    }

    // Mark the action step itself as complete
    if (actionStep.metadata) {
      actionStep.metadata.completionStatus = true;
      actionStep.metadata.updatedAt = new Date().toISOString();
    }

    // Also mark the parent chart entity as complete
    const chartEntity = graph.entities.find(e => e.name === `${chartId}_chart`);
    if (chartEntity && chartEntity.metadata) {
      chartEntity.metadata.completionStatus = true;
      chartEntity.metadata.updatedAt = new Date().toISOString();
    }

    // Structural tension principle: completed action steps flow into the CURRENT REALITY
    // of the PARENT chart, advancing the overall structure.
    const parentChartId = chartEntity?.metadata?.parentChart;
    if (parentChartId) {
      const parentCurrentReality = graph.entities.find(e =>
        e.name === `${parentChartId}_current_reality` &&
        e.entityType === 'current_reality'
      );

      if (parentCurrentReality) {
        const completionMessage = `Completed: ${actionStep.observations[0]}`;
        if (!parentCurrentReality.observations.includes(completionMessage)) {
          parentCurrentReality.observations.push(completionMessage);
          if (parentCurrentReality.metadata) {
            parentCurrentReality.metadata.updatedAt = new Date().toISOString();
          }
        }
      }
    }

    await this.saveGraphAppropriate(graph);
  }

  async getChartProgress(chartId: string): Promise<{
    chartId: string;
    progress: number;
    completedActions: number;
    totalActions: number;
    nextAction?: string;
    dueDate?: string;
  }> {
    const graph = await this.loadGraph();
    const actionSteps = graph.entities.filter(e => 
      e.entityType === 'action_step' && 
      e.metadata?.chartId === chartId
    );

    const completedActions = actionSteps.filter(e => e.metadata?.completionStatus === true).length;
    const totalActions = actionSteps.length;
    const progress = totalActions > 0 ? completedActions / totalActions : 0;

    // Find next incomplete action step with earliest due date
    const incompleteActions = actionSteps
      .filter(e => e.metadata?.completionStatus !== true)
      .sort((a, b) => {
        const dateA = new Date(a.metadata?.dueDate || '').getTime();
        const dateB = new Date(b.metadata?.dueDate || '').getTime();
        return dateA - dateB;
      });

    const chart = graph.entities.find(e => e.name === `${chartId}_chart`);

    return {
      chartId,
      progress,
      completedActions,
      totalActions,
      nextAction: incompleteActions[0]?.name,
      dueDate: chart?.metadata?.dueDate
    };
  }

  private distributeActionStepDates(startDate: Date, endDate: Date, stepCount: number): Date[] {
    const totalTime = endDate.getTime() - startDate.getTime();
    const stepInterval = totalTime / (stepCount + 1); // +1 to leave space before final due date
    
    const dates: Date[] = [];
    for (let i = 1; i <= stepCount; i++) {
      dates.push(new Date(startDate.getTime() + (stepInterval * i)));
    }
    
    return dates;
  }

  async listActiveCharts(): Promise<Array<{
    chartId: string;
    desiredOutcome: string;
    dueDate?: string;
    progress: number;
    completedActions: number;
    totalActions: number;
    level: number;
    parentChart?: string;
  }>> {
    const graph = await this.loadGraph();
    const charts = graph.entities.filter(e => e.entityType === 'structural_tension_chart');
    
    const chartSummaries = await Promise.all(
      charts.map(async (chart) => {
        const chartId = chart.metadata?.chartId || chart.name.replace('_chart', '');
        const progress = await this.getChartProgress(chartId);
        
        // Get desired outcome
        const desiredOutcome = graph.entities.find(e => 
          e.name === `${chartId}_desired_outcome` && e.entityType === 'desired_outcome'
        );
        
        return {
          chartId,
          desiredOutcome: desiredOutcome?.observations[0] || 'Unknown outcome',
          dueDate: chart.metadata?.dueDate,
          progress: progress.progress,
          completedActions: progress.completedActions,
          totalActions: progress.totalActions,
          level: chart.metadata?.level || 0,
          parentChart: chart.metadata?.parentChart
        };
      })
    );

    return chartSummaries.sort((a, b) => {
      // Sort by level first (master charts first), then by due date
      if (a.level !== b.level) return a.level - b.level;
      
      const dateA = new Date(a.dueDate || '').getTime();
      const dateB = new Date(b.dueDate || '').getTime();
      return dateA - dateB;
    });
  }

  async updateActionProgress(
    actionStepName: string, 
    progressObservation: string,
    updateCurrentReality?: boolean
  ): Promise<void> {
    const graph = await this.loadGraph();
    const actionStep = graph.entities.find(e => e.name === actionStepName && (e.entityType === 'action_step' || e.entityType === 'desired_outcome'));
    
    if (!actionStep) {
      throw new Error(`Action step ${actionStepName} not found`);
    }

    // Add progress observation to action step
    actionStep.observations.push(progressObservation);
    if (actionStep.metadata) {
      actionStep.metadata.updatedAt = new Date().toISOString();
    }

    // Optionally update current reality with progress
    if (updateCurrentReality && actionStep.metadata?.chartId) {
      const chartEntity = graph.entities.find(e => e.name === `${actionStep.metadata!.chartId}_chart`);
      const parentChartId = chartEntity?.metadata?.parentChart;
      const targetChartId = parentChartId || actionStep.metadata!.chartId;

      const currentReality = graph.entities.find(e => 
        e.name === `${targetChartId}_current_reality` && 
        e.entityType === 'current_reality'
      );
      
      if (currentReality) {
        // Progress observations flow into current reality, changing the structural dynamic
        const progressMessage = `Progress on ${actionStep.observations[0]}: ${progressObservation}`;
        if (!currentReality.observations.includes(progressMessage)) {
          currentReality.observations.push(progressMessage);
          if (currentReality.metadata) {
            currentReality.metadata.updatedAt = new Date().toISOString();
          }
        }
      }
    }

    await this.saveGraph(graph);
  }

  async updateCurrentReality(chartId: string, newObservations: string[]): Promise<void> {
    const graph = await this.loadGraph();
    const currentReality = graph.entities.find(e => 
      e.name === `${chartId}_current_reality` && 
      e.entityType === 'current_reality'
    );
    
    if (!currentReality) {
      throw new Error(`Chart ${chartId} not found or missing current reality`);
    }

    // Add new observations to current reality
    const uniqueObservations = newObservations.filter(obs => !currentReality.observations.includes(obs));
    currentReality.observations.push(...uniqueObservations);
    
    if (currentReality.metadata) {
      currentReality.metadata.updatedAt = new Date().toISOString();
    }

    await this.saveGraph(graph);
  }

  async updateDesiredOutcome(chartId: string, newDesiredOutcome: string): Promise<void> {
    const graph = await this.loadGraph();
    const desiredOutcomeEntity = graph.entities.find(e => 
      e.name === `${chartId}_desired_outcome` && e.entityType === 'desired_outcome'
    );
    
    if (!desiredOutcomeEntity) {
      throw new Error(`Chart ${chartId} desired outcome not found`);
    }

    // Replace the first observation (which is the desired outcome text)
    desiredOutcomeEntity.observations[0] = newDesiredOutcome;
    
    if (desiredOutcomeEntity.metadata) {
      desiredOutcomeEntity.metadata.updatedAt = new Date().toISOString();
    }

    await this.saveGraph(graph);
  }

  async updateActionStepTitle(actionStepName: string, newTitle: string): Promise<void> {
    const graph = await this.loadGraph();
    const actionStepEntity = graph.entities.find(e => e.name === actionStepName);
    
    if (!actionStepEntity) {
      throw new Error(`Action step ${actionStepName} not found`);
    }

    // Replace the first observation (which is the action step title)
    actionStepEntity.observations[0] = newTitle;
    
    if (actionStepEntity.metadata) {
      actionStepEntity.metadata.updatedAt = new Date().toISOString();
    }

    await this.saveGraph(graph);
  }

  async addActionStep(
    parentChartId: string,
    actionStepTitle: string,
    dueDate?: string,
    currentReality?: string
  ): Promise<{ chartId: string; actionStepName: string }> {
    const graph = await this.loadGraph();
    const parentChart = graph.entities.find(e => 
      e.entityType === 'structural_tension_chart' && e.metadata?.chartId === parentChartId
    );
    
    if (!parentChart) {
      throw new Error(`Parent chart ${parentChartId} not found`);
    }

    // Get parent chart's due date for auto-distribution
    const parentDueDate = parentChart.metadata?.dueDate;
    if (!parentDueDate) {
      throw new Error(`Parent chart ${parentChartId} has no due date`);
    }

    // Calculate due date for action step if not provided
    let actionStepDueDate = dueDate;
    if (!actionStepDueDate) {
      // Distribute between now and parent due date (simple midpoint for now)
      const now = new Date();
      const parentEnd = new Date(parentDueDate);
      const midpoint = new Date(now.getTime() + (parentEnd.getTime() - now.getTime()) / 2);
      actionStepDueDate = midpoint.toISOString();
    }

    // Require current reality assessment - no defaults that prematurely resolve tension
    if (!currentReality) {
      throw new Error(`🌊 DELAYED RESOLUTION PRINCIPLE VIOLATION

Action step: "${actionStepTitle}"

❌ **Problem**: Current reality assessment missing
📚 **Principle**: "Tolerate discrepancy, tension, and delayed resolution" - Robert Fritz

🎯 **What's Needed**: Honest assessment of your actual current state relative to this action step.

✅ **Examples**:
- "Never used Django, completed Python basics"  
- "Built one API, struggling with authentication"
- "Read 3 chapters, concepts still unclear"

❌ **Avoid**: "Ready to begin", "Prepared to start", "All set to..."

**Why This Matters**: Premature resolution destroys the structural tension that generates creative advancement. The system NEEDS honest current reality to create productive tension.

💡 **Tip**: Run 'init_llm_guidance' for complete methodology overview.`);
    }
    
    const actionCurrentReality = currentReality;

    // Create telescoped structural tension chart
    const telescopedChart = await this.createStructuralTensionChart(
      actionStepTitle,
      actionCurrentReality, 
      actionStepDueDate
    );

    // Update the telescoped chart's metadata to show parent relationship
    const updatedGraph = await this.loadGraph();
    const telescopedChartEntity = updatedGraph.entities.find(e => e.name === `${telescopedChart.chartId}_chart`);
    if (telescopedChartEntity && telescopedChartEntity.metadata) {
      telescopedChartEntity.metadata.parentChart = parentChartId;
      telescopedChartEntity.metadata.level = (parentChart.metadata?.level || 0) + 1;
      telescopedChartEntity.metadata.updatedAt = new Date().toISOString();
    }

    // Create relationship: telescoped chart advances toward parent's desired outcome
    const parentDesiredOutcome = updatedGraph.entities.find(e => 
      e.name === `${parentChartId}_desired_outcome` && e.entityType === 'desired_outcome'
    );

    if (parentDesiredOutcome) {
      const timestamp = new Date().toISOString();
      await this.createRelations([{
        from: `${telescopedChart.chartId}_desired_outcome`,
        to: parentDesiredOutcome.name,
        relationType: 'advances_toward',
        metadata: { createdAt: timestamp }
      }]);
    }

    await this.saveGraph(updatedGraph);

    return { 
      chartId: telescopedChart.chartId, 
      actionStepName: `${telescopedChart.chartId}_desired_outcome` 
    };
  }

  // Enhanced method for LLMs to telescope with intelligent current reality extraction
  async telescopeActionStepWithContext(
    parentChartId: string, 
    actionStepTitle: string, 
    userContext: string,
    currentReality?: string,
    dueDate?: string
  ): Promise<{ chartId: string; actionStepName: string }> {
    
    // If current reality not provided, try to extract from context
    let finalCurrentReality = currentReality;
    if (!finalCurrentReality) {
      finalCurrentReality = this.extractCurrentRealityFromContext(userContext, actionStepTitle) ?? undefined;
    }
    
    // If still no current reality, provide guidance while maintaining tension
    if (!finalCurrentReality) {
      throw new Error(
        `Current reality assessment needed for "${actionStepTitle}". ` +
        `Please assess your actual current state relative to this action step. ` +
        `Example: "I have never used Django before" or "I completed the basics but haven't built a real project" ` +
        `rather than assuming readiness. Structural tension requires honest current reality assessment.`
      );
    }
    
    // Proceed with telescoping using the assessed current reality
    return this.addActionStep(parentChartId, actionStepTitle, finalCurrentReality, dueDate);
  }

  async removeActionStep(parentChartId: string, actionStepName: string): Promise<void> {
    const graph = await this.loadGraph();
    
    // Find the action step (which is actually a telescoped chart's desired outcome)
    const actionStepEntity = graph.entities.find(e => e.name === actionStepName);
    if (!actionStepEntity || !actionStepEntity.metadata?.chartId) {
      throw new Error(`Action step ${actionStepName} not found`);
    }

    const telescopedChartId = actionStepEntity.metadata.chartId;
    
    // Verify it belongs to the parent chart
    const telescopedChart = graph.entities.find(e => 
      e.entityType === 'structural_tension_chart' && 
      e.metadata?.chartId === telescopedChartId &&
      e.metadata?.parentChart === parentChartId
    );
    
    if (!telescopedChart) {
      throw new Error(`Action step ${actionStepName} does not belong to chart ${parentChartId}`);
    }

    // Remove all entities belonging to the telescoped chart
    const entitiesToRemove = graph.entities
      .filter(e => e.metadata?.chartId === telescopedChartId)
      .map(e => e.name);

    await this.deleteEntities(entitiesToRemove);
  }

  // COAIA Project Organization - Enhanced chart management for .coaia directories
  
  async initializeCoaiaProject(): Promise<{ message: string; structure: any }> {
    // Determine the target directory based on configuration priority (same as getCoaiaStoragePath)
    let coaiaDir: string;
    
    if (memoryPath) {
      // If --memory-path is configured, use it as the base directory
      coaiaDir = memoryPath.endsWith('/') ? memoryPath : (memoryPath.endsWith('.jsonl') ? path.dirname(memoryPath) : memoryPath);
    } else {
      // Fallback to project root detection
      const projectRoot = findProjectRoot();
      if (!projectRoot) {
        throw new Error('No project detected and no --memory-path configured. Either run from within a project directory (must contain .git, package.json, etc.) or provide --memory-path');
      }
      coaiaDir = path.join(projectRoot, '.coaia');
    }
    
    // Create directory structure
    await fs.mkdir(coaiaDir, { recursive: true });
    await fs.mkdir(path.join(coaiaDir, 'templates'), { recursive: true });
    
    // Initialize default chart file (master database equivalent)
    const defaultChartFile = path.join(coaiaDir, 'charts.jsonl');
    if (!existsSync(defaultChartFile)) {
      await fs.writeFile(defaultChartFile, '', 'utf-8');
    }

    // Create sample context files to demonstrate the concept
    const sampleContexts = ['work', 'personal', 'learning'];
    for (const context of sampleContexts) {
      const contextFile = path.join(coaiaDir, `charts-${context}.jsonl`);
      if (!existsSync(contextFile)) {
        await fs.writeFile(contextFile, `# COAIA Charts for ${context} context\n`, 'utf-8');
      }
    }

    // Create template files
    const templatePath = path.join(coaiaDir, 'templates', 'common-goals.txt');
    const templateContent = [
      '# COAIA Memory - Structural Tension Chart Templates',
      '# Use different contexts for different areas of life/work',
      '# Examples: charts-work.jsonl, charts-personal.jsonl, charts-health.jsonl',
      '',
      '## Context Usage:',
      '# Default/Master: charts.jsonl (no context specified)',
      '# Work context: charts-work.jsonl (context: "work")', 
      '# Personal context: charts-personal.jsonl (context: "personal")',
      '# Health context: charts-health.jsonl (context: "health")',
      '# Learning context: charts-learning.jsonl (context: "learning")',
      '',
      '## Template Patterns:',
      '# Focus on what you want to CREATE (not solve or fix)',
      '# Action steps ARE structural tension charts (can be telescoped)',
      '# Current reality must be factual, not "ready to begin"'
    ].join('\n');
    
    await fs.writeFile(templatePath, templateContent);

    const structure = {
      location: coaiaDir,
      files: {
        'charts.jsonl': 'Master/default chart database',
        'charts-work.jsonl': 'Work-related structural tension charts',
        'charts-personal.jsonl': 'Personal goals and projects', 
        'charts-learning.jsonl': 'Learning and skill development charts',
        'templates/common-goals.txt': 'Usage patterns and methodology guidance'
      }
    };

    return {
      message: `✅ COAIA project initialized at ${coaiaDir}. Multiple chart contexts available (default, work, personal, learning). Create additional contexts as needed.`,
      structure
    };
  }

  async listCoaiaProjects(): Promise<{ current_project?: string; coaia_contexts?: any; global_charts: number; project_contexts?: any; configured_path?: string; message?: string }> {
    const result: any = {
      global_charts: 0,
      project_contexts: undefined
    };

    // Show configured memory path if set
    if (memoryPath) {
      result.configured_path = memoryPath;
      result.message = `Using configured memory path: ${memoryPath}`;
    }

    // Check charts in configured/detected COAIA directory
    const coaiaDir = memoryPath ?
      (memoryPath.endsWith('/') ? memoryPath : (memoryPath.endsWith('.jsonl') ? path.dirname(memoryPath) : memoryPath)) :
      (() => {
        const projectRoot = findProjectRoot();
        return projectRoot ? path.join(projectRoot, '.coaia') : null;
      })();

    if (coaiaDir && existsSync(coaiaDir)) {
      result.current_project = coaiaDir;

      // Find all chart files in COAIA directory
      try {
        const files = await fs.readdir(coaiaDir);
        const chartFiles = files.filter(file => file.endsWith('.jsonl') && file.startsWith('charts'));

        const contexts: any = {};
        let totalProjectCharts = 0;

        for (const file of chartFiles) {
          const filePath = path.join(coaiaDir, file);
          const contextName = file === 'charts.jsonl' ? 'default' : file.replace('charts-', '').replace('.jsonl', '');

          try {
            const content = await fs.readFile(filePath, 'utf-8');
            const lines = content.split('\n').filter(line => line.trim() && !line.startsWith('#'));
            const chartCount = lines.filter(line => {
              try {
                const item = JSON.parse(line);
                return item.type === 'entity' && item.entityType === 'structural_tension_chart';
              } catch {
                return false;
              }
            }).length;

            contexts[contextName] = {
              file: file,
              path: filePath,
              charts: chartCount
            };
            totalProjectCharts += chartCount;
          } catch {
            // File not readable, skip
            contexts[contextName] = {
              file: file,
              path: filePath,
              charts: 0
            };
          }
        }

        result.project_contexts = contexts;
        result.total_project_charts = totalProjectCharts;
        result.coaia_structure = {
          directory: coaiaDir,
          available_contexts: Object.keys(contexts).sort(),
          templates: path.join(coaiaDir, 'templates')
        };
      } catch {
        // Directory not readable
        result.project_contexts = {};
      }
    }

    return result;
  }

  // Context-aware structural tension chart methods
  async createStructuralTensionChartInContext(
    desiredOutcome: string,
    currentReality: string,
    dueDate: string,
    context?: string,
    actionSteps?: string[]
  ): Promise<{ chartId: string; entities: Entity[]; relations: Relation[]; context: string }> {
    // Use the existing validation logic
    const problemSolvingWords = ['fix', 'solve', 'eliminate', 'prevent', 'stop', 'avoid', 'reduce', 'remove'];
    const detectedProblemWords = problemSolvingWords.filter(word =>
      desiredOutcome.toLowerCase().includes(word)
    );

    if (detectedProblemWords.length > 0) {
      throw new Error(`🌊 CREATIVE ORIENTATION REQUIRED

Desired Outcome: "${desiredOutcome}"

❌ **Problem**: Contains problem-solving language: "${detectedProblemWords.join(', ')}"
📚 **Principle**: Structural Tension Charts use creative orientation - focus on what you want to CREATE, not what you want to eliminate.

🎯 **Reframe Your Outcome**:
Instead of elimination → Creation focus

✅ **Examples**:
- Instead of: "Fix communication problems"
- Use: "Establish clear, effective communication practices"

**Why This Matters**: Problem-solving creates oscillating patterns. Creative orientation creates advancing patterns toward desired outcomes.`);
    }

    // Create chart using COAIA context system
    const graph = await this.loadCoaiaGraph(context);
    const chartId = `chart_${Date.now()}`;
    
    // Create chart entities
    const entities: Entity[] = [
      {
        name: `${chartId}_chart`,
        entityType: 'structural_tension_chart',
        observations: [`Chart created on ${new Date().toISOString()}`],
        metadata: {
          chartId,
          dueDate,
          level: 0,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          context: context || 'default'
        }
      },
      {
        name: `${chartId}_desired_outcome`,
        entityType: 'desired_outcome', 
        observations: [desiredOutcome],
        metadata: {
          chartId,
          dueDate,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
      },
      {
        name: `${chartId}_current_reality`,
        entityType: 'current_reality',
        observations: [currentReality],
        metadata: {
          chartId,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
      }
    ];

    // Add action steps if provided
    if (actionSteps && actionSteps.length > 0) {
      actionSteps.forEach((step, index) => {
        entities.push({
          name: `${chartId}_action_${index + 1}`,
          entityType: 'action_step',
          observations: [step],
          metadata: {
            chartId,
            dueDate,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          }
        });
      });
    }

    // Create relations
    const relations: Relation[] = [
      {
        from: `${chartId}_current_reality`,
        to: `${chartId}_desired_outcome`,
        relationType: 'creates_tension_with'
      }
    ];

    // Add action step relations
    if (actionSteps && actionSteps.length > 0) {
      actionSteps.forEach((_, index) => {
        relations.push({
          from: `${chartId}_action_${index + 1}`,
          to: `${chartId}_desired_outcome`,
          relationType: 'advances_toward'
        });
      });
    }

    // Add to graph and save
    graph.entities.push(...entities);
    graph.relations.push(...relations);
    await this.saveCoaiaGraph(graph, context);

    return { 
      chartId, 
      entities, 
      relations,
      context: context || 'default'
    };
  }

  async listChartsInContext(context?: string): Promise<any[]> {
    const graph = await this.loadCoaiaGraph(context);
    const charts = graph.entities.filter(e => e.entityType === 'structural_tension_chart');
    
    return charts.map(chart => {
      const chartId = chart.metadata?.chartId;
      if (!chartId) return null;

      const desiredOutcome = graph.entities.find(e => 
        e.name === `${chartId}_desired_outcome` && e.entityType === 'desired_outcome'
      );
      const currentReality = graph.entities.find(e =>
        e.name === `${chartId}_current_reality` && e.entityType === 'current_reality'
      );
      const actionSteps = graph.entities.filter(e =>
        e.entityType === 'action_step' && e.metadata?.chartId === chartId
      );

      return {
        chartId,
        desiredOutcome: desiredOutcome?.observations[0] || 'Unknown outcome',
        currentReality: currentReality?.observations[0] || 'Unknown reality', 
        actionSteps: actionSteps.length,
        dueDate: chart.metadata?.dueDate,
        context: context || 'default',
        level: chart.metadata?.level || 0,
        createdAt: chart.metadata?.createdAt,
        updatedAt: chart.metadata?.updatedAt
      };
    }).filter(Boolean);
  }
}

const knowledgeGraphManager = new KnowledgeGraphManager();


// The server instance and tools exposed to AI models
const server = new Server(
  { name: "coaia-spiral", version: "3.0.1" },
  { capabilities: { tools: { listChanged: true } } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "create_entities",
        description: "ADVANCED: Create traditional knowledge graph entities. For structural tension charts, use create_structural_tension_chart or add_action_step instead.",
        inputSchema: {
          type: "object",
          properties: {
            entities: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  name: { type: "string", description: "The name of the entity" },
                  entityType: { type: "string", description: "The type of the entity" },
                  observations: {
                    type: "array",
                    items: { type: "string" },
                    description: "An array of observation contents associated with the entity"
                  },
                },
                required: ["name", "entityType", "observations"],
              },
            },
          },
          required: ["entities"],
        },
      },
      {
        name: "create_relations",
        description: "Create multiple new relations between entities in the knowledge graph. Relations should be in active voice",
        inputSchema: {
          type: "object",
          properties: {
            relations: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  from: { type: "string", description: "The name of the entity where the relation starts" },
                  to: { type: "string", description: "The name of the entity where the relation ends" },
                  relationType: { type: "string", description: "The type of the relation" },
                },
                required: ["from", "to", "relationType"],
              },
            },
          },
          required: ["relations"],
        },
      },
      {
        name: "add_observations",
        description: "ADVANCED: Add observations to traditional knowledge graph entities. For structural tension charts, use update_current_reality instead.",
        inputSchema: {
          type: "object",
          properties: {
            observations: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  entityName: { type: "string", description: "The name of the entity to add the observations to" },
                  contents: {
                    type: "array",
                    items: { type: "string" },
                    description: "An array of observation contents to add"
                  },
                },
                required: ["entityName", "contents"],
              },
            },
          },
          required: ["observations"],
        },
      },
      {
        name: "delete_entities",
        description: "Delete multiple entities and their associated relations from the knowledge graph",
        inputSchema: {
          type: "object",
          properties: {
            entityNames: {
              type: "array",
              items: { type: "string" },
              description: "An array of entity names to delete"
            },
          },
          required: ["entityNames"],
        },
      },
      {
        name: "delete_observations",
        description: "Delete specific observations from entities in the knowledge graph",
        inputSchema: {
          type: "object",
          properties: {
            deletions: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  entityName: { type: "string", description: "The name of the entity containing the observations" },
                  observations: {
                    type: "array",
                    items: { type: "string" },
                    description: "An array of observations to delete"
                  },
                },
                required: ["entityName", "observations"],
              },
            },
          },
          required: ["deletions"],
        },
      },
      {
        name: "delete_relations",
        description: "Delete multiple relations from the knowledge graph",
        inputSchema: {
          type: "object",
          properties: {
            relations: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  from: { type: "string", description: "The name of the entity where the relation starts" },
                  to: { type: "string", description: "The name of the entity where the relation ends" },
                  relationType: { type: "string", description: "The type of the relation" },
                },
                required: ["from", "to", "relationType"],
              },
              description: "An array of relations to delete"
            },
          },
          required: ["relations"],
        },
      },
      {
        name: "read_graph",
        description: "RARELY USED: Dumps entire knowledge graph (all entities and relations). Only use for debugging or when you need to see ALL data. For chart work, use list_active_charts instead.",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "search_nodes",
        description: "Search for nodes in the knowledge graph based on a query",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "The search query to match against entity names, types, and observation content" },
          },
          required: ["query"],
        },
      },
      {
        name: "open_nodes",
        description: "ADVANCED: Open specific entity nodes by exact name (e.g. 'chart_123_current_reality'). Only use if you need to inspect specific chart components. NOT for general chart viewing - use list_active_charts instead.",
        inputSchema: {
          type: "object",
          properties: {
            names: {
              type: "array",
              items: { type: "string" },
              description: "An array of exact entity names to retrieve (e.g. 'chart_123_desired_outcome')",
            },
          },
          required: ["names"],
        },
      },
      {
        name: "create_structural_tension_chart", 
        description: "Create a new structural tension chart with desired outcome, current reality, and optional action steps. CRITICAL: Use creative orientation (what you want to CREATE) not problem-solving (what you want to fix/solve). Current reality must be factual assessment, never 'ready to begin'.",
        inputSchema: {
          type: "object",
          properties: {
            desiredOutcome: { type: "string", description: "What you want to CREATE (not solve/fix). Focus on positive outcomes, not problems to eliminate." },
            currentReality: { type: "string", description: "Your current situation - factual assessment only. NEVER use 'ready to begin' or similar readiness statements." },
            dueDate: { type: "string", description: "When you want to achieve this outcome (ISO date string)" },
            actionSteps: {
              type: "array",
              items: { type: "string" },
              description: "Optional list of action steps needed to achieve the outcome"
            }
          },
          required: ["desiredOutcome", "currentReality", "dueDate"]
        }
      },
      {
        name: "telescope_action_step",
        description: "Break down an action step into a detailed structural tension chart. CRITICAL: Current reality must be an honest assessment of actual current state relative to this specific action step, NOT readiness or preparation statements. This maintains structural tension essential for creative advancement.",
        inputSchema: {
          type: "object",
          properties: {
            actionStepName: { type: "string", description: "Name of the action step to telescope" },
            newCurrentReality: { 
              type: "string", 
              description: "REQUIRED: Honest assessment of actual current state relative to this action step. Examples: 'Never used Django before', 'Completed models section, struggling with views'. AVOID: 'Ready to begin', 'Prepared to start'."
            },
            initialActionSteps: {
              type: "array",
              items: { type: "string" },
              description: "Optional list of initial action steps for the telescoped chart"
            }
          },
          required: ["actionStepName", "newCurrentReality"]
        }
      },
      {
        name: "mark_action_complete",
        description: "Mark an action step as completed and update current reality",
        inputSchema: {
          type: "object",
          properties: {
            actionStepName: { type: "string", description: "Name of the completed action step" }
          },
          required: ["actionStepName"]
        }
      },
      {
        name: "get_chart_progress",
        description: "Get detailed progress for a specific chart (redundant if you just used list_active_charts which shows progress). Only use if you need the nextAction details.",
        inputSchema: {
          type: "object",
          properties: {
            chartId: { type: "string", description: "ID of the chart to check progress for" }
          },
          required: ["chartId"]
        }
      },
      {
        name: "list_active_charts",
        description: "List all active structural tension charts with their progress. Use this FIRST to see all charts and their IDs. This shows chart overview with progress - you don't need other tools after this for basic chart information.",
        inputSchema: {
          type: "object",
          properties: {}
        }
      },
      {
        name: "update_action_progress",
        description: "Update progress on an action step without marking it complete, optionally updating current reality",
        inputSchema: {
          type: "object",
          properties: {
            actionStepName: { type: "string", description: "Name of the action step to update progress for" },
            progressObservation: { type: "string", description: "Description of progress made on this action step" },
            updateCurrentReality: { 
              type: "boolean", 
              description: "Whether to also add this progress to current reality (optional, defaults to false)"
            }
          },
          required: ["actionStepName", "progressObservation"]
        }
      },
      {
        name: "update_current_reality", 
        description: "FOR STRUCTURAL TENSION CHARTS: Add observations to current reality. DO NOT use add_observations or create_entities for chart work - use this instead.",
        inputSchema: {
          type: "object",
          properties: {
            chartId: { type: "string", description: "ID of the chart to update current reality for" },
            newObservations: {
              type: "array",
              items: { type: "string" },
              description: "Array of new observations to add to current reality"
            }
          },
          required: ["chartId", "newObservations"]
        }
      },
      {
        name: "add_action_step",
        description: "Add a strategic action step to an existing structural tension chart (creates telescoped chart). WARNING: Requires honest current reality assessment - avoid 'ready to begin' language. Action steps become full structural tension charts.",
        inputSchema: {
          type: "object", 
          properties: {
            parentChartId: { type: "string", description: "ID of the parent chart to add the action step to" },
            actionStepTitle: { type: "string", description: "Title of the action step (becomes desired outcome of telescoped chart)" },
            dueDate: { 
              type: "string", 
              description: "Optional due date for the action step (ISO string). If not provided, auto-distributed between now and parent due date"
            },
            currentReality: {
              type: "string",
              description: "Current reality specific to this action step. Required to maintain structural tension - assess the actual current state relative to this action step, not readiness to begin."
            }
          },
          required: ["parentChartId", "actionStepTitle", "currentReality"]
        }
      },
      {
        name: "remove_action_step", 
        description: "Remove an action step from a structural tension chart (deletes telescoped chart)",
        inputSchema: {
          type: "object",
          properties: {
            parentChartId: { type: "string", description: "ID of the parent chart containing the action step" },
            actionStepName: { type: "string", description: "Name of the action step to remove (telescoped chart's desired outcome name)" }
          },
          required: ["parentChartId", "actionStepName"]
        }
      },
      {
        name: "update_desired_outcome",
        description: "Simple update of a chart's desired outcome (goal). Much easier than complex observation editing.",
        inputSchema: {
          type: "object",
          properties: {
            chartId: { type: "string", description: "ID of the chart to update" },
            newDesiredOutcome: { type: "string", description: "New desired outcome text" }
          },
          required: ["chartId", "newDesiredOutcome"]
        }
      },
      {
        name: "update_action_step_title",
        description: "Simple update of an action step's title. Much easier than complex observation editing.",
        inputSchema: {
          type: "object",
          properties: {
            actionStepName: { type: "string", description: "Name of the action step entity to update (e.g. 'chart_123_desired_outcome')" },
            newTitle: { type: "string", description: "New action step title" }
          },
          required: ["actionStepName", "newTitle"]
        }
      },
      {
        name: "init_llm_guidance",
        description: "🚨 NEW LLM? Essential guidance for understanding COAIA Memory's structural tension methodology, delayed resolution principle, and proper tool usage. Run this FIRST to avoid common mistakes.",
        inputSchema: {
          type: "object",
          properties: {
            format: { 
              type: "string", 
              enum: ["full", "quick", "save_directive"], 
              default: "full",
              description: "Level of detail: 'full' for complete guidance, 'quick' for essentials only, 'save_directive' for session memory instructions"
            }
          }
        }
      },

      // COAIA Project Organization Tools
      {
        name: "initialize_coaia_project",
        description: `Initialize a .coaia directory structure for flexible structural tension chart management in the current project.

Creates multiple chart contexts similar to the original AIM database approach:
- .coaia/charts.jsonl - Master/default chart database
- .coaia/charts-work.jsonl - Work-related structural tension charts
- .coaia/charts-personal.jsonl - Personal goals and projects
- .coaia/charts-learning.jsonl - Learning and skill development
- .coaia/templates/common-goals.txt - Usage patterns and methodology guidance

Users can create additional contexts as needed for different areas of life/work. This mirrors the flexible multi-database approach from the original AIM system but specifically for structural tension charts.`,
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "list_coaia_projects",
        description: `Show COAIA project status and all available chart contexts.

Displays:
- Current project detection (.coaia directory status)
- All available chart contexts (default, work, personal, learning, etc.)
- Chart counts per context
- Directory structure and file locations
- Project-specific chart organization overview

Helps you understand all available contexts and how your charts are organized across different areas of life/work.`,
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "create_chart_in_context",
        description: `Create a structural tension chart in a specific context (work, personal, health, etc.).

This provides the flexible multi-context approach similar to the original AIM system. Charts can be organized by life area, project type, or any meaningful categorization.

Contexts are created automatically - just specify any descriptive name like 'work', 'personal', 'health', 'learning', 'side-projects', etc.`,
        inputSchema: {
          type: "object",
          properties: {
            desiredOutcome: {
              type: "string",
              description: "What you want to CREATE (not solve or fix) - must be creative-oriented"
            },
            currentReality: {
              type: "string", 
              description: "Honest, factual assessment of where you are now (not 'ready to begin')"
            },
            dueDate: {
              type: "string",
              description: "Target completion date (ISO format: YYYY-MM-DD)"
            },
            context: {
              type: "string",
              description: "Optional context for organizing charts (e.g., 'work', 'personal', 'health', 'learning'). If not specified, uses default context."
            },
            actionSteps: {
              type: "array",
              items: { type: "string" },
              description: "Optional strategic action steps - each becomes a telescoped chart"
            }
          },
          required: ["desiredOutcome", "currentReality", "dueDate"]
        },
      },
      {
        name: "list_charts_in_context",
        description: `List all structural tension charts in a specific context.

Shows charts organized by context (work, personal, health, etc.) with summaries including desired outcomes, current reality, action steps count, and due dates.`,
        inputSchema: {
          type: "object",
          properties: {
            context: {
              type: "string",
              description: "Context to list charts from (e.g., 'work', 'personal', 'health'). If not specified, lists charts from default context."
            }
          }
        },
      }
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (!args) {
    throw new Error(`No arguments provided for tool: ${name}`);
  }

  switch (name) {
    case "create_entities":
      return { content: [{ type: "text", text: JSON.stringify(await knowledgeGraphManager.createEntities(args.entities as Entity[]), null, 2) }] };
    case "create_relations":
      return { content: [{ type: "text", text: JSON.stringify(await knowledgeGraphManager.createRelations(args.relations as Relation[]), null, 2) }] };
    case "add_observations":
      return { content: [{ type: "text", text: JSON.stringify(await knowledgeGraphManager.addObservations(args.observations as { entityName: string; contents: string[] }[]), null, 2) }] };
    case "delete_entities":
      await knowledgeGraphManager.deleteEntities(args.entityNames as string[]);
      return { content: [{ type: "text", text: "Entities deleted successfully" }] };
    case "delete_observations":
      await knowledgeGraphManager.deleteObservations(args.deletions as { entityName: string; observations: string[] }[]);
      return { content: [{ type: "text", text: "Observations deleted successfully" }] };
    case "delete_relations":
      await knowledgeGraphManager.deleteRelations(args.relations as Relation[]);
      return { content: [{ type: "text", text: "Relations deleted successfully" }] };
    case "read_graph":
      return { content: [{ type: "text", text: JSON.stringify(await knowledgeGraphManager.readGraph(), null, 2) }] };
    case "search_nodes":
      return { content: [{ type: "text", text: JSON.stringify(await knowledgeGraphManager.searchNodes(args.query as string), null, 2) }] };
    case "open_nodes":
      return { content: [{ type: "text", text: JSON.stringify(await knowledgeGraphManager.openNodes(args.names as string[]), null, 2) }] };
    case "create_structural_tension_chart":
      const chartResult = await knowledgeGraphManager.createStructuralTensionChart(
        args.desiredOutcome as string,
        args.currentReality as string,
        args.dueDate as string,
        args.actionSteps as string[]
      );
      return { content: [{ type: "text", text: JSON.stringify(chartResult, null, 2) }] };
    case "telescope_action_step":
      const telescopeResult = await knowledgeGraphManager.telescopeActionStep(
        args.actionStepName as string,
        args.newCurrentReality as string,
        args.initialActionSteps as string[]
      );
      return { content: [{ type: "text", text: JSON.stringify(telescopeResult, null, 2) }] };
    case "mark_action_complete":
      await knowledgeGraphManager.markActionStepComplete(args.actionStepName as string);
      return { content: [{ type: "text", text: `Action step '${args.actionStepName}' marked as complete and current reality updated` }] };
    case "get_chart_progress":
      const progressResult = await knowledgeGraphManager.getChartProgress(args.chartId as string);
      return { content: [{ type: "text", text: JSON.stringify(progressResult, null, 2) }] };
    case "list_active_charts":
      const chartsResult = await knowledgeGraphManager.listActiveCharts();
      
      // Format as hierarchical ASCII tree
      let hierarchyText = "## Structural Tension Charts Hierarchy\n\n";
      
      // Group by master charts (level 0)
      const masterCharts = chartsResult.filter(c => c.level === 0);
      const actionCharts = chartsResult.filter(c => c.level > 0);
      
      masterCharts.forEach(master => {
        const progress = master.progress > 0 ? ` (${Math.round(master.progress * 100)}% complete)` : "";
        const dueDate = master.dueDate ? ` [Due: ${new Date(master.dueDate).toLocaleDateString()}]` : "";
        
        hierarchyText += `📋 **${master.desiredOutcome}** (Master Chart)${progress}${dueDate}\n`;
        hierarchyText += `    ID: ${master.chartId}\n`;
        
        // Find action steps for this master chart
        const actions = actionCharts.filter(a => a.parentChart === master.chartId);
        
        if (actions.length > 0) {
          actions.forEach((action, index) => {
            const isLast = index === actions.length - 1;
            const connector = isLast ? "└── " : "├── ";
            const actionProgress = action.progress > 0 ? ` (${Math.round(action.progress * 100)}%)` : "";
            const actionDue = action.dueDate ? ` [${new Date(action.dueDate).toLocaleDateString()}]` : "";
            
            hierarchyText += `    ${connector}🎯 ${action.desiredOutcome} (Action Step)${actionProgress}${actionDue}\n`;
            hierarchyText += `        ID: ${action.chartId}\n`;
          });
        } else {
          hierarchyText += `    └── (No action steps yet)\n`;
        }
        hierarchyText += "\n";
      });
      
      if (masterCharts.length === 0) {
        hierarchyText += "No active structural tension charts found.\n\n";
        hierarchyText += "💡 Create your first chart with: create_structural_tension_chart\n";
      }
      
      return { content: [{ type: "text", text: hierarchyText }] };
    case "update_action_progress":
      await knowledgeGraphManager.updateActionProgress(
        args.actionStepName as string,
        args.progressObservation as string,
        args.updateCurrentReality as boolean
      );
      return { content: [{ type: "text", text: `Action step '${args.actionStepName}' progress updated` }] };
    case "update_current_reality":
      await knowledgeGraphManager.updateCurrentReality(
        args.chartId as string,
        args.newObservations as string[]
      );
      return { content: [{ type: "text", text: `Current reality updated for chart '${args.chartId}'` }] };
    case "add_action_step":
      const addActionResult = await knowledgeGraphManager.addActionStep(
        args.parentChartId as string,
        args.actionStepTitle as string,
        args.dueDate as string,
        args.currentReality as string
      );
      return { content: [{ type: "text", text: `Action step '${args.actionStepTitle}' added to chart '${args.parentChartId}' as telescoped chart '${addActionResult.chartId}'` }] };
    case "remove_action_step":
      await knowledgeGraphManager.removeActionStep(
        args.parentChartId as string,
        args.actionStepName as string
      );
      return { content: [{ type: "text", text: `Action step '${args.actionStepName}' removed from chart '${args.parentChartId}'` }] };
    case "update_desired_outcome":
      await knowledgeGraphManager.updateDesiredOutcome(
        args.chartId as string,
        args.newDesiredOutcome as string
      );
      return { content: [{ type: "text", text: `Desired outcome updated for chart '${args.chartId}'` }] };
    case "update_action_step_title":
      await knowledgeGraphManager.updateActionStepTitle(
        args.actionStepName as string,
        args.newTitle as string
      );
      return { content: [{ type: "text", text: `Action step title updated for '${args.actionStepName}'` }] };
    case "init_llm_guidance":
      const format = args.format as string || "full";
      
      if (format === "save_directive") {
        return { content: [{ type: "text", text: `## 💡 RECOMMENDED: Save This Guidance

**Claude Code**: Add this guidance to CLAUDE.md in your project directory
**Gemini**: Save as GEMINI.md in your workspace  
**Other Agents**: Create AGENTS.md or similar session memory file

This ensures you remember COAIA Memory's structural tension principles across our entire conversation.

**Quick Command**: Use format="full" to get the complete guidance content to save.` }] };
      }
      
      if (format === "quick") {
        return { content: [{ type: "text", text: `## 🚨 COAIA Memory Quick Reference

**CRITICAL**: "Ready to begin" = WRONG. Current reality must be factual assessment.

**Core Tools**:
1. \`list_active_charts\` → Start here, see all charts
2. \`create_structural_tension_chart\` → New chart (outcome + reality + actions)
3. \`add_action_step\` → Add strategic actions (creates telescoped chart)
4. \`telescope_action_step\` → Break down actions into detailed sub-charts

**Common Mistakes**:
❌ "Ready to begin Django tutorial" 
✅ "Never used Django, completed Python basics"

Use format="full" for complete guidance.` }] };
      }
      
      // Default: full guidance
      return { content: [{ type: "text", text: LLM_GUIDANCE }] };

    // COAIA Project Organization Handlers
    case "initialize_coaia_project":
      const initResult = await knowledgeGraphManager.initializeCoaiaProject();
      return { content: [{ type: "text", text: JSON.stringify(initResult, null, 2) }] };
    case "list_coaia_projects":
      const projectsResult = await knowledgeGraphManager.listCoaiaProjects();
      return { content: [{ type: "text", text: JSON.stringify(projectsResult, null, 2) }] };
    case "create_chart_in_context":
      const contextChartResult = await knowledgeGraphManager.createStructuralTensionChartInContext(
        args.desiredOutcome as string,
        args.currentReality as string,
        args.dueDate as string,
        args.context as string,
        args.actionSteps as string[]
      );
      return { content: [{ type: "text", text: JSON.stringify(contextChartResult, null, 2) }] };
    case "list_charts_in_context":
      const contextChartsResult = await knowledgeGraphManager.listChartsInContext(args.context as string);
      return { content: [{ type: "text", text: JSON.stringify(contextChartsResult, null, 2) }] };

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("COAIA Memory - Creative Oriented AI Assistant Memory Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
