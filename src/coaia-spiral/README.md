# COAIA Spiral - Creative-Oriented AI Assistant Memory System

> MCP server implementing structural tension charts and advancing spiral patterns based on Robert Fritz's creative methodology

## What is COAIA Spiral?

COAIA Spiral extends traditional knowledge graphs with **structural tension charts** - a powerful framework for organizing creative processes around desired outcomes rather than problem-solving. Based on Robert Fritz's structural tension methodology, it helps AI assistants maintain creative orientation and support advancing spiral patterns.

**Current Version**: v2.4.0 (COAIA Project Organization) - **Now includes .coaia directory support for organized structural tension chart management**

## Key Features

### 🎯 Structural Tension Charts
- **Desired Outcomes**: Clear, specific results you want to create
- **Current Reality**: Honest assessment of where you are now  
- **Structural Tension**: The unresolved tension between current reality and desired outcome that naturally seeks resolution
- **Action Steps**: Strategic secondary actions - intermediary end results that advance toward the primary goal
- **Due Dates**: Time organization that creates momentum

### 🔭 Telescoping Support
- Break down complex action steps into detailed sub-charts
- Proper due date inheritance from parent steps
- Hierarchical navigation between overview and details
- Maintains structural tension at every level

### 📈 Advancing Pattern Tracking
- Completed action steps become part of current reality, changing the structural dynamic
- Each completion advances the system toward equilibrium (desired outcome)
- Success creates new structural tension for continued advancement
- Prevents oscillating patterns through proper structural design

### 🗣️ Natural Language Ready
- Conversational patterns documented for intuitive interaction
- Creative-oriented language (focus on creation vs problem-solving)
- AI assistants can guide users through structural tension exercises

### 🔗 Traditional Knowledge Graph
- Full entity, relation, and observation management
- Search and retrieval capabilities
- Compatible with existing MCP knowledge graph workflows

## 🏗️ COAIA Project Organization

**NEW in v2.4.0**: Project-specific structural tension chart organization with `.coaia` directories:

### Why .coaia Directories?
Unlike generic memory storage, COAIA focuses specifically on **structural tension charts** and creative goal achievement:

- **`.coaia` directories**: Organize structural tension charts within projects
- **Chart lifecycle management**: Separate active charts from completed learning examples
- **Template patterns**: Reusable structural tension patterns for common goals
- **Project-specific creativity**: Each project can have its own creative goals and patterns

### Chart Organization Structure
```
my-project/
├── .coaia/
│   ├── active-charts.jsonl      # Current structural tension charts
│   ├── completed-charts.jsonl   # Successfully achieved charts (learning examples)
│   └── templates/
│       └── common-goals.jsonl   # Reusable patterns for desired outcomes
└── src/
```

### Benefits of COAIA Organization
- **Focus on Creation**: Specifically designed for structural tension methodology, not generic data storage
- **Learning from Success**: Completed charts become templates for future goal achievement
- **Project Context**: Charts organized within the projects where they're relevant
- **Pattern Recognition**: Build libraries of successful creative patterns

## Installation & Usage

### As NPX Package
```bash
npx coaia-spiral --memory-path ./my-charts.jsonl
```

### In Claude Desktop Config
```json
{
  "mcpServers": {
    "coaia-spiral": {
      "command": "npx",
      "args": ["-y", "coaia-spiral", "--memory-path", "/path/to/your/charts.jsonl"],
      "autoapprove": [
        "create_structural_tension_chart",
        "telescope_action_step", 
        "mark_action_complete",
        "get_chart_progress",
        "list_active_charts",
        "initialize_coaia_project",
        "list_coaia_projects", 
        "move_chart_to_completed",
        "create_entities",
        "create_relations",
        "add_observations"
      ]
    }
  }
}
```

### Local Development
```bash
git clone <repository>
cd coaia-spiral
npm install
npm run build
```

### Project-Local Chart Organization

In any project, initialize COAIA organization:

1. **Ensure project markers exist** (`.git`, `package.json`, etc.)
2. **Use AI assistant to run**: `initialize_coaia_project`
3. **Start creating charts**: Charts will be organized in `.coaia/active-charts.jsonl`
4. **Archive completed charts**: Use `move_chart_to_completed` to preserve successful patterns

Benefits:
- Charts organized by project context
- Completed charts become learning templates
- Separate active work from archived successes
- Project-specific creative goal management

