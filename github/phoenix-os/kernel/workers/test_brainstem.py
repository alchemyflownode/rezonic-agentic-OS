import asyncio
from context_bus import ContextBus
from brain_worker import BrainWorker
from analyst_worker import AnalystWorker
from constitutional_council_fixed import ConstitutionalCouncilWorker
from memory_worker import MemoryWorker

async def main():
    bus = ContextBus()
    await bus.initialize()

    brain = BrainWorker(bus)
    analyst = AnalystWorker(bus)
    council = ConstitutionalCouncilWorker(bus)
    memory = MemoryWorker(bus)

    await brain.initialize()
    await analyst.initialize()
    await council.initialize()
    await memory.initialize()

    # Start the heartbeats
    asyncio.create_task(analyst.run_loop())
    asyncio.create_task(council.run_loop())
    asyncio.create_task(memory.run_loop())

    await asyncio.sleep(0.5)

    # JOHN SPEAKS
    print("--- JOHN SENDS THOUGHT ---")
    await brain.execute("Check BTC momentum", asset="BTC")
    
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
