# Changelog

All notable changes to COAIA Memory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2025-08-31

### 🚀 LLM-Intelligent Enhancement

**Key Features**:
- 🌊 Comprehensive LLM Guidance System
  - Build-time consolidated methodology documentation
  - `init_llm_guidance` tool with multiple formats (full, quick, save_directive)
  - Intelligent error handling with educational responses

- 🧠 Enhanced AI Interaction
  - Creative orientation validation
  - Delayed resolution principle enforcement
  - Problem-solving language detection
  - Comprehensive teaching messages with Robert Fritz's principles

- 📘 Documentation Improvements
  - Methodology warnings in tool descriptions
  - Intelligent error messages guiding LLMs
  - Self-documenting MCP server

### Technical Enhancements
- Updated server description to highlight LLM guidance
- Improved validation with educational error responses
- Added context extraction for current reality assessment

## [2.2.8] - 2025-08-29

### 🐛 Bug Fixes

- Resolved TypeScript type issue in `telescopeActionStepWithContext` method
- Added null coalescing to ensure proper type handling when extracting current reality from context

## [2.2.3] - 2025-08-25

### ✨ Enhancements

- **Progress-Based Reality Updates (v2.1.0 Enhancement)**
  - Added `update_action_progress` tool: Allows tracking progress on an action step without marking it complete, optionally updating current reality.
  - Added `update_current_reality` tool: Enables adding external observations directly to a chart's current reality.
  - Enhanced philosophical alignment: Supports "journey-aware" tracking, recognizing that reality changes throughout the creative process, not just upon completion.

- **Expanded Chart Management Tools**
  - Added `add_action_step` tool: Allows adding a strategic action step to an existing chart, which automatically creates a telescoped chart.
  - Added `remove_action_step` tool: Enables removal of an action step (and its associated telescoped chart).
  - Added `update_desired_outcome` tool: Provides a simple way to modify a chart's main goal.
  - Added `update_action_step_title` tool: Allows simple modification of an action step's title.

- **Improved User Experience**
  - The `list_active_charts` tool now provides a clear, hierarchical ASCII tree view of all active charts, enhancing navigation and overview.
  - Updated tool descriptions for traditional knowledge graph operations (`create_entities`, `add_observations`, `read_graph`, `open_nodes`) to guide users towards the new, more appropriate structural tension chart tools.

### 🐛 Bug Fixes

- Minor internal adjustments for version consistency and build stability.

## [2.0.0-rc.1] - 2025-08-14

### 🎯 Major Release Candidate - Structural Tension Charts

This release candidate represents a complete evolution from traditional knowledge graphs to creative-oriented memory systems based on Robert Fritz's structural tension methodology.

#### Added
- **Structural Tension Chart Architecture**
  - `structural_tension_chart` entity type for organizing creative processes
  - `desired_outcome` entities for clear, specific end results
  - `current_reality` entities for honest assessment of current state
  - `action_step` entities for strategic secondary actions with due dates
  - Automatic due date distribution between current time and chart deadline

- **Core Chart Management Tools**
  - `create_structural_tension_chart` - Create charts with outcome, reality, and action steps
  - `get_chart_progress` - Monitor advancement with completion percentages and next actions
  - `list_active_charts` - Overview of all charts sorted by level and due date
  - `mark_action_complete` - Complete actions with automatic current reality updates

- **Telescoping Functionality**
  - `telescope_action_step` - Break down action steps into detailed sub-charts
  - Proper due date inheritance from parent action steps
  - Hierarchical chart levels with parent-child relationship tracking
  - Maintains structural tension at every telescoping level

- **Advancing Pattern Support**
  - Completed actions automatically flow into current reality
  - Each completion changes structural dynamic and advances system toward desired outcome
  - Success builds momentum for continued advancement
  - Prevention of oscillating patterns through proper structural design

- **Enhanced Metadata System**
  - Due dates, completion status, and timestamps for all entities
  - Chart hierarchy tracking with parent chart and action step references
  - Creative phase support (germination, assimilation, completion)
  - Level tracking for telescoped chart organization

- **Creative Relations Framework**
  - `creates_tension_with` - Fundamental structural tension between reality and outcome
  - `advances_toward` - Action steps that advance system toward desired outcome
  - `telescopes_into` - Hierarchical chart relationships
  - `flows_into` - Completed actions updating current reality
  - `contains` - Chart container relationships

