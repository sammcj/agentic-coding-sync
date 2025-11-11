"""Rename detection for agentic-sync."""

from dataclasses import dataclass
from pathlib import Path

from .files import compute_checksum


@dataclass
class RenameCandidate:
    """A potential file rename."""

    old_path: str
    new_path: str
    checksum: str
    confidence: float  # 1.0 = exact match


def detect_renames(
    deleted_files: dict[str, str],  # relpath -> checksum
    new_files: dict[str, Path],  # relpath -> full path
    similarity_threshold: float = 1.0,
) -> list[RenameCandidate]:
    """
    Detect potential file renames by matching checksums.

    Args:
        deleted_files: Dict of deleted file relpaths to checksums
        new_files: Dict of new file relpaths to full paths
        similarity_threshold: Minimum similarity (default: 1.0 = exact match only)

    Returns:
        List of rename candidates
    """
    candidates = []

    # Build checksum map for new files
    new_checksums = {}
    for relpath, full_path in new_files.items():
        try:
            checksum = compute_checksum(full_path)
            new_checksums[relpath] = checksum
        except OSError:
            continue

    # Find matches
    for deleted_path, deleted_checksum in deleted_files.items():
        for new_path, new_checksum in new_checksums.items():
            if deleted_checksum == new_checksum:
                # Exact match
                candidate = RenameCandidate(
                    old_path=deleted_path,
                    new_path=new_path,
                    checksum=deleted_checksum,
                    confidence=1.0,
                )
                candidates.append(candidate)

    return candidates


def apply_rename(
    old_path: Path, new_path: Path, dest_base: Path, dest_is_source: bool
) -> tuple[Path, Path]:
    """
    Calculate source and destination paths for applying a rename.

    Args:
        old_path: Old relative path
        new_path: New relative path
        dest_base: Base path for destination
        dest_is_source: True if destination is source (vs target)

    Returns:
        Tuple of (source, dest) paths
    """
    # For rename, we delete old and the new file will be synced normally
    old_full = dest_base / old_path
    return old_full, dest_base / new_path
