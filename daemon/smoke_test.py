"""Onboarding smoke test.

Per AI_IT_Team_Setup_Checklist Phase 2. Probes the local dev environment and
writes a structured PASS/FAIL report to `environment_awareness.yaml` inside
the Hermes profile directory.

The Swarm Manager (per the SOUL.md Logical Processing gate) MUST read this
file before drafting any plan, so it knows what the Mac Mini can actually
execute.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import yaml  # type: ignore

CHECKS: list[tuple[str, str, Callable[[], tuple[bool, str]]]] = [
    # (id, label, runner returning (ok, version_or_detail))
    ("git",       "git --version",        lambda: _run(["git", "--version"])),
    ("playwright","npx playwright",       lambda: _run(["npx", "playwright", "--version"])),
    ("railway",   "railway status",       lambda: _run(["railway", "status"], allow_fail=True)),
    ("github_cli","gh auth status",       lambda: _run(["gh", "auth", "status"], allow_fail=True)),
    ("node",      "node --version",       lambda: _run(["node", "--version"])),
    ("python",    "python --version",     lambda: _run([sys.executable, "--version"])),
]


def _run(cmd: list[str], allow_fail: bool = False) -> tuple[bool, str]:
    if shutil.which(cmd[0]) is None and cmd[0] not in ("python",):
        return False, f"{cmd[0]}: not on PATH"
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15, check=False
        )
    except subprocess.TimeoutExpired:
        return False, f"{cmd[0]}: timeout"
    out = (r.stdout or r.stderr).strip().splitlines()
    first = out[0] if out else ""
    if r.returncode == 0 or allow_fail:
        return True, first
    return False, first or f"exit {r.returncode}"


def run_checks() -> dict:
    results: dict[str, dict] = {}
    overall_ok = True
    for key, label, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001
            ok, detail = False, f"exception: {e}"
        if not ok:
            overall_ok = False
        results[key] = {
            "label": label,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    return {"overall": "PASS" if overall_ok else "FAIL", "checks": results}


def main() -> int:
    p = argparse.ArgumentParser(prog="smoke_test")
    p.add_argument(
        "--profile-dir",
        required=True,
        help="Path to the Hermes profile dir, e.g. ~/.hermes/profiles/marketing",
    )
    p.add_argument(
        "--emit-json",
        action="store_true",
        help="Print the result JSON to stdout in addition to writing the file",
    )
    args = p.parse_args()

    profile_dir = Path(args.profile_dir).expanduser()
    profile_dir.mkdir(parents=True, exist_ok=True)
    target = profile_dir / "environment_awareness.yaml"

    report = run_checks()
    with target.open("w", encoding="utf-8") as f:
        yaml.safe_dump(report, f, sort_keys=False)
    if args.emit_json:
        print(json.dumps(report, indent=2))
    print(f"wrote {target}  overall={report['overall']}")
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
