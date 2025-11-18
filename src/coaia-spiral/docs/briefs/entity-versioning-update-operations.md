# Technical Brief: Entity Versioning and Update Operations

## Overview

This document outlines the technical implementation plan for adding version tracking and update capabilities to the MCP Knowledge Graph server. These features will enable tracking the history and evolution of knowledge entities and relations, as well as provide tools to update existing graph elements.

## Background

Currently, the MCP Knowledge Graph server allows creating entities and relations but lacks the ability to track their history or update them after creation. This makes it difficult to understand how knowledge evolves over time or to correct/update existing information.

## User Personas

1. **Knowledge Administrators**: Need to maintain and update knowledge bases with accurate information
2. **History Trackers**: Want to understand how knowledge has evolved over time
3. **Integration Developers**: Need to update existing entities and relations through API calls

## Implementation Details

### 1. Version Tracking System

We will enhance entity and relation objects to include version information:

```typescript
interface Entity {
  name: string;
  entityType: string;
  observations: string[];
  createdAt: string;  // ISO timestamp of creation/update
  version: number;    // Incremented with each update
}

interface Relation {
  from: string;
  to: string;
  relationType: string;
  createdAt: string;  // ISO timestamp of creation/update
  version: number;    // Incremented with each update
}
```

### 2. Entity and Relation Update Operations

We'll implement methods to update existing entities and relations:

```typescript
async updateEntities(entities: Entity[]): Promise<Entity[]> {
  const graph = await this.loadGraph();
  const updatedEntities = entities.map(updateEntity => {
    const existingEntity = graph.entities.find(e => e.name === updateEntity.name);
    if (!existingEntity) {
      throw new Error(`Entity with name ${updateEntity.name} not found`);
    }
    return {
      ...existingEntity,
      ...updateEntity,
      version: existingEntity.version + 1,
      createdAt: new Date().toISOString()
    };
  });

  // Update entities in the graph
  updatedEntities.forEach(updatedEntity => {
    const index = graph.entities.findIndex(e => e.name === updatedEntity.name);
    if (index !== -1) {
      graph.entities[index] = updatedEntity;
    }
  });

  await this.saveGraph(graph);
  return updatedEntities;
}

async updateRelations(relations: Relation[]): Promise<Relation[]> {
  const graph = await this.loadGraph();
  const updatedRelations = relations.map(updateRelation => {
    const existingRelation = graph.relations.find(r =>
      r.from === updateRelation.from &&
      r.to === updateRelation.to &&
      r.relationType === updateRelation.relationType
    );
    if (!existingRelation) {
      throw new Error(`Relation not found`);
    }
    return {
      ...existingRelation,
      ...updateRelation,
      version: existingRelation.version + 1,
      createdAt: new Date().toISOString()
    };
  });

  // Update relations in the graph
  updatedRelations.forEach(updatedRelation => {
    const index = graph.relations.findIndex(r =>
      r.from === updatedRelation.from &&
      r.to === updatedRelation.to &&
      r.relationType === updatedRelation.relationType
    );
    if (index !== -1) {
      graph.relations[index] = updatedRelation;
    }
  });

  await this.saveGraph(graph);
  return updatedRelations;
}
```

### 3. New Tools for Entity and Relation Management

We'll add these tools to manage knowledge graph elements:

- `update_entities`: Update multiple existing entities in the knowledge graph
- `update_relations`: Update multiple existing relations in the knowledge graph

These tools will be exposed through the MCP server interface:

```typescript
{
  name: "update_entities",
  description: "Update multiple existing entities in the knowledge graph",
  inputSchema: {
    type: "object",
    properties: {
      entities: {
        type: "array",
        items: {
          type: "object",
          properties: {
            name: { type: "string", description: "The name of the entity to update" },
            entityType: { type: "string", description: "The updated type of the entity" },
            observations: {
              type: "array",
              items: { type: "string" },
              description: "The updated array of observation contents"
            },
          },
          required: ["name"],
        },
      },
    },
    required: ["entities"],
  },
}
```

### 4. Environment Variable Support

To improve configuration flexibility, we'll add environment variable support:

```typescript
// Check for memory path in command line args or environment variable
let memoryPath = argv['memory-path'] || process.env.MEMORY_FILE_PATH;
```

### 5. Dockerization Support

We'll add a Dockerfile to enable easy containerized deployment:

```dockerfile
FROM node:lts-alpine

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --ignore-scripts

# Copy the rest of the code
COPY . .

# Build the project
RUN npm run build

# Run the MCP server
CMD [ "node", "dist/index.js" ]
```

## User Experience Improvements

1. **Version Information**: Include version and timestamp information in API responses
2. **Update Validation**: Verify entities exist before allowing updates
3. **Documentation**: Clear examples for updating entities and relations

## Safety Mechanisms

1. **Version Incrementing**: Automatically track version numbers to prevent overwriting
2. **Error Handling**: Clear error messages when entities or relations don't exist
3. **Field Preservation**: Preserve existing fields not explicitly updated

## Implementation Plan

1. **Phase 1: Core Version Tracking**
   - Update Entity and Relation interfaces
   - Modify creation operations to initialize version fields
   - Add updateEntities and updateRelations methods

2. **Phase 2: Tool Interface**
   - Implement update_entities and update_relations tools
   - Update server registration and tool handling

3. **Phase 3: Configuration Enhancements**
   - Add environment variable support
   - Improve documentation and configuration examples

4. **Phase 4: Deployment Improvements**
   - Add Dockerfile
   - Create deployment documentation

5. **Phase 5: Testing & Documentation**
   - Comprehensive testing across different scenarios
   - Update README with version tracking examples

## Benefits

1. **Knowledge Evolution**: Track how knowledge changes over time
2. **Error Correction**: Easily fix mistakes in the knowledge graph
3. **Audit Trail**: Understand when and how often knowledge elements change
4. **Deployment Flexibility**: Run as container or local process with configurable options
5. **Integration Simplicity**: Update APIs make it easier to maintain knowledge programmatically
