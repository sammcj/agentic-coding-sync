"""Special file handling for agentic-sync."""

import json
from pathlib import Path


def extract_json_keys(
    source_file: Path, include_keys: list[str], exclude_patterns: list[str] | None = None
) -> str:
    """
    Extract specific keys from a JSON file.

    Args:
        source_file: Path to source JSON file
        include_keys: List of top-level keys to include
        exclude_patterns: List of patterns to exclude (not yet implemented)

    Returns:
        JSON string with only included keys
    """
    try:
        with open(source_file) as f:
            data = json.load(f)

        # Extract only specified keys
        filtered_data = {}
        for key in include_keys:
            if key in data:
                filtered_data[key] = data[key]

        # Convert back to JSON with nice formatting
        return json.dumps(filtered_data, indent=2)

    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Failed to extract keys from {source_file}: {e}")


def merge_json_keys(dest_file: Path, extracted_content: str, include_keys: list[str]) -> None:
    """
    Merge extracted JSON keys into destination file.

    Args:
        dest_file: Path to destination JSON file
        extracted_content: JSON string with keys to merge
        include_keys: List of keys that were extracted
    """
    try:
        # Load existing destination file if it exists
        if dest_file.exists():
            with open(dest_file) as f:
                dest_data = json.load(f)
        else:
            dest_data = {}

        # Load extracted data
        extracted_data = json.loads(extracted_content)

        # Merge: update only the specified keys
        for key in include_keys:
            if key in extracted_data:
                dest_data[key] = extracted_data[key]

        # Write back to destination
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_file, "w") as f:
            json.dump(dest_data, f, indent=2)
            f.write("\n")  # Add trailing newline

    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Failed to merge keys into {dest_file}: {e}")


def process_special_file(
    source_file: Path,
    dest_file: Path,
    mode: str,
    include_keys: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> bool:
    """
    Process a file with special handling.

    Args:
        source_file: Source file path
        dest_file: Destination file path
        mode: Processing mode ("extract_keys", "copy", etc.)
        include_keys: Keys to include (for extract_keys mode)
        exclude_patterns: Patterns to exclude

    Returns:
        True if processed successfully
    """
    if mode == "extract_keys":
        if not include_keys:
            raise ValueError("include_keys required for extract_keys mode")

        # Extract keys from source
        extracted_content = extract_json_keys(source_file, include_keys, exclude_patterns)

        # Merge into destination
        merge_json_keys(dest_file, extracted_content, include_keys)

        return True
    else:
        raise ValueError(f"Unknown special file mode: {mode}")
