# tests/test_phase1.py
"""Test Phase 1 hardening modules"""

import sys
sys.path.insert(0, '.')

def test_decorators():
    from workers.decorators import handle_errors, with_timeout, log_execution
    print("✅ decorators imported")

def test_logging():
    from logging_config import setup_logging, get_logger
    print("✅ logging_config imported")

def test_backup():
    from workers.backup_worker import BackupWorker
    print("✅ backup_worker imported")

def test_shutdown():
    from graceful_shutdown import GracefulShutdown
    print("✅ graceful_shutdown imported")

if __name__ == "__main__":
    print("🧪 Testing Phase 1 Hardening Modules...")
    test_decorators()
    test_logging()
    test_backup()
    test_shutdown()
    print("\n🎉 Phase 1 complete! All modules ready.")