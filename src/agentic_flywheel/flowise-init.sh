#!/bin/bash
# Flowise Environment Initialization and Configuration Manager
# Supports --init mode for environment setup and configuration persistence

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/flowise-workspace.yaml"
DEFAULT_CONFIG_FILE="$SCRIPT_DIR/flow-registry.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Usage function
usage() {
    echo "Flowise Environment Initialization and Management"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --init              Initialize new flowise workspace"
    echo "  --load-config FILE  Load configuration from specific file"
    echo "  --save-config FILE  Save current configuration to file"
    echo "  --list-flows        List available flows from registry"
    echo "  --test-flows        Test connectivity to all configured flows"
    echo "  --session-prefix    Generate session prefix for current context"
    echo "  --env ENV           Set environment (development|production)"
    echo "  --help              Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  FLOWISE_ENV         Environment mode (development|production)"
    echo "  FLOWISE_URL         Override base URL"
    echo "  FLOWISE_WORKSPACE   Path to workspace configuration"
    echo ""
    echo "Examples:"
    echo "  $0 --init                                 # Initialize new workspace"
    echo "  $0 --session-prefix creative-orientation  # Generate session ID"
    echo "  $0 --test-flows                          # Test all flow connections"
    echo "  $0 --env production --save-config        # Save production config"
}

# Generate UUID (fallback implementations)
generate_uuid() {
    if command -v uuid >/dev/null 2>&1; then
        uuid
    elif command -v uuidgen >/dev/null 2>&1; then
        uuidgen | tr '[:upper:]' '[:lower:]'
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c "import uuid; print(uuid.uuid4())"
    else
        # Fallback to timestamp + random
        echo "$(date +%s)-$(shuf -i 1000-9999 -n 1)-$(shuf -i 1000-9999 -n 1)-$(shuf -i 1000-9999 -n 1)"
    fi
}

# Initialize workspace configuration
init_workspace() {
    echo -e "${BLUE}🚀 Initializing Flowise Workspace${NC}"
    echo ""
    
    # Collect workspace information
    read -p "Workspace name: " WORKSPACE_NAME
    read -p "Project description: " PROJECT_DESC
    read -p "Flowise base URL [https://beagle-emerging-gnu.ngrok-free.app]: " BASE_URL
    BASE_URL=${BASE_URL:-"https://beagle-emerging-gnu.ngrok-free.app"}
    
    read -p "Environment (development|production) [production]: " ENVIRONMENT
    ENVIRONMENT=${ENVIRONMENT:-"production"}
    
    # Generate workspace UUID
    WORKSPACE_ID=$(generate_uuid)
    
    # Create workspace configuration
    cat > "$CONFIG_FILE" << EOF
# Flowise Workspace Configuration
# Generated: $(date)

workspace:
  name: "$WORKSPACE_NAME"
  id: "$WORKSPACE_ID"
  description: "$PROJECT_DESC"
  created: "$(date -Iseconds)"
  version: "1.0.0"

environment:
  current: "$ENVIRONMENT"
  base_url: "$BASE_URL"
  
# Active flows configuration
active_flows:
  creative-orientation:
    id: "7d405a51-968d-4467-9ae6-d49bf182cdf9"
    session_prefix: "chat:creative-orientation"
    status: "active"
    last_tested: ""
    
  faith2story:
    id: "896f7eed-342e-4596-9429-6fb9b5fbd91b"
    session_prefix: "chat:faith2story"
    status: "active"
    last_tested: ""

# Session management
session_config:
  default_ttl: 3600
  uuid_format: "uuid4"
  current_session: ""
  
# Integration settings
integrations:
  rise_framework:
    enabled: true
    path: "/media/jgi/F/Dropbox/jgt/edu/llm_mastery/arenas_250706/cross_REPO_WORK__RISE/"
  
  mcp_server:
    enabled: true
    port: 3000

# Work context
context:
  current_project: "$WORKSPACE_NAME"
  active_phase: "initialization"
  structural_tension:
    current_reality: "Setting up flowise automation environment"
    desired_outcome: "Fully operational creative-oriented flowise workflows"
    
# History tracking
history:
  sessions: []
  flows_used: []
  configurations: []
EOF

    echo -e "${GREEN}✅ Workspace configuration created: $CONFIG_FILE${NC}"
    echo -e "${YELLOW}📋 Workspace ID: $WORKSPACE_ID${NC}"
    echo ""
    
    # Test connections
    echo -e "${BLUE}🔧 Testing flow connections...${NC}"
    test_flows_connectivity
    
    echo ""
    echo -e "${GREEN}🎉 Workspace initialization complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test flows: $0 --test-flows"
    echo "  2. Generate session: $0 --session-prefix creative-orientation"
    echo "  3. Use flowise tools with your configured environment"
}

