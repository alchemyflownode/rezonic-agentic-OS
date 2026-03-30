#!/usr/bin/env python3
"""Test RezCoder standalone"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

async def test():
    print("🦎 Testing RezCoder...")
    
    from workers.rezcoder import RezCoderWorker
    
    rezcoder = RezCoderWorker()
    await rezcoder.initialize()
    
    # Test health
    health = await rezcoder.execute("health")
    print(f"Health: {health['stats']}")
    
    # Test review on itself
    result = await rezcoder.execute("review", file_path="workers/rezcoder.py")
    print(f"Review: Health={result['health_score']}/100, Issues={result['total_issues']}")
    
    print("✅ RezCoder works!")

if __name__ == "__main__":
    asyncio.run(test())