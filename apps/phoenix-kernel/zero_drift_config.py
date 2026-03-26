# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
﻿# Phoenix Kernel - Zero Drift Configuration
# No pre-loaded memory - builds from scratch

MEMORY_CONFIG = {
    "preload_blueprints": False,      # Don't load existing blueprints
    "start_empty": True,               # Start with empty memory
    "allow_scan": True,                # Allow scanning but don't pre-scan
    "auto_scan_paths": [],             # No auto-scan paths
    "drift_lock": "ZERO_DRIFT_INIT"    # Starting drift lock
}

# Memory will be built organically through:
# 1. User interactions
# 2. Trade executions
# 3. Worker activities
# 4. Constitutional reviews
