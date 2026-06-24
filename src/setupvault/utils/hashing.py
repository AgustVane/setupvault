from __future__ import annotations

import hashlib
from pathlib import Path


def hash_file(path: str | Path, algorithm: str = "sha256") -> str:
    """Compute the hex digest of a file.

    Args:
        path: Path to the file.
        algorithm: Hash algorithm (default ``sha256``).

    Returns:
        Hex digest string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If *algorithm* is not supported by ``hashlib``.
    """
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_bytes(data: bytes, algorithm: str = "sha256") -> str:
    """Compute the hex digest of raw bytes."""
    return hashlib.new(algorithm, data).hexdigest()


def hash_string(data: str, algorithm: str = "sha256") -> str:
    """Compute the hex digest of a UTF-8 encoded string."""
    return hashlib.new(algorithm, data.encode("utf-8")).hexdigest()
