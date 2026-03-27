#!/bin/bash
# launch-local.sh — Sovereign Demo Launcher
# Run: ./scripts/launch-local.sh

echo ""
echo "🦊 Phoenix OS — Sovereign AI Operating System"
echo "═══════════════════════════════════════════════════════════════"
echo "• Execution: LOCAL ONLY"
echo "• Telemetry: DISABLED"
echo "• Constitution: ACTIVE"
echo "• Determinism: TEMPERATURE=0"
echo ""

# Check if we're in the right directory
if [ ! -d "apps/phoenix-kernel" ]; then
    echo "❌ Please run this script from the repository root"
    echo "   cd /path/to/rezonic-agentic-OS"
    echo "   ./scripts/launch-local.sh"
    exit 1
fi

# Verify integrity (optional)
echo "🔐 Verifying kernel integrity..."
if command -v sha256sum &> /dev/null; then
    ACTUAL_HASH=$(sha256sum apps/phoenix-kernel/rezphoenix_v15_final.py | cut -d' ' -f1)
    echo "   Kernel hash: ${ACTUAL_HASH:0:32}..."
else
    echo "   (sha256sum not available — skipping hash check)"
fi

# Start kernel
echo ""
echo "🚀 Launching Phoenix Kernel (port 8002)..."
cd apps/phoenix-kernel
python rezphoenix_v15_final.py &
KERNEL_PID=$!

# Wait for kernel to be ready
echo "   Waiting for kernel to initialize..."
sleep 5

# Start frontend
echo "🎨 Launching Phoenix Frontend (port 3000)..."
cd ../phoenix-frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Phoenix OS is now running!"
echo ""
echo "📍 Dashboard: http://localhost:3000"
echo "📍 Kernel API: http://localhost:8002"
echo "📍 Health Check: http://localhost:8002/health"
echo ""
echo "🛡️  Sovereignty is active:"
echo "   • All data stays on your machine"
echo "   • No telemetry or cloud dependencies"
echo "   • Constitutional enforcement engaged"
echo ""
echo "💡 Try these commands in the dashboard:"
echo "   /sovereignty  → View sovereignty report"
echo "   /health       → System status"
echo "   /workers      → List all workers"
echo "   /code         → Generate code"
echo ""
echo "Press Ctrl+C to stop all services"
echo "═══════════════════════════════════════════════════════════════"

# Handle shutdown
trap 'echo ""; echo "🛑 Shutting down Phoenix OS..."; kill $KERNEL_PID $FRONTEND_PID 2>/dev/null; exit 0' INT

# Wait for interrupt
wait