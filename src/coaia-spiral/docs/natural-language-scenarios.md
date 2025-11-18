# Natural Language Interface Scenarios for Creative-Oriented MCP Knowledge Graph

> Documentation of conversational patterns for interacting with structural tension charts and creative memory systems through natural language.

This document outlines the key conversational scenarios and language patterns needed to interact naturally with a creative-oriented memory system based on structural tension principles.

## Core Conversational Scenarios

### 1. Creating a New Structural Tension Chart

**Natural Language Input:**
```
"I want to create a new goal to learn Python web development in 6 weeks"
"I need to build a mobile app by March 15th"
"My desired outcome is to establish a morning creative routine within 30 days"
```

**System Processing:**
- Create `desired_outcome` entity with specific description
- Set due date based on timeframe mentioned
- Prompt for current reality assessment
- Create new `structural_tension_chart` entity linking them
- Generate unique chart ID for tracking

**Response Pattern:**
```
"I've created your desired outcome: 'Learn Python web development' with a due date of [calculated date]. 
What's your current reality regarding Python web development?"
```

### 2. Assessing Current Reality

**Natural Language Input:**
```
"My current reality is I know basic Python but no web frameworks"
"Right now I have zero experience with mobile development"
"Currently I don't have any consistent morning routine"
```

**System Processing:**
- Create `current_reality` entity with detailed observations
- Link to corresponding desired outcome via `creates_tension_with` relation
- System recognizes structural tension is now established
- Enable action step planning phase

**Response Pattern:**
```
"Current reality captured: 'Basic Python knowledge, no web frameworks'. 
Structural tension is now established between where you are and where you want to be.
What action steps do you think you'll need to take?"
```

### 3. Adding Action Steps

**Natural Language Input:**
```
"I need to complete a Django tutorial, build a practice project, and deploy something live"
"My steps are: research frameworks, choose one, build a simple app, test on devices, publish to app store"
"I want to: set up a morning space, choose creative activities, start with 15 minutes daily, gradually expand"
```

**System Processing:**
- Parse multiple action steps from natural language
- Create individual `action_step` entities for each
- Automatically distribute due dates between now and final goal
- Link each step with `advances_toward` relations to desired outcome
- Organize chronologically

**Response Pattern:**
```
"I've created 3 action steps with due dates:
1. Complete Django tutorial (due: [date])
2. Build practice project (due: [date]) 
3. Deploy something live (due: [date])

Need more detail on any of these steps?"
```

### 4. Telescoping Into Detail

**Natural Language Input:**
```
"I want to break down the Django tutorial step into more detail"
"Can we expand the 'build practice project' step?"
"Let's telescope into the morning routine setup"
```

**System Processing:**
- Convert specified action step into new desired outcome
- Create telescoped chart with inherited due date from parent action step
- Prompt for current reality assessment specific to this sub-goal
- Maintain parent-child relationship for navigation

**Response Pattern:**
```
"Creating detailed chart for 'Complete Django tutorial' due [inherited date].
This becomes the desired outcome for a new chart.
What's your current reality regarding Django specifically?"
```

### 5. Tracking Progress and Completion

**Natural Language Input:**
```
"I completed the Django tutorial yesterday"
"Finished setting up my morning creative space"
"Done with the research phase - chose React Native"
```

**System Processing:**
- Mark specified action step as completed
- Automatically "flow into" current reality section
- Update chart status and recalculate progress
- Identify next action step in sequence
- Track advancing pattern data

**Response Pattern:**
```
"Great! Marking 'Django tutorial' as complete and updating your current reality.
Next up: 'Build practice project' (due: [date])
Your chart is now 33% complete."
```

### 6. Reality Updates and Adjustments

**Natural Language Input:**
```
"My situation changed - I got access to a Django course at work"  
"Update: I found a React Native bootcamp that starts next week"
"My morning routine reality: I successfully did 15 minutes for 5 days straight"
```

**System Processing:**
- Update current reality observations with new information
- Assess impact on existing action steps
- Suggest chart adjustments if needed
- Maintain structural tension with updated information

**Response Pattern:**
```
"Updated current reality with new Django course access.
This might accelerate your timeline - would you like to adjust your action steps or due dates?"
```

### 7. Chart Overview and Navigation

**Natural Language Input:**
```
"Show me my Python learning chart"
"What charts do I have active?"
"How am I progressing on the mobile app goal?"
"Give me an overview of all my creative projects"
```

**System Processing:**
- Locate relevant charts by name/topic
- Generate progress summaries
- Show telescoped relationships if any
- Highlight next actions and due dates

