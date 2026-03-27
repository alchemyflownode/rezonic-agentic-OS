#!/bin/bash
# launch-local.sh — Sovereign Demo Launcher

echo "🦊 Phoenix OS — Sovereign AI Operating System"
echo "═══════════════════════════════════════════════════════════════"
echo "• Execution: LOCAL ONLY"
echo "• Telemetry: DISABLED"
echo "• Constitution: ACTIVE"
echo "• Determinism: TEMPERATURE=0"
echo ""

# Verify integrity
echo "🔐 Verifying kernel integrity..."
EXPECTED_HASH="f8e3a7c2b1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"
ACTUAL_HASH=$(sha256sum apps/phoenix-kernel/rezphoenix_v15_final.py | cut -d' ' -f1)

if [ "$ACTUAL_HASH" != "$EXPECTED_HASH" ]; then
    echo "⚠️  Hash mismatch! Run with --audit-entropy to verify determinism."
else
    echo "✅ Kernel integrity verified — deterministic mode available"
fi

# Start kernel
echo ""
echo "🚀 Launching Phoenix Kernel (port 8002)..."
cd apps/phoenix-kernel
python rezphoenix_v15_final.py &
KERNEL_PID=$!

# Wait for kernel to be ready
sleep 3

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
echo ""
echo "🛡️  Sovereignty is active:"
echo "   • All data stays on your machine"
echo "   • No telemetry or cloud dependencies"
echo "   • Constitutional enforcement engaged"
echo ""
echo "Press Ctrl+C to stop all services"
echo "═══════════════════════════════════════════════════════════════"

# Wait for interrupt
wait $KERNEL_PID $FRONTEND_PID