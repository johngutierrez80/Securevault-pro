#!/usr/bin/env python3
"""
Pipeline demo helper for educational scenarios.

This script applies and reverts controlled changes that intentionally fail CI/CD
checks in a demo branch. It is designed for classroom presentations only.

Usage examples:
  python scripts/pipeline-demo/pipeline_demo.py apply test-fail
  python scripts/pipeline-demo/pipeline_demo.py revert test-fail
  python scripts/pipeline-demo/pipeline_demo.py status
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = REPO_ROOT / "scripts" / "pipeline-demo" / ".pipeline_demo_state.json"

SCENARIOS = {
    "test-fail": {
        "file": REPO_ROOT / "servicios" / "auth-service" / "tests" / "test_security_and_jwt.py",
        "find": "    assert verify_password(password, hashed) is True\n",
        "replace": "    assert verify_password(password, hashed) is False  # demo: intentional failure\n",
        "description": "Forces a unit test failure in auth-service.",
    },
    "sast-fail": {
        "file": REPO_ROOT / "servicios" / "vault-service" / "app" / "core" / "security.py",
        "append": (
            "\n\n# demo: intentionally insecure snippet for SAST pipeline demonstration\n"
            "import pickle\n\n"
            "def dangerous_deserialize(data: bytes):\n"
            "    return pickle.loads(data)\n"
        ),
        "description": "Adds an insecure pattern likely to be flagged by SAST tools.",
    },
    "healthcheck-fail": {
        "file": REPO_ROOT / "servicios" / "auth-service" / "Dockerfile",
        "find": (
            "HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD "
            "python -c \"import socket; s=socket.socket(); s.settimeout(2); "
            "s.connect(('127.0.0.1', 8001)); s.close()\"\n"
        ),
        "replace": (
            "HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD "
            "python -c \"import time; time.sleep(10); raise SystemExit(1)\"\n"
        ),
        "description": "Forces container healthcheck failure for deploy demo.",
    },
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_state() -> Dict[str, dict]:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: Dict[str, dict]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def apply_scenario(name: str) -> None:
    spec = SCENARIOS[name]
    path = spec["file"]
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    text = path.read_text(encoding="utf-8")
    state = load_state()
    if name in state:
        raise SystemExit(f"Scenario '{name}' already applied. Revert it first.")

    original_text = text

    if "append" in spec:
        if spec["append"] in text:
            raise SystemExit("Append snippet already exists in file.")
        text = text + spec["append"]
    else:
        find = spec["find"]
        replace = spec["replace"]
        if find not in text:
            raise SystemExit(
                "Expected source text was not found. File may have changed; aborting safely."
            )
        text = text.replace(find, replace, 1)

    state[name] = {
        "file": str(path),
        "original_sha": sha256_text(original_text),
        "original_text": original_text,
    }
    save_state(state)
    path.write_text(text, encoding="utf-8")
    print(f"Applied scenario: {name}")
    print(f"Changed file: {path}")


def revert_scenario(name: str) -> None:
    state = load_state()
    if name not in state:
        raise SystemExit(f"Scenario '{name}' is not currently applied.")

    entry = state[name]
    path = Path(entry["file"])
    if not path.exists():
        raise SystemExit(f"Cannot revert; file missing: {path}")

    original_text = entry["original_text"]
    path.write_text(original_text, encoding="utf-8")

    del state[name]
    save_state(state)
    print(f"Reverted scenario: {name}")
    print(f"Restored file: {path}")


def show_status() -> None:
    state = load_state()
    if not state:
        print("No scenarios currently applied.")
        return
    print("Applied scenarios:")
    for name, entry in state.items():
        print(f"- {name}: {entry['file']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Educational pipeline demo helper")
    parser.add_argument("action", choices=["apply", "revert", "status"])
    parser.add_argument("scenario", nargs="?", choices=sorted(SCENARIOS.keys()))
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.action == "status":
        show_status()
        return

    if not args.scenario:
        raise SystemExit("Scenario is required for apply/revert actions.")

    if args.action == "apply":
        apply_scenario(args.scenario)
    elif args.action == "revert":
        revert_scenario(args.scenario)


if __name__ == "__main__":
    main()
