#!/usr/bin/env python3
"""
upgrade_rezcoder.py — RezCoder Self-Upgrade Protocol
=====================================================

The ultimate meta-test: RezCoder reviews and fixes its own source code.

Flow:
  1. Initialize RezCoder worker
  2. Review workers/rezcoder.py (itself)
  3. Apply auto-fixes above confidence threshold
  4. Re-review to verify improvement
  5. Generate upgrade report
  6. Also review the core engine (code-worker.py)

Usage:
    cd D:/Rezonic_Agentic/apps/phoenix-kernel
    python upgrade_rezcoder.py
    python upgrade_rezcoder.py --also-fix-engine
    python upgrade_rezcoder.py --confidence 0.9 --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ensure phoenix-kernel is on the path
KERNEL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(KERNEL_DIR))


async def run_self_upgrade(
    confidence: float = 0.7,
    dry_run: bool = False,
    also_fix_engine: bool = False,
) -> dict:
    """Run the full RezCoder self-upgrade pipeline."""

    print("🦎 REZCODER SELF-UPGRADE PROTOCOL")
    print("=" * 55)

    # ── Import & initialize ──────────────────────────────
    from workers.rezcoder import RezCoderWorker

    rezcoder = RezCoderWorker()
    await rezcoder.initialize()

    targets = [Path("workers/rezcoder.py")]
    if also_fix_engine:
        engine_path = Path("code-worker.py")
        if engine_path.exists():
            targets.append(engine_path)
        else:
            print(f"  ⚠️  Engine file not found: {engine_path}")

    all_reports: dict[str, dict] = {}

    for target_path in targets:
        if not target_path.exists():
            print(f"\n❌ File not found: {target_path}")
            continue

        print(f"\n{'─' * 55}")
        print(f"📁 Target: {target_path}")
        print(f"{'─' * 55}")

        # ── Step 1: Review before ────────────────────────
        print("\n🔍 Step 1: Reviewing current code...")
        review_before = await rezcoder.execute(
            "review", file_path=str(target_path)
        )

        if not review_before.get("success"):
            print(f"  ❌ Review failed: {review_before.get('error')}")
            continue

        print(f"   Health Score : {review_before['health_score']}/100")
        print(f"   Issues Found : {review_before['total_issues']}")
        print(f"   Errors       : {review_before['error_count']}")
        print(f"   Warnings     : {review_before['warning_count']}")

        if review_before.get("issues"):
            print("\n   Top Issues:")
            for issue in review_before["issues"][:5]:
                line = issue.get("line", "—")
                sev = issue.get("severity", "?")
                msg = issue.get("message", "")[:65]
                print(f"     {sev.upper():>8} L{line}: {msg}")

        if review_before.get("strengths"):
            print("\n   Strengths:")
            for s in review_before["strengths"][:5]:
                print(f"     {s}")

        # ── Step 2: Apply fixes ──────────────────────────
        print(f"\n🔧 Step 2: Applying auto-fixes "
              f"(confidence >= {confidence:.0%})...")

        fix_result = await rezcoder.execute(
            "fix",
            file_path=str(target_path),
            confidence=confidence,
            backup=True,
            dry_run=dry_run,
        )

        if fix_result.get("fixes_applied"):
            count = len(fix_result["fixes_applied"])
            print(f"   ✅ Applied {count} fix(es):")
            for fix in fix_result["fixes_applied"]:
                print(f"      • {fix[:75]}")
        else:
            print("   ⚠️  No fixes applied "
                  "(below threshold or code already clean)")

        if fix_result.get("fixes_skipped"):
            count = len(fix_result["fixes_skipped"])
            print(f"   ⏭️  Skipped {count} fix(es)")

        if fix_result.get("backup_path"):
            print(f"   💾 Backup: {fix_result['backup_path']}")

        # ── Step 3: Re-review after ─────────────────────
        print("\n✅ Step 3: Verifying after fixes...")
        review_after = await rezcoder.execute(
            "review", file_path=str(target_path)
        )

        if review_after.get("success"):
            print(f"   New Health   : {review_after['health_score']}/100")
            print(f"   Remaining    : {review_after['total_issues']} issues")
        else:
            print(f"   ⚠️  Post-fix review failed: "
                  f"{review_after.get('error')}")
            review_after = review_before  # fallback

        # ── Step 4: Generate report ─────────────────────
        print("\n📄 Step 4: Generating upgrade report...")
        report = await rezcoder.execute(
            "report", file_path=str(target_path)
        )

        if report.get("report_path"):
            print(f"   Report: {report['report_path']}")
        else:
            print(f"   ⚠️  Report generation failed")

        # ── Per-file summary ────────────────────────────
        before_score = review_before.get("health_score", 0)
        after_score = review_after.get("health_score", 0)
        delta = after_score - before_score

        all_reports[str(target_path)] = {
            "before_health": before_score,
            "after_health": after_score,
            "delta": delta,
            "fixes_applied": fix_result.get("fixes_applied", []),
            "fixes_skipped": fix_result.get("fixes_skipped", []),
            "issues_before": review_before.get("total_issues", 0),
            "issues_after": review_after.get("total_issues", 0),
            "report_path": report.get("report_path"),
        }

    # ── Final summary ────────────────────────────────────
    print(f"\n{'═' * 55}")
    print("📊 UPGRADE SUMMARY")
    print(f"{'═' * 55}")

    for path, data in all_reports.items():
        print(f"\n  📄 {path}")
        print(f"     Before : {data['before_health']}/100")
        print(f"     After  : {data['after_health']}/100")
        sign = "+" if data["delta"] >= 0 else ""
        print(f"     Delta  : {sign}{data['delta']:.1f}")
        print(f"     Fixes  : {len(data['fixes_applied'])}")

    total_delta = sum(d["delta"] for d in all_reports.values())
    total_fixes = sum(
        len(d["fixes_applied"]) for d in all_reports.values()
    )
    print(f"\n  🏁 Total improvement: {total_delta:+.1f} points")
    print(f"  🔧 Total fixes:      {total_fixes}")
    if dry_run:
        print("  ⏸️  DRY RUN — no files were modified")
    print(f"{'═' * 55}")

        # ── Worker stats ─────────────────────────────────────
    health = await rezcoder.health_check()
    stats = health.get('stats', {})
    reviews = stats.get('reviews', 0)
    fixes = stats.get('fixes', 0)
    issues = stats.get('total_issues', 0)
    print(f"\n  🦎 Worker stats: "
          f"{reviews} reviews, {fixes} fixes, {issues} issues found")

    return all_reports


def main() -> int:
    """CLI entry point for self-upgrade."""
    parser = argparse.ArgumentParser(
        description="RezCoder Self-Upgrade Protocol",
    )
    parser.add_argument(
        "--confidence", type=float, default=0.7,
        help="Fix confidence threshold (default: 0.7)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Analyze without writing changes",
    )
    parser.add_argument(
        "--also-fix-engine", action="store_true",
        help="Also review and fix code-worker.py",
    )
    args = parser.parse_args()

    reports = asyncio.run(run_self_upgrade(
        confidence=args.confidence,
        dry_run=args.dry_run,
        also_fix_engine=args.also_fix_engine,
    ))

    # Save JSON report
    report_file = Path("rezcoder_upgrade_report.json")
    report_file.write_text(
        json.dumps(reports, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\n📁 JSON report: {report_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