#### Enhanced
- **Knowledge Graph Foundation**
  - Extended existing entity/relation/observation architecture
  - Maintained full backward compatibility with traditional knowledge graph operations
  - Added metadata support to base Entity and Relation interfaces
  - Preserved all existing MCP tool functionality

- **Natural Language Interface**
  - Creative-oriented language patterns documented for AI assistant interaction
  - Conversation flow examples for chart creation, telescoping, and progress tracking
  - Anti-pattern language detection guidelines (avoiding problem-solving bias)
  - Educational guidance frameworks for teaching structural tension principles

#### Technical Improvements
- **TypeScript Implementation**
  - Strongly typed interfaces for all structural tension components
  - Compile-time validation of chart structure integrity
  - Enhanced error handling for chart operations
  - Modular architecture supporting extensibility

- **MCP Server Architecture**
  - Updated server name from "mcp-knowledge-graph" to "coaia-memory"
  - Version bump to 2.0.0 reflecting major functionality addition
  - All tools exposed through standard MCP interface
  - Maintained compatibility with Claude Code CLI and other MCP clients

- **Data Persistence**
  - JSONL format preservation for knowledge graph data
  - Atomic operations for chart creation and updates
  - Transactional integrity for telescoping operations
  - Efficient storage of hierarchical chart relationships

#### Documentation
- **Comprehensive Usage Examples**
  - Natural language interaction patterns for each tool
  - Chart creation scenarios with realistic desired outcomes
  - Telescoping examples showing due date inheritance
  - Progress tracking demonstrations

- **Creative Orientation Guidelines**
  - Focus on creation vs problem-solving language
  - Structural tension awareness principles
  - Advancing pattern recognition techniques
  - Anti-pattern detection and correction guidance

#### Testing & Validation
- **Test Environment Setup**
  - Pre-configured MCP client setup for easy testing
  - Sample structural tension charts with realistic data
  - Complete testing scenarios and usage instructions
  - Validation of core functionality with real user interactions

- **Real-World Validation**
  - Guitar learning chart creation and telescoping
  - Action completion tracking and reality updates
  - Cross-chart relationship management
  - Knowledge graph integration alongside structural tension charts

#### Changed
- **Package Identity**
  - Name: `mcp-knowledge-graph-mia` → `coaia-memory`
  - Description: Enhanced to reflect structural tension chart capabilities
  - Version: 1.0.3 → 2.0.0-rc.1
  - Author: Updated to J.Guillaume D.-Isabelle with Shane Holloman as contributor
  - Added Robert Fritz methodology attribution

- **Server Configuration**
  - Server name: "mcp-knowledge-graph" → "coaia-memory"
  - Updated console output to reflect creative orientation
  - Enhanced error messages with structural tension awareness

#### Removed
- None - Full backward compatibility maintained

### 🔧 Technical Details

#### Dependencies
- Maintained existing MCP SDK dependencies
- No breaking changes to existing API surface
- TypeScript configuration optimized for ES2020 target

#### Breaking Changes
- None for existing knowledge graph operations
- New tools added without affecting existing functionality
- Configuration changes only affect server name and version

#### Migration Guide
- Existing knowledge graph data fully compatible
- Update MCP server name in configuration: `mcp-knowledge-graph` → `coaia-memory`
- Add new structural tension tools to autoapprove list if desired
- No data migration required

### 🎉 Release Candidate Status

This RC demonstrates complete structural tension chart functionality validated through real-world testing. The system successfully:
- Creates meaningful structural tension charts
- Performs telescoping with proper due date inheritance  
- Tracks progress with automatic current reality updates
- Maintains advancing patterns through completion cycles
- Integrates seamlessly with traditional knowledge graph operations

**Ready for broader testing and feedback collection.**

**Next Milestone**: Guided chart creation system with quality validation and anti-pattern detection.

---

## [1.0.3] - 2025-08-08 (Pre-COAIA)

### Previous Version Notes
- Original MCP knowledge graph implementation by Shane Holloman
- Basic entity, relation, and observation management
- Standard MCP tool interface
- JSONL data persistence

*This version served as the foundation for COAIA Memory development.*