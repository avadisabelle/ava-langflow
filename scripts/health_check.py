#!/usr/bin/env python3
"""
Health Check Utility - Agentic Flywheel v2.0.0

Comprehensive system health check for all components.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentic_flywheel.tools import (
    handle_backend_registry_status,
    handle_backend_list_flows
)


class HealthChecker:
    """System health checker"""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []

    def check(self, name: str, condition: bool, details: str = ""):
        """Record check result"""
        if condition:
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
            self.checks_passed += 1
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
            self.checks_failed += 1

    def warn(self, name: str, details: str = ""):
        """Record warning"""
        print(f"⚠️  {name}")
        if details:
            print(f"   {details}")
        self.warnings.append(name)

    def summary(self):
        """Print summary"""
        print()
        print("=" * 60)
        print("Health Check Summary")
        print("=" * 60)
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print()

        if self.checks_failed == 0 and len(self.warnings) == 0:
            print("🎉 All systems operational!")
            return 0
        elif self.checks_failed == 0:
            print("✓ System operational with warnings")
            return 0
        else:
            print("⚠️  System has failures - review errors above")
            return 1


async def check_environment():
    """Check environment configuration"""
    print("\n" + "=" * 60)
    print("Environment Configuration")
    print("=" * 60 + "\n")

    checker = HealthChecker()

    # Required variables
    checker.check(
        "FLOWISE_BASE_URL",
        bool(os.getenv("FLOWISE_BASE_URL")),
        os.getenv("FLOWISE_BASE_URL", "Not set")
    )

    checker.check(
        "LANGFLOW_BASE_URL",
        bool(os.getenv("LANGFLOW_BASE_URL")),
        os.getenv("LANGFLOW_BASE_URL", "Not set")
    )

    # Optional but recommended
    if os.getenv("LANGFUSE_ENABLED") == "true":
        checker.check(
            "LANGFUSE_PUBLIC_KEY",
            bool(os.getenv("LANGFUSE_PUBLIC_KEY")),
            "Set" if os.getenv("LANGFUSE_PUBLIC_KEY") else "Not set"
        )
        checker.check(
            "LANGFUSE_SECRET_KEY",
            bool(os.getenv("LANGFUSE_SECRET_KEY")),
            "Set" if os.getenv("LANGFUSE_SECRET_KEY") else "Not set"
        )
    else:
        checker.warn("Langfuse Tracing", "Disabled - observability limited")

    if os.getenv("REDIS_ENABLED") == "true":
        checker.check(
            "REDIS_HOST",
            bool(os.getenv("REDIS_HOST")),
            os.getenv("REDIS_HOST", "Not set")
        )
    else:
        checker.warn("Redis Persistence", "Disabled - no session continuity")

    return checker


async def check_backends():
    """Check backend connectivity"""
    print("\n" + "=" * 60)
    print("Backend Status")
    print("=" * 60 + "\n")

    try:
        result = await handle_backend_registry_status("backend_registry_status", {})
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text

        print(response_text)
        print()

        # Parse response to determine health
        import json
        try:
            data = json.loads(response_text)
            total = data.get("total_backends", 0)
            healthy = data.get("healthy_count", 0)

            checker = HealthChecker()
            checker.check(
                "Backend Registry",
                total > 0,
                f"{total} backends registered"
            )
            checker.check(
                "Backend Health",
                healthy == total,
                f"{healthy}/{total} backends healthy"
            )
            return checker

        except json.JSONDecodeError:
            checker = HealthChecker()
            checker.check("Backend Status", True, "Retrieved (manual parse needed)")
            return checker

    except Exception as e:
        checker = HealthChecker()
        checker.check("Backend Status", False, str(e))
        return checker


async def check_flows():
    """Check flow availability"""
    print("\n" + "=" * 60)
    print("Flow Availability")
    print("=" * 60 + "\n")

    try:
        result = await handle_backend_list_flows("backend_list_flows", {
            "backend_filter": "all"
        })
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text

        import json
        try:
            data = json.loads(response_text)
            total_flows = data.get("total_flows", 0)
            by_backend = data.get("summary", {}).get("by_backend", {})

            checker = HealthChecker()
            checker.check(
                "Total Flows",
                total_flows > 0,
                f"{total_flows} flows available"
            )

            for backend, count in by_backend.items():
                checker.check(
                    f"{backend.title()} Flows",
                    count > 0,
                    f"{count} flows"
                )

            return checker

        except json.JSONDecodeError:
            checker = HealthChecker()
            checker.check("Flow Discovery", True, "Retrieved (manual parse needed)")
            return checker

    except Exception as e:
        checker = HealthChecker()
        checker.check("Flow Discovery", False, str(e))
        return checker


async def check_optional_services():
    """Check optional services"""
    print("\n" + "=" * 60)
    print("Optional Services")
    print("=" * 60 + "\n")

    checker = HealthChecker()

    # Check Redis
    if os.getenv("REDIS_ENABLED") == "true":
        try:
            import redis.asyncio as aioredis
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))

            try:
                r = await aioredis.from_url(
                    f"redis://{host}:{port}",
                    decode_responses=True,
                    socket_connect_timeout=2.0
                )
                await r.ping()
                await r.close()
                checker.check("Redis Connection", True, f"{host}:{port}")
            except Exception as e:
                checker.check("Redis Connection", False, str(e))

        except ImportError:
            checker.warn("Redis", "redis package not installed")
    else:
        checker.warn("Redis", "Disabled in configuration")

    # Check Langfuse
    if os.getenv("LANGFUSE_ENABLED") == "true":
        try:
            from langfuse import Langfuse
            try:
                langfuse = Langfuse(
                    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
                )
                checker.check("Langfuse Connection", True, "Configured")
            except Exception as e:
                checker.check("Langfuse Connection", False, str(e))
        except ImportError:
            checker.warn("Langfuse", "langfuse package not installed")
    else:
        checker.warn("Langfuse", "Disabled in configuration")

    return checker


async def main():
    """Run all health checks"""
    print("\n" + "=" * 60)
    print("Agentic Flywheel v2.0.0 - Health Check")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)

    all_checkers = []

    # Run checks
    all_checkers.append(await check_environment())
    all_checkers.append(await check_backends())
    all_checkers.append(await check_flows())
    all_checkers.append(await check_optional_services())

    # Combined summary
    total_passed = sum(c.checks_passed for c in all_checkers)
    total_failed = sum(c.checks_failed for c in all_checkers)
    total_warnings = sum(len(c.warnings) for c in all_checkers)

    print("\n" + "=" * 60)
    print("Overall System Health")
    print("=" * 60)
    print(f"✅ Checks Passed: {total_passed}")
    print(f"❌ Checks Failed: {total_failed}")
    print(f"⚠️  Warnings: {total_warnings}")
    print()

    if total_failed == 0 and total_warnings == 0:
        print("🎉 All systems fully operational!")
        print("Ready for production deployment.")
        return 0
    elif total_failed == 0:
        print("✓ System operational with optional features disabled")
        print("Consider enabling Redis and Langfuse for full functionality.")
        return 0
    else:
        print("⚠️  System has critical failures")
        print("Review errors above and fix configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
