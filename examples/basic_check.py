#!/usr/bin/env python3
"""basic_check.py — Check a shapefile for common issues with geodoctor."""
import subprocess
import sys
from pathlib import Path


def check_file(filepath: str) -> bool:
    """Run geodoctor on a file and return True if no issues found."""
    result = subprocess.run(
        ["geodoctor", "check", filepath, "--format", "json"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"✓ {filepath}: No issues found")
        return True
    else:
        print(f"✗ {filepath}: Issues found")
        print(result.stdout)
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python basic_check.py <file.shp>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not Path(filepath).exists():
        print(f"File not found: {filepath}")
        sys.exit(1)

    ok = check_file(filepath)
    sys.exit(0 if ok else 1)