## Core Tools

### Structural Tension Chart Management (COAIA)
- `create_structural_tension_chart` - Create new chart with outcome, reality, and action steps
- `telescope_action_step` - Break down action steps into detailed sub-charts
- `mark_action_complete` - Complete actions and update current reality
- `get_chart_progress` - Monitor chart advancement
- `list_active_charts` - Overview of all active charts

### COAIA Project Organization (NEW)
- `initialize_coaia_project` - Set up .coaia directory structure for organized charts
- `list_coaia_projects` - Show project status and chart organization
- `move_chart_to_completed` - Archive completed charts as learning examples

### Traditional Knowledge Graph Operations
- `create_entities` - Add new entities (people, concepts, events)
- `create_relations` - Connect entities with relationships
- `add_observations` - Record new information about entities
- Plus full CRUD operations for entities, relations, and observations

## Example Usage

### Creating a Chart
```javascript
// Natural language: "I want to learn Python web development in 6 weeks"
{
  "desiredOutcome": "Learn Python web development", 
  "currentReality": "I know basic Python but no web frameworks",
  "dueDate": "2025-09-15T00:00:00Z",
  "actionSteps": [
    "Complete Django tutorial",
    "Build practice project", 
    "Deploy something live"
  ]
}
```

### Telescoping Detail
```javascript
// Natural language: "Break down the Django tutorial step"
{
  "actionStepName": "chart_123_action_1",
  "newCurrentReality": "Never used Django, familiar with Python basics"
}
```

### Tracking Progress
```javascript
// Natural language: "I finished the Django tutorial"
{
  "actionStepName": "chart_123_action_1"
}
```

## Creative Orientation Principles

### Focus on Creation, Not Problem-Solving
- **Use**: "I want to create...", "My desired outcome is..."
- **Avoid**: "I need to fix...", "The problem is...", "I want to stop..."

### Structural Tension Awareness  
- Always pair desired outcomes with current reality to create structural tension
- This unresolved tension naturally seeks resolution through advancement
- Action steps are strategic intermediary results that change the structural dynamic
- Completed actions flow into current reality, creating new tension for continued advancement

### Advancing Patterns
- Success builds on success
- Completed actions become part of current reality
- Momentum creates natural progression toward goals

## Development & Testing

### Build & Test
```bash
npm install
npm run build
```

### Test Environment
```bash
cd test-environment
claude-code  # Launch with pre-configured MCP setup
```

## Release Status

### ✅ Validated in v2.0.0-rc.1
- **Core Structural Tension Charts**: Fully functional with proper entity relationships
- **Telescoping Support**: Action steps break down into sub-charts with due date inheritance
- **Advancing Pattern Tracking**: Completions flow into current reality, system advances naturally
- **MCP Integration**: All tools working correctly in Claude Code CLI environment
- **Real-World Testing**: Validated with actual user interactions in test environment

### Next Milestone
**Guided Chart Creation**: Transform from passive storage to active coaching system that helps users create meaningful structural tension charts with proper creative orientation validation.

## Architecture

### Enhanced Entity Types
- `structural_tension_chart` - Container for chart components
- `desired_outcome` - What you want to create
- `current_reality` - Where you are now  
- `action_step` - Strategic actions with due dates

### Creative Relations
- `creates_tension_with` - Between current reality and desired outcome
- `advances_toward` - Action steps advancing toward outcomes
- `telescopes_into` - Hierarchical chart relationships
- `flows_into` - Completed actions updating reality

### Metadata Support
- Due dates and completion tracking
- Chart hierarchy and telescoping relationships
- Creative phases (germination, assimilation, completion)
- Timestamps and progress metrics

## Credits

- **Author**: J.Guillaume D.-Isabelle <jgi@jgwill.com> (https://github.com/jgwill)
- **Methodology**: Robert Fritz - Structural Tension (https://robertfritz.com)  
- **Foundation**: Shane Holloman - Original MCP Knowledge Graph
- **License**: MIT

## Philosophy

COAIA Spiral embodies the principle that **structure determines behavior**. By organizing memory around structural tension rather than problem-solving patterns, it naturally supports creative advancement and helps users build the life they want to create.

The system recognizes that structural tension is the fundamental organizing principle of the creative process - not a problem to be solved, but a generative force to be harnessed.