# Load configuration from file
load_configuration() {
    local config_file="$1"
    if [[ ! -f "$config_file" ]]; then
        echo -e "${RED}❌ Configuration file not found: $config_file${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📥 Loading configuration from: $config_file${NC}"
    
    # Parse YAML and set environment variables
    if command -v yq >/dev/null 2>&1; then
        export FLOWISE_URL=$(yq e '.environment.base_url' "$config_file")
        export FLOWISE_ENV=$(yq e '.environment.current' "$config_file")
        echo -e "${GREEN}✅ Configuration loaded${NC}"
        echo -e "${YELLOW}   Base URL: $FLOWISE_URL${NC}"
        echo -e "${YELLOW}   Environment: $FLOWISE_ENV${NC}"
    else
        echo -e "${YELLOW}⚠️  yq not available, manual configuration required${NC}"
        echo "   Install yq for automatic configuration parsing"
    fi
}

# Save current configuration
save_configuration() {
    local config_file="${1:-$CONFIG_FILE}"
    echo -e "${BLUE}💾 Saving configuration to: $config_file${NC}"
    
    # Update timestamps and session history
    if [[ -f "$config_file" ]]; then
        # Create backup
        cp "$config_file" "${config_file}.backup.$(date +%s)"
        echo -e "${GREEN}✅ Configuration saved (backup created)${NC}"
    else
        echo -e "${YELLOW}⚠️  No existing configuration to save${NC}"
    fi
}

# List available flows
list_flows() {
    echo -e "${BLUE}📋 Available Flowise Flows${NC}"
    echo ""
    
    if [[ -f "$CONFIG_FILE" ]]; then
        echo "From workspace configuration:"
        if command -v yq >/dev/null 2>&1; then
            yq e '.active_flows | to_entries | .[] | "  " + .key + " (" + .value.id + ")"' "$CONFIG_FILE"
        else
            grep -A 1 "id:" "$CONFIG_FILE" | grep -v "^--$"
        fi
    else
        echo "From default registry:"
        if [[ -f "$DEFAULT_CONFIG_FILE" ]]; then
            echo "  creative-orientation (7d405a51-968d-4467-9ae6-d49bf182cdf9)"
            echo "  faith2story (896f7eed-342e-4596-9429-6fb9b5fbd91b)"
        fi
    fi
    echo ""
}

# Test flow connectivity
test_flows_connectivity() {
    echo -e "${BLUE}🔍 Testing flow connectivity...${NC}"
    
    # Use Python script to test connections
    if [[ -f "$SCRIPT_DIR/flowise-config-manager.py" ]]; then
        if python3 "$SCRIPT_DIR/flowise-config-manager.py" --test-connection; then
            echo -e "${GREEN}✅ Flowise server reachable${NC}"
        else
            echo -e "${RED}❌ Cannot reach Flowise server${NC}"
        fi
        
        # Test specific flows
        echo "Testing individual flows:"
        python3 "$SCRIPT_DIR/flowise-config-manager.py" --list-flows
    else
        echo -e "${YELLOW}⚠️  flowise-config-manager.py not found${NC}"
    fi
}

# Generate session prefix
generate_session_prefix() {
    local flow_type="$1"
    local uuid=$(generate_uuid)
    
    if [[ -z "$flow_type" ]]; then
        echo "chat:session:$uuid"
    else
        echo "chat:$flow_type:$uuid"
    fi
}

# Update flow status
update_flow_status() {
    local flow_name="$1"
    local status="$2"
    local timestamp=$(date -Iseconds)
    
    # Update configuration file with new status
    if [[ -f "$CONFIG_FILE" ]] && command -v yq >/dev/null 2>&1; then
        yq e ".active_flows.$flow_name.last_tested = \"$timestamp\"" -i "$CONFIG_FILE"
        yq e ".active_flows.$flow_name.status = \"$status\"" -i "$CONFIG_FILE"
        echo -e "${GREEN}✅ Updated $flow_name status: $status${NC}"
    fi
}

# Set environment
set_environment() {
    local env="$1"
    
    if [[ "$env" != "development" && "$env" != "production" ]]; then
        echo -e "${RED}❌ Invalid environment: $env${NC}"
        echo "Valid environments: development, production"
        return 1
    fi
    
    export FLOWISE_ENV="$env"
    
    if [[ "$env" == "development" ]]; then
        export FLOWISE_URL="http://localhost:3222"
    else
        export FLOWISE_URL="https://beagle-emerging-gnu.ngrok-free.app"
    fi
    
    echo -e "${GREEN}✅ Environment set to: $env${NC}"
    echo -e "${YELLOW}   Base URL: $FLOWISE_URL${NC}"
}

# Main execution
main() {
    case "$1" in
        --init)
            init_workspace
            ;;
        --load-config)
            load_configuration "$2"
            ;;
        --save-config)
            save_configuration "$2"
            ;;
        --list-flows)
            list_flows
            ;;
        --test-flows)
            test_flows_connectivity
            ;;
        --session-prefix)
            generate_session_prefix "$2"
            ;;
        --env)
            set_environment "$2"
            ;;
        --help|"")
            usage
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"