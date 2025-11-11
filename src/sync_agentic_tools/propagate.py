"""
Propagation logic for cross-tool file copying with transformations.
"""

import re
from pathlib import Path
from typing import Any

from .config import Config, PropagationRule
from .ui import show_error, show_info


def apply_sed_transform(content: str, pattern: str) -> str:
    """
    Apply sed-style regex transformation.

    Supports patterns like: 's/old/new/g', 's/old/new/', 's|old|new|g'
    """
    # Parse sed pattern
    if not pattern.startswith("s"):
        raise ValueError(f"Invalid sed pattern: {pattern}")

    # Find delimiter (usually /)
    delimiter = pattern[1]
    parts = pattern.split(delimiter)

    if len(parts) < 3:
        raise ValueError(f"Invalid sed pattern: {pattern}")

    search = parts[1]
    replace = parts[2]
    flags = parts[3] if len(parts) > 3 else ""

    # Apply regex replacement
    if "g" in flags:
        # Global replacement
        return re.sub(search, replace, content)
    else:
        # Single replacement
        return re.sub(search, replace, content, count=1)


def apply_remove_xml_sections_transform(content: str, sections: list[str]) -> str:
    """
    Remove specific sections from markdown-style content.

    Sections are identified by XML-style tags like <SECTION_NAME>...</SECTION_NAME>
    """
    result = content

    for section in sections:
        # Match section with both self-closing and paired tags
        # Pattern: <SECTION_NAME>...</SECTION_NAME> or <SECTION_NAME/>
        pattern = rf"<{section}[^>]*>.*?</{section}>|<{section}\s*/>"
        result = re.sub(pattern, "", result, flags=re.DOTALL)

    return result


def apply_transform(content: str, transform: dict[str, Any]) -> str:
    """Apply a single transformation to content."""
    transform_type = transform.get("type")

    if transform_type == "sed":
        pattern = transform.get("pattern")
        if not pattern:
            raise ValueError("sed transform requires 'pattern' parameter")
        return apply_sed_transform(content, pattern)

    elif transform_type == "remove_xml_sections":
        sections = transform.get("sections")
        if not sections:
            raise ValueError("remove_xml_sections transform requires 'sections' parameter")
        return apply_remove_xml_sections_transform(content, sections)

    else:
        raise ValueError(f"Unknown transform type: {transform_type}")


def propagate_file(
    config: Config,
    rule: PropagationRule,
    dry_run: bool = False,
) -> None:
    """
    Propagate a file from source tool to target tools with transformations.

    Args:
        config: Configuration object
        rule: Propagation rule to apply
        dry_run: If True, don't actually write files
    """
    # Determine source path
    if rule.source_path:
        # Absolute path provided
        source_path = Path(rule.source_path).expanduser()
    elif rule.source_tool and rule.source_file:
        # Tool-relative path
        if rule.source_tool not in config.tools:
            raise ValueError(f"Source tool not found: {rule.source_tool}")

        source_tool = config.tools[rule.source_tool]
        # Tool-based propagation always uses target directories
        source_path = source_tool.target / rule.source_file
    else:
        raise ValueError(
            "Propagation rule must specify either source_path or (source_tool + source_file)"
        )

    if not source_path.exists():
        show_info(f"Skipping propagation: source file does not exist: {source_path}")
        return

    # Read source content
    try:
        with open(source_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        show_error(f"Failed to read source file {source_path}: {e}")
        return

    # Propagate to each target
    for target in rule.targets:
        # Determine target path
        if target.dest_path:
            # Absolute path provided
            target_path = Path(target.dest_path).expanduser()
        elif target.tool and target.target_file:
            # Tool-relative path
            if target.tool not in config.tools:
                show_error(f"Target tool not found: {target.tool}")
                continue

            target_tool = config.tools[target.tool]
            # Tool-based propagation always uses target directories
            target_path = target_tool.target / target.target_file
        else:
            show_error("Target must specify either dest_path or (tool + target_file)")
            continue

        # Apply transformations
        transformed_content = content
        for transform in target.transforms:
            try:
                transformed_content = apply_transform(transformed_content, transform)
            except Exception as e:
                show_error(f"Failed to apply transform {transform.type}: {e}")
                continue

        # Check if target already has the same content
        needs_update = True
        if target_path.exists():
            try:
                with open(target_path, encoding="utf-8") as f:
                    existing_content = f.read()
                if existing_content == transformed_content:
                    needs_update = False
            except Exception:
                # If we can't read target, assume it needs update
                needs_update = True

        # Write to target only if changed
        if not needs_update:
            # Skip - already up to date
            pass
        elif dry_run:
            show_info(f"Would propagate: {source_path} → {target_path}")
        else:
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(transformed_content)

                # Format source and target for display
                source_display = (
                    str(source_path)
                    if rule.source_path
                    else f"{rule.source_tool}:{rule.source_file}"
                )
                target_display = (
                    str(target_path) if target.dest_path else f"{target.tool}:{target.target_file}"
                )
                show_info(f"Propagated: {source_display} → {target_display}")
            except Exception as e:
                show_error(f"Failed to write target file {target_path}: {e}")


def run_propagation(config: Config, dry_run: bool = False) -> None:
    """
    Run all propagation rules in configuration.

    Args:
        config: Configuration object
        dry_run: If True, don't actually write files
    """
    if not config.propagate:
        return

    show_info("Running propagation rules...")

    for rule in config.propagate:
        try:
            propagate_file(config, rule, dry_run)
        except Exception as e:
            source_display = rule.source_path or f"{rule.source_tool}/{rule.source_file}"
            show_error(f"Propagation failed for {source_display}: {e}")
