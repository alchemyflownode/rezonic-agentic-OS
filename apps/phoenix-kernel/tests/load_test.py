# tests/load_test.py
"""Load testing for Phoenix Kernel"""

import asyncio
import time
import aiohttp
from typing import List, Dict
import statistics

class LoadTester:
    """Load test the Phoenix Kernel API"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.results = []
    
    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: str) -> float:
        """Test a single endpoint and return response time"""
        start = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}", timeout=5) as resp:
                await resp.text()
                return time.time() - start
        except Exception as e:
            print(f"Error: {e}")
            return -1
    
    async def run_concurrent_test(self, endpoint: str, concurrency: int = 10) -> Dict:
        """Run concurrent requests to an endpoint"""
        async with aiohttp.ClientSession() as session:
            tasks = [self.test_endpoint(session, endpoint) for _ in range(concurrency)]
            times = await asyncio.gather(*tasks)
            
            valid_times = [t for t in times if t > 0]
            
            return {
                "endpoint": endpoint,
                "concurrency": concurrency,
                "successful": len(valid_times),
                "failed": concurrency - len(valid_times),
                "avg_response_ms": statistics.mean(valid_times) * 1000 if valid_times else 0,
                "min_response_ms": min(valid_times) * 1000 if valid_times else 0,
                "max_response_ms": max(valid_times) * 1000 if valid_times else 0,
                "p95_ms": statistics.quantiles(valid_times, n=20)[18] * 1000 if len(valid_times) >= 20 else 0
            }
    
    async def run_load_test(self, concurrency: int = 50, iterations: int = 5) -> List[Dict]:
        """Run comprehensive load test"""
        endpoints = ["/health", "/workers/list", "/swarm/manifest"]
        results = []
        
        for endpoint in endpoints:
            print(f"Testing {endpoint} with concurrency {concurrency}...")
            endpoint_results = []
            
            for i in range(iterations):
                result = await self.run_concurrent_test(endpoint, concurrency)
                endpoint_results.append(result)
                print(f"  Iteration {i+1}: {result['avg_response_ms']:.2f}ms avg, {result['successful']}/{result['concurrency']} successful")
            
            # Average results
            avg_result = {
                "endpoint": endpoint,
                "concurrency": concurrency,
                "avg_response_ms": statistics.mean([r["avg_response_ms"] for r in endpoint_results]),
                "success_rate": statistics.mean([r["successful"] / r["concurrency"] for r in endpoint_results]) * 100
            }
            results.append(avg_result)
        
        return results
    
    async def stress_test(self, duration_seconds: int = 30, rate: int = 10) -> Dict:
        """Continuous load for stress testing"""
        print(f"Running stress test for {duration_seconds}s at {rate} req/s...")
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            requests = 0
            successes = 0
            failures = 0
            response_times = []
            
            async def worker():
                nonlocal requests, successes, failures
                while time.time() - start_time < duration_seconds:
                    start = time.time()
                    try:
                        async with session.get(f"{self.base_url}/health", timeout=2) as resp:
                            await resp.text()
                            response_times.append(time.time() - start)
                            successes += 1
                    except:
                        failures += 1
                    requests += 1
                    await asyncio.sleep(1 / rate)
            
            # Run workers
            tasks = [worker() for _ in range(rate)]
            await asyncio.gather(*tasks)
            
            return {
                "duration": duration_seconds,
                "target_rate": rate,
                "total_requests": requests,
                "successful": successes,
                "failed": failures,
                "success_rate": (successes / requests) * 100 if requests else 0,
                "avg_response_ms": statistics.mean(response_times) * 1000 if response_times else 0,
                "max_response_ms": max(response_times) * 1000 if response_times else 0
            }

async def main():
    """Run load tests"""
    print("=" * 60)
    print("🔥 LOAD TESTING PHOENIX KERNEL 🔥")
    print("=" * 60)
    
    tester = LoadTester()
    
    # Test 1: Concurrent tests
    print("\n📊 Test 1: Concurrent Requests")
    results = await tester.run_load_test(concurrency=20, iterations=3)
    for r in results:
        print(f"  {r['endpoint']}: {r['avg_response_ms']:.2f}ms avg, {r['success_rate']:.1f}% success")
    
    # Test 2: Stress test
    print("\n📊 Test 2: Stress Test")
    stress = await tester.stress_test(duration_seconds=10, rate=20)
    print(f"  {stress['total_requests']} requests, {stress['success_rate']:.1f}% success")
    print(f"  Avg response: {stress['avg_response_ms']:.2f}ms")
    print(f"  Max response: {stress['max_response_ms']:.2f}ms")
    
    print("\n✅ Load testing complete!")

if __name__ == "__main__":
    asyncio.run(main())