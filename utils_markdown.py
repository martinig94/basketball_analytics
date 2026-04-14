"""Utilities for injecting generated content into MkDocs markdown files."""

import re
from datetime import datetime

import pandas as pd


# ── private core ──────────────────────────────────────────────────────────────


def _replace_between_markers(
    file_path: str,
    content: str,
    suffix: str,
    marker_type: str,
) -> None:
    """Replace everything between a START/END marker pair with *content*.

    Marker pairs look like::

        <!-- START_{marker_type} {suffix} -->
        ...existing content...
        <!-- END_{marker_type} {suffix} -->

    The replacement is written back atomically (read → transform → write).
    Any ``{{ date }}`` placeholders in the file are also expanded.

    Args:
        file_path: Path to the markdown file to update.
        content: Raw markdown string to inject between the markers.
        suffix: Marker identifier (e.g. ``"ZONE-SUMMARY"``).
        marker_type: Marker keyword — ``"TABLE"`` or ``"INFO"``.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    new_text = re.sub(
        rf"(<!-- START_{re.escape(marker_type)} {re.escape(suffix)} -->)(.*?)"
        rf"(<!-- END_{re.escape(marker_type)} {re.escape(suffix)} -->)",
        f"\\1\n{content}\n\\3",
        text,
        flags=re.DOTALL,
    )
    new_text = new_text.replace(
        "{{ date }}", datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_text)


# ── public interface ───────────────────────────────────────────────────────────


def update_content_in_file(file_path: str, content: str, suffix: str) -> None:
    """Inject *content* between ``START_TABLE`` / ``END_TABLE`` markers.

    Args:
        file_path: Path to the markdown file to update.
        content: Raw markdown string to inject between the markers.
        suffix: Marker identifier (e.g. ``"SEASON-OVERVIEW"``).
    """
    _replace_between_markers(file_path, content, suffix, "TABLE")


def update_table_in_file(
    file_path: str, table_to_md: pd.DataFrame, suffix: str
) -> None:
    """Render *table_to_md* as markdown and inject it between ``TABLE`` markers.

    Args:
        file_path: Path to the markdown file to update.
        table_to_md: DataFrame to render via ``DataFrame.to_markdown()``.
        suffix: Marker identifier (e.g. ``"SEASON-OVERVIEW"``).
    """
    update_content_in_file(file_path, table_to_md.to_markdown(index=False), suffix)


def update_info_in_file(file_path: str, content: str, suffix: str) -> None:
    """Inject *content* between ``START_INFO`` / ``END_INFO`` markers.

    Intended for admonition blocks (``!!! info``, ``!!! tip``, etc.) and
    other freeform markdown that is not a DataFrame table.

    Args:
        file_path: Path to the markdown file to update.
        content: Raw markdown string to inject between the markers.
        suffix: Marker identifier (e.g. ``"ZONE-SUMMARY"``).
    """
    _replace_between_markers(file_path, content, suffix, "INFO")
