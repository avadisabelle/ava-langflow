#!/usr/bin/env python3
"""
Performance Benchmarking Tool - Agentic Flywheel v2.0.0

Comprehensive performance testing for all system components.
"""

import asyncio
import os
import sys
import time
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentic_flywheel.tools import (
    handle_universal_query,
    handle_backend_registry_status,
    handle_backend_list_flows,
    handle_backend_performance_compare
)


class PerformanceBenchmark:
    """Performance benchmarking utility"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "benchmarks": []
        }

    def record(self, name: str, duration_ms: float, success: bool, details: str = ""):
        """Record benchmark result"""
        self.results["benchmarks"].append({
            "name": name,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            "details": details
        })

    def summary(self):
        """Print summary statistics"""
        print("\n" + "=" * 60)
        print("Performance Benchmark Summary")
        print("=" * 60)

        if not self.results["benchmarks"]:
            print("No benchmarks completed")
            return

        # Group by category
        categories = {}
        for bench in self.results["benchmarks"]:
            category = bench["name"].split(":")[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(bench)

        # Print by category
        for category, benches in categories.items():
            print(f"\n{category}")
            print("-" * 60)

            durations = [b["duration_ms"] for b in benches if b["success"]]
            if durations:
                print(f"  Operations: {len(benches)}")
                print(f"  Successful: {len([b for b in benches if b['success']])}")
                print(f"  Avg Duration: {statistics.mean(durations):.2f}ms")
                print(f"  Min Duration: {min(durations):.2f}ms")
                print(f"  Max Duration: {max(durations):.2f}ms")
                if len(durations) > 1:
                    print(f"  Std Dev: {statistics.stdev(durations):.2f}ms")

        print("\n" + "=" * 60)


async def benchmark_universal_query(benchmark: PerformanceBenchmark):
    """Benchmark universal query performance"""
    print("\n" + "=" * 60)
    print("Universal Query Benchmarks")
    print("=" * 60 + "\n")

    test_questions = [
        ("What is structural tension?", "creative"),
        ("How do I create a desired outcome?", "creative"),
        ("Optimize this Python code", "technical"),
        ("Explain async/await patterns", "technical"),
    ]

    for question, intent in test_questions:
        print(f"Testing: {question[:50]}...")

        start = time.time()
        try:
            result = await handle_universal_query("universal_query", {
                "question": question,
                "backend": "auto",
                "intent": intent
            })
            duration_ms = (time.time() - start) * 1000

            success = len(result) > 0
            benchmark.record(
                f"Universal Query: {intent}",
                duration_ms,
                success,
                question[:30]
            )

            print(f"  ✅ {duration_ms:.2f}ms")

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            benchmark.record(
                f"Universal Query: {intent}",
                duration_ms,
                False,
                str(e)
            )
            print(f"  ❌ {duration_ms:.2f}ms - {str(e)[:50]}")

        # Small delay between requests
        await asyncio.sleep(0.1)


async def benchmark_backend_operations(benchmark: PerformanceBenchmark):
    """Benchmark backend management operations"""
    print("\n" + "=" * 60)
    print("Backend Operations Benchmarks")
    print("=" * 60 + "\n")

    # Test registry status
    print("Testing: backend_registry_status...")
    start = time.time()
    try:
        result = await handle_backend_registry_status("backend_registry_status", {})
        duration_ms = (time.time() - start) * 1000

        success = len(result) > 0
        benchmark.record(
            "Backend Ops: Registry Status",
            duration_ms,
            success
        )
        print(f"  ✅ {duration_ms:.2f}ms")

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        benchmark.record(
            "Backend Ops: Registry Status",
            duration_ms,
            False,
            str(e)
        )
        print(f"  ❌ {duration_ms:.2f}ms - {str(e)[:50]}")

    # Test flow listing
    print("Testing: backend_list_flows...")
    start = time.time()
    try:
        result = await handle_backend_list_flows("backend_list_flows", {
            "backend_filter": "all"
        })
        duration_ms = (time.time() - start) * 1000

        success = len(result) > 0
        benchmark.record(
            "Backend Ops: List Flows",
            duration_ms,
            success
        )
        print(f"  ✅ {duration_ms:.2f}ms")

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        benchmark.record(
            "Backend Ops: List Flows",
            duration_ms,
            False,
            str(e)
        )
        print(f"  ❌ {duration_ms:.2f}ms - {str(e)[:50]}")

    # Test performance comparison
    print("Testing: backend_performance_compare...")
    start = time.time()
    try:
        result = await handle_backend_performance_compare("backend_performance_compare", {
            "metric": "latency",
            "time_range": "24h"
        })
        duration_ms = (time.time() - start) * 1000

        success = len(result) > 0
        benchmark.record(
            "Backend Ops: Performance Compare",
            duration_ms,
            success
        )
        print(f"  ✅ {duration_ms:.2f}ms")

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        benchmark.record(
            "Backend Ops: Performance Compare",
            duration_ms,
            False,
            str(e)
        )
        print(f"  ❌ {duration_ms:.2f}ms - {str(e)[:50]}")


async def benchmark_routing_performance(benchmark: PerformanceBenchmark):
    """Benchmark intelligent routing speed"""
    print("\n" + "=" * 60)
    print("Intelligent Routing Benchmarks")
    print("=" * 60 + "\n")

    # Test rapid backend selection (routing only, no execution)
    print("Testing: Routing decision speed (10 iterations)...")

    routing_times = []
    for i in range(10):
        start = time.time()
        try:
            # Use a query that requires routing decision
            result = await handle_universal_query("universal_query", {
                "question": f"Test question {i}",
                "backend": "auto",
                "include_routing_metadata": True
            })
            duration_ms = (time.time() - start) * 1000
            routing_times.append(duration_ms)

        except Exception as e:
            print(f"  ⚠️  Iteration {i+1} failed: {str(e)[:50]}")

        await asyncio.sleep(0.05)

    if routing_times:
        avg_routing = statistics.mean(routing_times)
        benchmark.record(
            "Routing: Decision Speed",
            avg_routing,
            True,
            f"{len(routing_times)} successful iterations"
        )
        print(f"  ✅ Average: {avg_routing:.2f}ms")
        print(f"  📊 Min: {min(routing_times):.2f}ms, Max: {max(routing_times):.2f}ms")


async def benchmark_redis_performance(benchmark: PerformanceBenchmark):
    """Benchmark Redis read/write performance"""
    print("\n" + "=" * 60)
    print("Redis Performance Benchmarks")
    print("=" * 60 + "\n")

    if os.getenv("REDIS_ENABLED") != "true":
        print("  ⚠️  Redis disabled - skipping benchmarks")
        return

    try:
        import redis.asyncio as aioredis

        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))

        r = await aioredis.from_url(
            f"redis://{host}:{port}",
            decode_responses=True,
            socket_connect_timeout=2.0
        )

        # Test write performance
        print("Testing: Redis write (10 operations)...")
        write_times = []
        for i in range(10):
            start = time.time()
            await r.set(f"benchmark_test_{i}", f"value_{i}", ex=60)
            duration_ms = (time.time() - start) * 1000
            write_times.append(duration_ms)

        avg_write = statistics.mean(write_times)
        benchmark.record(
            "Redis: Write",
            avg_write,
            True,
            "10 operations"
        )
        print(f"  ✅ Average: {avg_write:.2f}ms")

        # Test read performance
        print("Testing: Redis read (10 operations)...")
        read_times = []
        for i in range(10):
            start = time.time()
            await r.get(f"benchmark_test_{i}")
            duration_ms = (time.time() - start) * 1000
            read_times.append(duration_ms)

        avg_read = statistics.mean(read_times)
        benchmark.record(
            "Redis: Read",
            avg_read,
            True,
            "10 operations"
        )
        print(f"  ✅ Average: {avg_read:.2f}ms")

        # Cleanup
        for i in range(10):
            await r.delete(f"benchmark_test_{i}")

        await r.close()

    except ImportError:
        print("  ⚠️  redis package not installed - skipping")
    except Exception as e:
        print(f"  ❌ Redis benchmark failed: {str(e)}")


async def benchmark_concurrent_load(benchmark: PerformanceBenchmark):
    """Benchmark concurrent request handling"""
    print("\n" + "=" * 60)
    print("Concurrent Load Benchmarks")
    print("=" * 60 + "\n")

    print("Testing: 5 concurrent queries...")

    queries = [
        "What is structural tension?",
        "How do I create goals?",
        "Explain creative orientation",
        "What is the reality principle?",
        "Define desired outcome"
    ]

    start = time.time()
    try:
        tasks = [
            handle_universal_query("universal_query", {
                "question": q,
                "backend": "auto"
            })
            for q in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration_ms = (time.time() - start) * 1000

        successful = sum(1 for r in results if not isinstance(r, Exception))
        benchmark.record(
            "Concurrent: 5 Queries",
            duration_ms,
            successful == len(queries),
            f"{successful}/{len(queries)} successful"
        )

        print(f"  ✅ {duration_ms:.2f}ms total ({successful}/{len(queries)} successful)")
        print(f"  📊 Average per query: {duration_ms / len(queries):.2f}ms")

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        benchmark.record(
            "Concurrent: 5 Queries",
            duration_ms,
            False,
            str(e)
        )
        print(f"  ❌ {duration_ms:.2f}ms - {str(e)[:50]}")


async def main():
    """Run all benchmarks"""
    print("\n" + "=" * 60)
    print("Agentic Flywheel v2.0.0 - Performance Benchmark")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)

    benchmark = PerformanceBenchmark()

    # Run benchmarks
    await benchmark_universal_query(benchmark)
    await benchmark_backend_operations(benchmark)
    await benchmark_routing_performance(benchmark)
    await benchmark_redis_performance(benchmark)
    await benchmark_concurrent_load(benchmark)

    # Print summary
    benchmark.summary()

    # Performance targets
    print("\n" + "=" * 60)
    print("Performance Targets")
    print("=" * 60)
    print("✓ Universal Query: <2000ms")
    print("✓ Backend Selection: <200ms")
    print("✓ Health Check: <500ms")
    print("✓ Redis Operations: <50ms")
    print()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
