#!/bin/bash
# Global Installation Script for Flowise Automation
# Makes flowise capabilities available system-wide

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
FLOWISE_HOME="/opt/flowise-automation"
CONFIG_DIR="/etc/flowise"
USER_CONFIG_DIR="$HOME/.config/flowise"
BIN_DIR="/usr/local/bin"
SYSTEMD_DIR="/etc/systemd/system"

# Current script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running as root for system installation
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        INSTALL_MODE="system"
        echo -e "${BLUE}🔧 Installing system-wide (requires root)${NC}"
    else
        INSTALL_MODE="user"
        FLOWISE_HOME="$HOME/.local/share/flowise-automation"
        CONFIG_DIR="$HOME/.config/flowise"
        BIN_DIR="$HOME/.local/bin"
        echo -e "${YELLOW}👤 Installing for current user only${NC}"
        
        # Ensure user bin directory exists and is in PATH
        mkdir -p "$BIN_DIR"
        if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
            echo -e "${YELLOW}⚠️  Add $BIN_DIR to your PATH for global access${NC}"
            echo "   Add this to your ~/.bashrc or ~/.zshrc:"
            echo "   export PATH=\"$BIN_DIR:\$PATH\""
        fi
    fi
}

# Create directory structure
create_directories() {
    echo -e "${BLUE}📁 Creating directory structure...${NC}"
    
    if [[ "$INSTALL_MODE" == "system" ]]; then
        mkdir -p "$FLOWISE_HOME" "$CONFIG_DIR" "$BIN_DIR"
        # Create flowise user if system install
        if ! id "flowise" &>/dev/null; then
            useradd -r -s /bin/false -d "$FLOWISE_HOME" flowise
            echo -e "${GREEN}👤 Created flowise system user${NC}"
        fi
    else
        mkdir -p "$FLOWISE_HOME" "$CONFIG_DIR" "$BIN_DIR"
    fi
    
    # Create config subdirectories
    mkdir -p "$CONFIG_DIR"/{environments,workspaces,templates}
    mkdir -p "$USER_CONFIG_DIR"/{workspaces,sessions,history}
}

