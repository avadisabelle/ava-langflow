# Development Workflow

## Initial Environment

- Windows 11 system
- Node.js environment managed by Volta
- PowerShell 7.4.6 as the terminal

## Project Structure

This is part of a monorepo project:

- Package: @modelcontextprotocol/server-memory
- Version: 0.6.2
- Type: ES Module (package.json "type": "module")

## Setup Steps

1. **TypeScript Configuration**
   - Created tsconfig.base.json with ES module support:

     ```json
     {
       "compilerOptions": {
         "target": "ES2020",
         "module": "NodeNext",
         "moduleResolution": "NodeNext",
         "esModuleInterop": true,
         "strict": true,
         "skipLibCheck": true,
         "forceConsistentCasingInFileNames": true,
         "declaration": true,
         "sourceMap": true,
         "allowJs": true,
         "checkJs": true
       }
     }
     ```

   - Maintained monorepo compatibility in tsconfig.json:

     ```json
     {
       "extends": "./tsconfig.base.json",
       "compilerOptions": {
         "outDir": "./dist",
         "rootDir": "."
       },
       "include": [
         "./**/*.ts"
       ]
     }
     ```

2. **Dependencies**
   - Installed TypeScript globally with Volta:

     ```bash
     volta install typescript
     ```

   - Added type definitions for minimist:

     ```bash
     volta run npm install --save-dev @types/minimist
     ```

3. **Code Fixes**
   - Fixed duplicate argv declarations in index.ts
   - Removed backup directory that was causing build conflicts
   - Ensured proper ES module imports

4. **Build Process**
   - Build script in package.json:

     ```json
     "scripts": {
       "build": "tsc && shx chmod +x dist/*.js",
       "prepare": "npm run build",
       "watch": "tsc --watch"
     }
     ```

   - Successfully built with:

     ```bash
     volta run npm run build
     ```

## Build Output

The successful build generates:

- dist/index.js (compiled JavaScript)
- dist/index.d.ts (TypeScript declarations)
- dist/index.js.map (source maps)

## Testing via  Inspector

- Run the inspector with a memory path argument:

```sh
volta run npx @modelcontextprotocol/inspector dist/index.js --memory-path=C:/Users/shane/Desktop/memory/memory.jsonl
```

## Development Notes

- Keep monorepo compatibility in mind when making changes
- Use Volta for all Node.js/npm operations
- Maintain ES module format throughout the codebase
- Run builds with `volta run npm run build`
