#!/bin/bash
. _env.sh
export SESSION_ID=a66f8bd2-29f5-461d-ad65-36b65252d469
export session_id__avaLangflowAgenticFlywheel_2511180446
export session_id__avaLangflowAgenticFlywheel_2511180446__MCP_CONFIG
export session_id__avaLangflowAgenticFlywheel_2511180446__ADD_DIR
claude "we will want to develop @src/agentic_flywheel/ into this very own Langflow context (originally it works with flowise-ai but we want it to work in langflow), I guess that first, we will create a ./rispecs/ and use @__llms/llms-rise-framework.txt to create the specs that we need for that MCP, it was developped outside of here, therefore, it seemed relevant to explore extending its usage within this context for enhancing the work in here.  Given that it will be capable to store the chatflow (or langflow equivalent) being called by the Agentic Flywheel within Redis and that we would have potential tracing in langfuse, the coaiapy_aetherial MCP for example could be used to get the result of the inquiry being sent " --mcp-config $session_id__avaLangflowAgenticFlywheel_2511180446__MCP_CONFIG --add-dir $session_id__avaLangflowAgenticFlywheel_2511180446__ADD_DIR --session-id $session_id__avaLangflowAgenticFlywheel_2511180446