# Copy core files
install_core_files() {
    echo -e "${BLUE}📦 Installing core files...${NC}"
    
    # Copy all flowise files to installation directory
    cp -r "$SCRIPT_DIR"/* "$FLOWISE_HOME/"
    
    # Make scripts executable
    chmod +x "$FLOWISE_HOME"/*.sh
    chmod +x "$FLOWISE_HOME"/*.py
    
    # Install global configurations
    if [[ ! -f "$CONFIG_DIR/global-config.yaml" ]]; then
        cp "$FLOWISE_HOME/flow-registry.yaml" "$CONFIG_DIR/global-config.yaml"
        echo -e "${GREEN}📄 Installed global configuration${NC}"
    fi
    
    # Set ownership for system install
    if [[ "$INSTALL_MODE" == "system" ]]; then
        chown -R flowise:flowise "$FLOWISE_HOME"
        chown -R root:root "$CONFIG_DIR"
        chmod 755 "$CONFIG_DIR"
    fi
}

# Create global command symlinks
create_global_commands() {
    echo -e "${BLUE}🔗 Creating global commands...${NC}"
    
    # Create symbolic links for global access
    ln -sf "$FLOWISE_HOME/flowise-manager.sh" "$BIN_DIR/flowise"
    ln -sf "$FLOWISE_HOME/flowise-config-manager.py" "$BIN_DIR/flowise-config" 
    ln -sf "$FLOWISE_HOME/flowise-init.sh" "$BIN_DIR/flowise-init"
    ln -sf "$FLOWISE_HOME/flowise-mcp-server.py" "$BIN_DIR/flowise-mcp"
    
    # Create convenience aliases
    cat > "$BIN_DIR/flowise-creative" << 'EOF'
#!/bin/bash
# Quick creative orientation access
SESSION_ID="chat:creative-orientation:$(python3 -c 'import uuid; print(uuid.uuid4())')"
flowise creative "$1" "$SESSION_ID"
EOF
    
    cat > "$BIN_DIR/flowise-faith" << 'EOF'
#!/bin/bash
# Quick faith2story access  
SESSION_ID="chat:faith2story:$(python3 -c 'import uuid; print(uuid.uuid4())')"
flowise-config "$1" --intent faith2story --session-id "$SESSION_ID"
EOF
    
    chmod +x "$BIN_DIR/flowise-creative" "$BIN_DIR/flowise-faith"
    
    echo -e "${GREEN}✅ Global commands created:${NC}"
    echo "  - flowise (main interface)"
    echo "  - flowise-config (advanced configuration)"
    echo "  - flowise-init (workspace management)"
    echo "  - flowise-mcp (MCP server)"
    echo "  - flowise-creative (quick creative orientation)"
    echo "  - flowise-faith (quick faith2story)"
}

# Install system service (only for system install)
install_system_service() {
    if [[ "$INSTALL_MODE" != "system" ]]; then
        return 0
    fi
    
    echo -e "${BLUE}⚙️  Installing system services...${NC}"
    
    # Create MCP server service
    cat > "$SYSTEMD_DIR/flowise-mcp.service" << EOF
[Unit]
Description=Flowise MCP Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=flowise
Group=flowise
WorkingDirectory=$FLOWISE_HOME
ExecStart=/usr/bin/python3 $FLOWISE_HOME/flowise-mcp-server.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=$FLOWISE_HOME

[Install]
WantedBy=multi-user.target
EOF

    # Create HTTP gateway service
    cat > "$SYSTEMD_DIR/flowise-gateway.service" << EOF
[Unit]
Description=Flowise HTTP Gateway
After=network.target
Wants=network.target

[Service]
Type=simple
User=flowise
Group=flowise
WorkingDirectory=$FLOWISE_HOME
ExecStart=/usr/bin/python3 -m http.server 8080 --bind 0.0.0.0
Restart=always
RestartSec=10
Environment=FLOWISE_CONFIG_PATH=$CONFIG_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable flowise-mcp.service
    
    echo -e "${GREEN}🔧 System services installed and enabled${NC}"
    echo "  - flowise-mcp.service (MCP server)"
    echo "  - flowise-gateway.service (HTTP gateway)"
    echo ""
    echo "Start services with:"
    echo "  sudo systemctl start flowise-mcp"
    echo "  sudo systemctl start flowise-gateway"
}

# Setup shell integration
setup_shell_integration() {
    echo -e "${BLUE}🐚 Setting up shell integration...${NC}"
    
    # Create shell integration script
    cat > "$CONFIG_DIR/shell-integration.sh" << 'EOF'
#!/bin/bash
# Flowise Shell Integration
# Source this file in your ~/.bashrc or ~/.zshrc

# Environment variables
export FLOWISE_HOME="${FLOWISE_HOME:-/opt/flowise-automation}"
export FLOWISE_CONFIG_DIR="${FLOWISE_CONFIG_DIR:-/etc/flowise}"

# Quick functions
flowise-quick() {
    local question="$1"
    local session_id="chat:quick:$(python3 -c 'import uuid; print(uuid.uuid4())')"
    flowise creative "$question" "$session_id"
}

flowise-session() {
    local flow="$1"
    local session_id="chat:$flow:$(python3 -c 'import uuid; print(uuid.uuid4())')"
    echo "Session: $session_id"
    export FLOWISE_SESSION="$session_id"
}

flowise-auto() {
    flowise-config "$1" --intent document-qa --session-id "$(flowise-session auto | cut -d' ' -f2)"
}

# Tab completion (basic)
_flowise_completion() {
    local commands="creative faith technical document auto"
    COMPREPLY=($(compgen -W "$commands" -- "${COMP_WORDS[1]}"))
}
complete -F _flowise_completion flowise

echo "🎯 Flowise automation ready - type 'flowise-quick' to get started"
EOF
    
    chmod +x "$CONFIG_DIR/shell-integration.sh"
    
    echo -e "${GREEN}🐚 Shell integration created${NC}"
    echo "  Add to your shell profile:"
    echo "  echo 'source $CONFIG_DIR/shell-integration.sh' >> ~/.bashrc"
}

# Create user configuration template
create_user_config() {
    echo -e "${BLUE}👤 Creating user configuration...${NC}"
    
    if [[ ! -f "$USER_CONFIG_DIR/user-config.yaml" ]]; then
        cat > "$USER_CONFIG_DIR/user-config.yaml" << EOF
# Flowise User Configuration
user:
  name: "$(whoami)"
  home: "$HOME"
  default_flow: "creative-orientation"
  
preferences:
  auto_generate_session: true
  session_ttl: 3600
  verbose_output: false
  
flows:
  creative-orientation:
    preferred_temperature: 0.8
    custom_prompts: {}
    
  faith2story:
    narrative_style: "reflective"
    preferred_temperature: 0.7

environment:
  current: "production"
  custom_base_url: ""
  
integrations:
  rise_framework: true
  mcp_server: true
EOF
        echo -e "${GREEN}📄 User configuration created${NC}"
    fi
}

# Test installation
test_installation() {
    echo -e "${BLUE}🧪 Testing installation...${NC}"
    
    # Test command availability
    if command -v flowise >/dev/null 2>&1; then
        echo -e "${GREEN}✅ flowise command available${NC}"
    else
        echo -e "${RED}❌ flowise command not found${NC}"
        return 1
    fi
    
    # Test configuration loading
    if flowise-init --list-flows >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Configuration loading works${NC}"
    else
        echo -e "${YELLOW}⚠️  Configuration may need adjustment${NC}"
    fi
    
    # Test Python dependencies
    if python3 -c "import requests, yaml" 2>/dev/null; then
        echo -e "${GREEN}✅ Python dependencies available${NC}"
    else
        echo -e "${YELLOW}⚠️  Install Python dependencies: pip install requests pyyaml${NC}"
    fi
    
    echo -e "${GREEN}🎉 Installation test completed${NC}"
}

# Main installation process
main() {
    echo -e "${BLUE}🚀 Flowise Automation Global Installation${NC}"
    echo "============================================"
    echo ""
    
    check_permissions
    create_directories
    install_core_files
    create_global_commands
    install_system_service
    setup_shell_integration
    create_user_config
    test_installation
    
    echo ""
    echo -e "${GREEN}🎉 Installation completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Add shell integration to your profile:"
    echo "   echo 'source $CONFIG_DIR/shell-integration.sh' >> ~/.bashrc"
    echo ""
    echo "2. Start using flowise globally:"
    echo "   flowise-quick 'What outcomes do I want to create?'"
    echo "   flowise creative 'Help me with creative planning'"
    echo "   flowise-faith 'Turn my experience into a story'"
    echo ""
    
    if [[ "$INSTALL_MODE" == "system" ]]; then
        echo "3. Start system services:"
        echo "   sudo systemctl start flowise-mcp"
        echo "   sudo systemctl start flowise-gateway"
        echo ""
    fi
    
    echo "4. Initialize a workspace:"
    echo "   flowise-init --init"
    echo ""
    echo -e "${BLUE}📚 Documentation: $FLOWISE_HOME/README.md${NC}"
    echo -e "${BLUE}🔧 Configuration: $CONFIG_DIR/global-config.yaml${NC}"
}

# Handle command line arguments
case "${1:-install}" in
    install)
        main
        ;;
    uninstall)
        echo -e "${YELLOW}🗑️  Uninstalling flowise automation...${NC}"
        rm -f "$BIN_DIR"/flowise* 2>/dev/null || true
        if [[ "$EUID" -eq 0 ]]; then
            systemctl stop flowise-mcp 2>/dev/null || true
            systemctl disable flowise-mcp 2>/dev/null || true
            rm -f "$SYSTEMD_DIR/flowise-"*.service
            systemctl daemon-reload
        fi
        echo -e "${GREEN}✅ Uninstallation completed${NC}"
        ;;
    test)
        test_installation
        ;;
    *)
        echo "Usage: $0 [install|uninstall|test]"
        exit 1
        ;;
esac