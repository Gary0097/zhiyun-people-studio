from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main() -> int:
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("id") != "zhiyun-people-studio" or manifest.get("type") != "app":
        raise SystemExit("plugin.json must identify the People Studio PawApp")
    if manifest.get("qwenpaw_version", {}).get("min") != "2.1.0":
        raise SystemExit("People Studio must retain QwenPaw 2.1.0 compatibility")
    required = [ROOT / "AGENTS.md", ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"]
    if any(not path.is_file() for path in required):
        raise SystemExit("repository governance files are incomplete")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT, check=False,
    )
    if result.returncode:
        return result.returncode
    print("People Studio release gate passed: manifest, governance, and tests are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
