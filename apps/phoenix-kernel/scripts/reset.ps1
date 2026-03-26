# Step 1: Kill EVERYTHING
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process next -ErrorAction SilentlyContinue | Stop-Process -Force
taskkill /F /IM node.exe 2>$null
taskkill /F /IM next.exe 2>$null

# Step 2: Wait for cleanup
Start-Sleep -Seconds 5

# Step 3: Clear all caches
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force node_modules/.cache -ErrorAction SilentlyContinue
npm cache clean --force

# Step 4: Check what's in your app folder
Get-ChildItem "app" -File

# Step 5: Create a BRAND NEW minimal app
Remove-Item -Path "app" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "app" -Force | Out-Null

# Step 6: Create minimal files (no complex components)
@'
export default function Home() {
  return (
    <html>
      <body style={{ 
        background: '#1a1b26', 
        color: '#c0caf5',
        fontFamily: 'system-ui',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        margin: 0,
        padding: '20px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <h1 style={{ fontSize: '2rem', marginBottom: '1rem' }}>🔥 Phoenix OS</h1>
          <p style={{ color: '#7dcfff' }}>System Ready</p>
          <a href="/dashboard" style={{ 
            color: '#7dcfff',
            display: 'inline-block',
            marginTop: '2rem',
            textDecoration: 'none',
            border: '1px solid #7dcfff',
            padding: '8px 16px',
            borderRadius: '8px'
          }}>Enter Dashboard →</a>
        </div>
      </body>
    </html>
  );
}
'@ | Out-File -FilePath "app\page.tsx" -Encoding UTF8 -Force

# Step 7: Create minimal layout
@'
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
'@ | Out-File -FilePath "app\layout.tsx" -Encoding UTF8 -Force

# Step 8: Create empty globals.css
'' | Out-File -FilePath "app\globals.css" -Encoding UTF8 -Force

# Step 9: Start fresh
npm run dev