# MCP Memory Server Pull Request Instructions

## Current Working Setup Preservation

Keep your local working version intact at `C:\Users\shane\Desktop\memory` until PR is merged:

```json
{
  "mcpServers": {
    "memory": {
      "command": "volta",
      "args": [
        "run",
        "node",
        "C:\\Users\\shane\\Desktop\\memory\\dist\\index.js",
        "--memory-path",
        "C:\\Users\\shane\\Desktop\\memory\\memory.jsonl"
      ]
    }
  }
}
```

## Getting the Original Repository

```bash
git clone https://github.com/modelcontextprotocol/servers.git
cd servers
```

## Modified Files to Track

Current local modifications:

- `tsconfig.json` - Changed from monorepo to local paths
- `tsconfig.base.json` - Created locally for standalone build
- `index.ts` - Added memory path functionality

## Preparing the Pull Request

### 1. Configuration Files

Revert tsconfig.json back to monorepo structure:

```json
{
    "extends": "../../tsconfig.json",
    "compilerOptions": {
      "outDir": "./dist",
      "rootDir": "."
    },
    "include": [
      "./**/*.ts"
    ]
}
```

### 2. Remove Local-Only Files

- Delete local `tsconfig.base.json` (not needed in monorepo)

### 3. Code Changes to Submit

- Keep all memory path functionality changes in `index.ts`
- Ensure cross-platform path handling remains intact
- Verify JSONL extension usage

### 4. Dependencies

Ensure these are in the monorepo's package.json:

```json
{
  "dependencies": {
    "minimist": "^1.2.8"
  },
  "devDependencies": {
    "@types/minimist": "^1.2.5"
  }
}
```

### 5. Documentation Updates

- Update README.md with new --memory-path option
- Document JSONL format requirement
- Add cross-platform path handling notes

### 6. Pull Request Process

1. Create new branch:

   ```bash
   git checkout -b feature/custom-memory-path
   ```

2. Copy modified files:

   ```bash
   cp /path/to/your/index.ts packages/server-memory/
   ```

3. Test build in monorepo:

   ```bash
   npm install
   npm run build
   ```

4. Commit changes:

   ```bash
   git add .
   git commit -m "Add custom memory path support with cross-platform handling"
   ```

5. Create PR:
   - Push to GitHub
   - Create pull request
   - Reference any related issues
   - Describe testing performed

## Additional Considerations

- Consider adding tests for the new functionality
- Follow monorepo's contribution guidelines
- Document any breaking changes
- Test on multiple platforms if possible

## Backup Plan

Until PR is merged, maintain your working local version:

1. Keep local build working
2. Note any improvements needed for PR
3. Continue using local version for development
