"""Hashing utilities for file integrity verification."""

import hashlib
from typing import BinaryIO


def compute_sha256(file: BinaryIO) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file: File-like object

    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.sha256()

    # Read file in chunks to handle large files
    while chunk := file.read(8192):
        hasher.update(chunk)

    return hasher.hexdigest()


def verify_sha256(file: BinaryIO, expected_hash: str) -> bool:
    """
    Verify SHA-256 hash of a file.

    Args:
        file: File-like object
        expected_hash: Expected hash value

    Returns:
        True if hash matches
    """
    actual_hash = compute_sha256(file)
    return actual_hash.lower() == expected_hash.lower()