**Response Pattern:**
```
"Python Web Development Chart (67% complete):
✅ Django tutorial (completed)
🔄 Practice project (in progress, due: [date])
⏳ Deploy live site (due: [date])

Current reality: Django basics learned, project structure started
Next action: Complete user authentication feature"
```

### 8. Cross-Chart Connections and Dependencies

**Natural Language Input:**
```
"The mobile app project depends on finishing the Python learning first"
"My morning routine needs to include time for the web development work"
"These two goals are related - can we connect them?"
```

**System Processing:**
- Create dependency relations between charts
- Identify scheduling conflicts or synergies
- Suggest timeline adjustments
- Maintain structural integrity of each chart

**Response Pattern:**
```
"I've connected your Python learning chart as a prerequisite for the mobile app chart.
The mobile app timeline will adjust based on Python completion.
Would you like me to allocate morning routine time specifically for web development?"
```

## Language Pattern Guidelines

### Creative Orientation Language

**Use These Patterns:**
- "I want to create..."
- "My desired outcome is..."
- "I'm building toward..."
- "What I want to bring into being..."
- "The result I'm creating is..."

**Avoid These Patterns:**
- "I need to fix..."
- "The problem is..."
- "I want to stop..."
- "I need to eliminate..."
- "I have to solve..."

### Structural Tension Awareness

**Current Reality Patterns:**
- "Where I am now is..."
- "My current situation is..."
- "What I have today is..."
- "The reality I'm starting from..."

**Desired Outcome Patterns:**
- "What I want to create is..."
- "My vision is..."
- "The outcome I'm aiming for..."
- "What I want to have is..."

### Time and Progress Language

**Due Date Patterns:**
- "by [specific date]"
- "within [timeframe]"
- "in [number] weeks/months"
- "before [event/deadline]"

**Progress Patterns:**
- "I completed..."
- "I finished..."
- "Done with..."
- "Accomplished..."

## Conversation Flow Templates

### New Chart Creation Flow
```
User: "I want to create [outcome] by [timeframe]"
System: "I've captured your desired outcome: '[outcome]' due [calculated date]. What's your current reality regarding [topic]?"
User: "[current situation description]"
System: "Current reality noted. Structural tension established. What action steps will get you there?"
User: "[list of steps]"
System: "Created chart with [X] action steps. Timeline looks good. Need to break down any steps further?"
```

### Telescoping Flow
```
User: "Break down [action step] further" / "More detail on [step]"
System: "Creating detailed chart for '[action step]' due [inherited date]. What's your current reality specifically for this step?"
User: "[current state for sub-goal]"
System: "What smaller actions will advance you toward '[action step]'?"
User: "[sub-actions]"
System: "Detailed chart created. You can navigate back to the main chart anytime."
```

### Progress Check Flow
```
User: "How's my progress on [chart/goal]?"
System: "[Chart name] ([X]% complete):
✅ [completed items]
🔄 [current item] (due: [date])
⏳ [upcoming items]
Next recommended action: [specific next step]"
```

### Completion Flow
```
User: "I finished [action step]"
System: "Excellent! Marking '[action step]' complete and updating current reality. 
Progress: [X]% complete
Next: '[next action]' (due: [date])
[Encouraging/momentum comment]"
```

## System Response Principles

### Encouraging Advancement
- Acknowledge completions enthusiastically
- Highlight progress made
- Connect actions to larger vision
- Maintain momentum language

### Structural Tension Maintenance
- Always relate back to desired outcome
- Keep current reality updated
- Ensure action steps bridge the gap
- Preserve the creative tension

### Natural Flow
- Use conversational, not technical language
- Mirror the user's terminology when possible
- Ask clarifying questions naturally
- Provide gentle guidance toward structural thinking

### Creative Orientation
- Focus on what's being created, not problems solved
- Emphasize building and manifesting
- Support advancing patterns
- Celebrate structural tension as productive energy

## Implementation Notes

### Entity Recognition
The system needs to recognize when users are:
- Stating desired outcomes vs current reality
- Listing action steps vs making general comments  
- Requesting telescoping vs asking for information
- Reporting completion vs reporting problems

### Context Awareness
- Remember which chart is currently active
- Track conversation history within chart context
- Understand user's preferred language patterns
- Maintain awareness of due dates and urgency

### Graceful Degradation
- When uncertain, ask clarifying questions
- Default to structural tension thinking
- Guide users toward creative orientation
- Provide examples when users seem stuck

This natural language interface should make structural tension charts feel like a natural extension of creative thinking rather than a technical tool to learn.