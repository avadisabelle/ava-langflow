#!/bin/bash
# Flowise flow management and intelligent routing

# Flow registry - Add your actual flow IDs here
declare -A FLOWS=(
    ["creative-orientation"]="7d405a51-968d-4467-9ae6-d49bf182cdf9"
    ["technical-analysis"]="896f7eed-342e-4596-9429-6fb9b5fbd91b"
    ["document-qa"]="8ce0ad25-da40-490e-a8ba-f00ea7836677"
    ["faith2story"]="896f7eed-342e-4596-9429-6fb9b5fbd91b"
    ["miadi46code"]="aad975b2-289f-4acc-acc0-f19f4cfcb013"
)

# Default flowise URL
FLOWISE_URL="${FLOWISE_URL:-https://beagle-emerging-gnu.ngrok-free.app}"

# Usage function
usage() {
    echo "Usage: $0 <intent> <question> [session_id] [flow_override]"
    echo ""
    echo "Intent options:"
    echo "  creative, orientation, planning - Uses creative orientation flow"
    echo "  technical, analysis, code      - Uses technical analysis flow"
    echo "  document, qa, search          - Uses document QA flow"
    echo "  miadi, coding, prototype       - Uses Miadi46Code development flow"
    echo ""
    echo "Examples:"
    echo "  $0 creative 'How can I improve my project?'"
    echo "  $0 technical 'Debug this code issue' my-session-123"
    echo "  $0 document 'Find information about X' session-456 custom-flow-id"
    exit 1
}

# Execute flowise query with configuration override
curl_flowise() {
    local flow_id="$1"
    local question="$2"
    local config="$3"
    local session_id="$4"
    
    # Build payload with overrideConfig
    local payload="{\"question\": \"$question\""
    
    if [[ -n "$config" && "$config" != "{}" ]]; then
        payload+=", \"overrideConfig\": $config"
    fi
    
    # Add sessionId to overrideConfig if provided
    if [[ -n "$session_id" ]]; then
        if [[ "$payload" == *"overrideConfig"* ]]; then
            # Remove closing brace and add sessionId
            payload="${payload%\}}, \"sessionId\": \"$session_id\"}"
        else
            payload+=", \"overrideConfig\": {\"sessionId\": \"$session_id\"}"
        fi
    fi
    
    payload+="}"
    
    echo "Querying flow: $flow_id"
    echo "Payload: $payload"
    echo ""
    
    curl "$FLOWISE_URL/api/v1/prediction/$flow_id" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        2>/dev/null | jq -r '.text // .answer // .' 2>/dev/null || echo "Error: Unable to parse response"
}

# Intelligent flow selection based on intent
flow_select() {
    local intent="$1"
    local question="$2"
    local session_id="$3"
    local flow_override="$4"
    
    # Use flow override if provided
    if [[ -n "$flow_override" ]]; then
        flow_id="$flow_override"
        config='{"temperature": 0.7}'
    else
        # Intelligent flow selection based on intent
        case "$intent" in
            "creative"|"orientation"|"planning")
                flow_id="${FLOWS[creative-orientation]}"
                config='{
                    "temperature": 0.8, 
                    "rephrasePrompt": "Rephrase this question to focus on creative opportunities and desired outcomes: {question}",
                    "responsePrompt": "Respond with creative orientation principles, focusing on structural tension and advancement energy: {context}"
                }'
                ;;
            "technical"|"analysis"|"code")
                flow_id="${FLOWS[technical-analysis]}"
                config='{
                    "temperature": 0.3, 
                    "returnSourceDocuments": true,
                    "maxOutputTokens": 2000
                }'
                ;;
            "document"|"qa"|"search")
                flow_id="${FLOWS[document-qa]}"
                config='{
                    "temperature": 0.5, 
                    "returnSourceDocuments": true,
                    "rephrasePrompt": "Clarify this information request: {question}"
                }'
                ;;
            "miadi"|"coding"|"prototype")
                flow_id="${FLOWS[miadi46code]}"
                config='{
                    "temperature": 0.3,
                    "returnSourceDocuments": true,
                    "modelName": "qwen3-coder",
                    "sessionTTL": 3600,
                    "windowSize": 10,
                    "rephrasePrompt": "Transform this into a specific coding request for the Miadi project: {question}",
                    "responsePrompt": "Generate code for the Miadi project based on available documentation and codebase context: {context}"
                }'
                ;;
            *)
                echo "Unknown intent: $intent. Using creative orientation flow."
                flow_id="${FLOWS[creative-orientation]}"
                config='{"temperature": 0.7}'
                ;;
        esac
    fi
    
    # Execute with configuration override
    curl_flowise "$flow_id" "$question" "$config" "$session_id"
}

# Generate unique session ID
generate_session_id() {
    echo "session-$(date +%s)-$$"
}

# Main execution
main() {
    if [[ $# -lt 2 ]]; then
        usage
    fi
    
    local intent="$1"
    local question="$2"
    local session_id="$3"
    local flow_override="$4"
    
    # Generate session ID if not provided
    if [[ -z "$session_id" ]]; then
        session_id=$(generate_session_id)
        echo "Generated session ID: $session_id"
        echo ""
    fi
    
    flow_select "$intent" "$question" "$session_id" "$flow_override"
}

# Check dependencies
if ! command -v curl &> /dev/null; then
    echo "Error: curl is required but not installed."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "Warning: jq not found. Response formatting may be limited."
fi

# Run main function
main "$@"