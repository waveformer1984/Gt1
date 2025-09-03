#!/usr/bin/env python3
"""
Process Artifact Data (f408)

Scans the repository, gathers file metadata and checksums, and writes
an artifact JSON file at cursor/process-artifact-data-f408.json.

- Excludes common build/IDE caches and VCS directories
- Computes sha256 checksums
- Captures lightweight text preview for small text files
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_EXCLUDES = {
    ".git",
    "bin",
    "build",
    "dist",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
}

ARTIFACT_FILENAME = "process-artifact-data-f408.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate process artifact data (f408)")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("."),
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output JSON path (default: cursor/{ARTIFACT_FILENAME})",
    )
    parser.add_argument(
        "--max-preview-bytes",
        type=int,
        default=2048,
        help="Max preview bytes to include for text files",
    )
    return parser.parse_args()


def is_excluded(path: Path, base_dir: Path) -> bool:
    try:
        relative = path.relative_to(base_dir)
    except ValueError:
        # Outside base directory
        return True

    parts = set(relative.parts)
    return any(ex in parts for ex in DEFAULT_EXCLUDES)


def compute_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def collect_file_metadata(file_path: Path, base_dir: Path, max_preview_bytes: int) -> Dict:
    relative_path = str(file_path.relative_to(base_dir))
    stat = file_path.stat()

    # best-effort content type
    content_type, _ = mimetypes.guess_type(file_path.name)

    # preview small text files
    preview: Optional[str] = None
    try:
        if content_type and content_type.startswith("text") and stat.st_size <= max_preview_bytes:
            preview = file_path.read_text(errors="replace")[:max_preview_bytes]
    except Exception:
        preview = None

    return {
        "path": relative_path,
        "size_bytes": stat.st_size,
        "modified_utc": datetime.utcfromtimestamp(stat.st_mtime).replace(tzinfo=timezone.utc).isoformat(),
        "sha256": compute_sha256(file_path),
        "content_type": content_type or "application/octet-stream",
        "preview": preview,
    }


def iter_files(base_dir: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(base_dir):
        root_path = Path(root)
        # prune excluded directories
        dirs[:] = [d for d in dirs if not is_excluded(root_path / d, base_dir)]
        for name in files:
            file_path = root_path / name
            if is_excluded(file_path, base_dir):
                continue
            yield file_path


def generate_artifact(base_dir: Path, max_preview_bytes: int) -> Dict:
    files: List[Dict] = []
    for file_path in iter_files(base_dir):
        try:
            files.append(collect_file_metadata(file_path, base_dir, max_preview_bytes))
        except Exception as exc:
            files.append({
                "path": str(file_path.relative_to(base_dir)),
                "error": str(exc),
            })
    artifact = {
        "schema": "cursor/process-artifact-data-f408",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "base_dir": str(base_dir.resolve()),
        "num_files": len(files),
        "files": files,
    }
    return artifact


def main() -> None:
    args = parse_args()
    base_dir = args.base_dir.resolve()

    output_path = args.output
    if output_path is None:
        output_path = base_dir / "cursor" / ARTIFACT_FILENAME

    output_path.parent.mkdir(parents=True, exist_ok=True)

    artifact = generate_artifact(base_dir=base_dir, max_preview_bytes=args.max_preview_bytes)

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(artifact, fh, ensure_ascii=False, indent=2)

    print(f"Wrote artifact: {output_path}")
    print(f"Files indexed: {artifact['num_files']}")


if __name__ == "__main__":
    main()