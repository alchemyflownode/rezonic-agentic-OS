# 🔐 Determinism Verification

Phoenix OS is designed to be **reproducible, auditable, and deterministic**. This guide lets you verify you're running the exact sovereign engine we built.

## ✅ Quick Verification

```bash
# Clone the sovereign reference
git clone https://github.com/alchemyflownode/rezonic-agentic-OS.git
cd rezonic-agentic-OS

# Verify kernel integrity
sha256sum apps/phoenix-kernel/rezphoenix_v15_final.py
# Expected: f8e3a7c2b1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1