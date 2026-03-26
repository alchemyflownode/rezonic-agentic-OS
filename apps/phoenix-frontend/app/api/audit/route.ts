// app/api/audit/route.ts
import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

interface ComponentInfo {
  name: string;
  purpose: string;
  usedIn: number;
  status: 'active' | 'available' | 'deprecated';
  filePath: string;
  imports: string[];
  usedBy: string[];
}

interface PageInfo {
  path: string;
  component: string;
  size: string;
  status: 'active' | 'inactive';
  lastModified: string;
}

export async function GET() {
  try {
    const projectRoot = path.join(process.cwd());
    const componentsDir = path.join(projectRoot, 'components');
    const appDir = path.join(projectRoot, 'app');
    
    // Scan all components
    const componentFiles = await scanDirectory(componentsDir, '.tsx');
    const components: ComponentInfo[] = [];
    
    for (const file of componentFiles) {
      const content = await fs.readFile(file, 'utf-8');
      const name = path.basename(file, '.tsx');
      const imports = extractImports(content);
      
      // Find where this component is used
      const usedBy = await findUsage(name, appDir);
      
      components.push({
        name,
        purpose: extractPurpose(content) || getPurposeFromName(name),
        usedIn: usedBy.length,
        status: usedBy.length > 0 ? 'active' : 'available',
        filePath: path.relative(projectRoot, file),
        imports,
        usedBy
      });
    }
    
    // Scan all pages
    const pageFiles = await scanDirectory(appDir, 'page.tsx');
    const pages: PageInfo[] = [];
    
    for (const file of pageFiles) {
      const content = await fs.readFile(file, 'utf-8');
      const routePath = getRoutePath(file, appDir);
      const stats = await fs.stat(file);
      
      // Determine main component used
      const componentMatch = content.match(/import.*from.*components\/(\w+)/);
      const mainComponent = componentMatch ? componentMatch[1] : 'Unknown';
      
      pages.push({
        path: routePath,
        component: mainComponent,
        size: `${(stats.size / 1024).toFixed(2)}KB`,
        status: 'active',
        lastModified: stats.mtime.toISOString().split('T')[0]
      });
    }
    
    // Generate audit report
    const auditReport = {
      pages,
      components,
      issues: generateIssues(components),
      performance: {
        totalComponents: components.length,
        totalPages: pages.length,
        buildTime: '2.5s',
        bundleSize: calculateBundleSize(pages)
      },
      timestamp: new Date().toISOString()
    };
    
    return NextResponse.json(auditReport);
    
  } catch (error) {
    console.error('Audit error:', error);
    return NextResponse.json(
      { error: 'Failed to scan project' },
      { status: 500 }
    );
  }
}

// Helper: Scan directory recursively
async function scanDirectory(dir: string, extension: string): Promise<string[]> {
  const files: string[] = [];
  
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      
      if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
        const subFiles = await scanDirectory(fullPath, extension);
        files.push(...subFiles);
      } else if (entry.isFile() && entry.name.endsWith(extension)) {
        files.push(fullPath);
      }
    }
  } catch (err) {
    // Directory might not exist
  }
  
  return files;
}

// Helper: Extract imports from file
function extractImports(content: string): string[] {
  const imports: string[] = [];
  const importRegex = /import\s+(?:{([^}]+)}|\*\s+as\s+(\w+)|(\w+))\s+from\s+['"]([^'"]+)['"]/g;
  let match;
  
  while ((match = importRegex.exec(content)) !== null) {
    if (match[1]) {
      // Named imports
      const named = match[1].split(',').map(i => i.trim());
      imports.push(...named);
    } else if (match[2]) {
      // Namespace import
      imports.push(match[2]);
    } else if (match[3]) {
      // Default import
      imports.push(match[3]);
    }
  }
  
  return imports;
}

// Helper: Find usage of component
async function findUsage(componentName: string, searchDir: string): Promise<string[]> {
  const usedIn: string[] = [];
  const files = await scanDirectory(searchDir, '.tsx');
  
  for (const file of files) {
    const content = await fs.readFile(file, 'utf-8');
    if (content.includes(componentName)) {
      const relativePath = path.relative(process.cwd(), file);
      usedIn.push(relativePath);
    }
  }
  
  return usedIn;
}

// Helper: Extract purpose from component comments
function extractPurpose(content: string): string {
  const commentMatch = content.match(/\/\/ Purpose:\s*(.+)/);
  if (commentMatch) return commentMatch[1];
  
  const jsdocMatch = content.match(/\/\*\*\s*\n?\s*\*\s*(.+)/);
  if (jsdocMatch) return jsdocMatch[1];
  
  return '';
}

// Helper: Get purpose from component name
function getPurposeFromName(name: string): string {
  const purposes: Record<string, string> = {
    SovereignCanvas: 'Code display & execution with Pyodide',
    SovereignMessage: 'Chat & AI responses with code block parsing',
    SovereignCodeBlock: 'Beautiful code display with syntax highlighting',
    SovereignCodeSurface: 'Full IDE with multi-file editing',
    PaperTradingPanel: 'Paper trading interface',
    TradingPanel: 'Live trading interface',
  };
  
  return purposes[name] || 'Component purpose unknown';
}

// Helper: Get route path from file
function getRoutePath(filePath: string, appDir: string): string {
  let relative = path.relative(appDir, filePath);
  relative = relative.replace(/\\/g, '/');
  relative = relative.replace('/page.tsx', '');
  relative = relative.replace('page.tsx', '');
  
  if (relative === '') return '/';
  return '/' + relative;
}

// Helper: Generate issues
function generateIssues(components: ComponentInfo[]) {
  const issues = [];
  
  for (const comp of components) {
    if (comp.usedIn === 0) {
      issues.push({
        type: 'warning',
        message: `${comp.name} exists but is not used anywhere`,
        component: comp.name
      });
    } else {
      issues.push({
        type: 'success',
        message: `${comp.name} is actively used in ${comp.usedIn} location${comp.usedIn > 1 ? 's' : ''}`,
        component: comp.name
      });
    }
  }
  
  return issues;
}

// Helper: Calculate bundle size
function calculateBundleSize(pages: PageInfo[]): string {
  const totalKB = pages.reduce((acc, page) => {
    const size = parseFloat(page.size);
    return acc + (isNaN(size) ? 0 : size);
  }, 0);
  
  return `${(totalKB / 1024).toFixed(2)}MB`;
}
