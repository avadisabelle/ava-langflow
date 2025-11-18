#!/usr/bin/env node

// Simple test of coaia-spiral functionality
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const serverPath = join(__dirname, 'dist', 'index.js');

console.log('🚀 Testing COAIA Memory System...\n');

// Start the MCP server
const server = spawn('node', [serverPath, '--memory-path', './test-memory.jsonl'], {
  stdio: ['pipe', 'pipe', 'pipe']
});

// Test data
const testChart = {
  desiredOutcome: "Learn Python web development",
  currentReality: "I know basic Python but no web frameworks",
  dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days from now
  actionSteps: [
    "Complete Django tutorial",
    "Build a practice project", 
    "Deploy something live"
  ]
};

// Send test commands
const testCommands = [
  // List tools
  {
    jsonrpc: "2.0",
    id: 1,
    method: "tools/list"
  },
  
  // Create structural tension chart
  {
    jsonrpc: "2.0",
    id: 2,
    method: "tools/call",
    params: {
      name: "create_structural_tension_chart",
      arguments: testChart
    }
  },
  
  // List active charts
  {
    jsonrpc: "2.0",
    id: 3,
    method: "tools/call",
    params: {
      name: "list_active_charts",
      arguments: {}
    }
  }
];

let commandIndex = 0;

// Handle server responses
server.stdout.on('data', (data) => {
  const response = data.toString();
  console.log('📥 Server Response:', response);
  
  // Send next command
  if (commandIndex < testCommands.length) {
    setTimeout(() => {
      const command = JSON.stringify(testCommands[commandIndex]) + '\n';
      console.log(`📤 Sending command ${commandIndex + 1}:`, testCommands[commandIndex].method);
      server.stdin.write(command);
      commandIndex++;
    }, 500);
  } else {
    // All commands sent, close server
    setTimeout(() => {
      server.kill();
      console.log('\n✅ COAIA Memory test completed!');
    }, 1000);
  }
});

server.stderr.on('data', (data) => {
  console.log('ℹ️  Server Info:', data.toString());
  
  // Server is ready, send first command
  if (data.toString().includes('running on stdio') && commandIndex === 0) {
    setTimeout(() => {
      const command = JSON.stringify(testCommands[commandIndex]) + '\n';
      console.log(`📤 Sending command ${commandIndex + 1}:`, testCommands[commandIndex].method);
      server.stdin.write(command);
      commandIndex++;
    }, 500);
  }
});

server.on('close', (code) => {
  console.log(`\n🏁 Test completed with exit code: ${code}`);
  process.exit(code);
});

// Cleanup on exit
process.on('SIGINT', () => {
  server.kill();
  process.exit(0);
});
