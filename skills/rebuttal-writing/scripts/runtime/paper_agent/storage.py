"""Deterministic JSON, immutable run directories, and integrity checks."""

import hashlib
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path


class ValidationError(ValueError):
    """Invalid input or unsafe/unverifiable agent response."""


def digest(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def write_json(path, value):
    Path(path).write_text(json_text(value), encoding="utf-8")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"),
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (ValueError, UnicodeError) as exc:
        raise ValidationError(f"Invalid JSON: {path}") from exc


@contextmanager
def new_directory(target):
    """Publish a complete directory; never reuse or overwrite an existing run."""
    target = Path(target).absolute()
    if target.exists() or target.is_symlink():
        raise ValidationError(f"Output already exists; choose a new directory: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".paper-agent-", dir=target.parent))
    try:
        yield staging
        target.mkdir()
        try:
            for child in staging.iterdir():
                os.rename(child, target / child.name)
        except BaseException:
            shutil.rmtree(target)
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def file_hashes(root):
    return {str(p.relative_to(root)): digest(p.read_bytes())
            for p in sorted(Path(root).rglob("*")) if p.is_file() and p.name != "manifest.json"}


def verify_files(root, manifest):
    root = Path(root).resolve()
    hashes = manifest.get("files")
    if not isinstance(hashes, dict) or not hashes:
        raise ValidationError("Manifest has no file hashes")
    for relative, expected in hashes.items():
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ValidationError("Manifest file hashes must map relative paths to SHA-256 strings")
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValidationError(f"Missing or invalid snapshot: {relative}")
        if digest(path.read_bytes()) != expected:
            raise ValidationError(f"Snapshot changed: {relative}. Prepare a new run.")
