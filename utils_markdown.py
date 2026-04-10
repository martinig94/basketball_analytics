"""Utilities for injecting generated content into MkDocs markdown files."""

import re
from datetime import datetime

import pandas as pd


def update_content_in_file(file_path: str, content: str, suffix: str) -> None:
    """Replace the body between START_TABLE/END_TABLE markers with *content*.

    Args:
        file_path: Path to the markdown file to update.
        content: Raw markdown string to inject between the markers.
        suffix: Marker identifier (e.g. ``"SEASON-OVERVIEW"``).
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    new_text = re.sub(
        rf"(<!-- START_TABLE {re.escape(suffix)} -->)(.*?)"
        rf"(<!-- END_TABLE {re.escape(suffix)} -->)",
        f"\\1\n{content}\n\\3",
        text,
        flags=re.DOTALL,
    )

    new_text = new_text.replace(
        "{{ date }}", datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_text)


def update_table_in_file(
    file_path: str, table_to_md: pd.DataFrame, suffix: str
) -> None:
    """Render *table_to_md* as markdown and inject it between markers in a file.

    Args:
        file_path: Path to the markdown file to update.
        table_to_md: DataFrame to render via ``DataFrame.to_markdown()``.
        suffix: Marker identifier (e.g. ``"SEASON-OVERVIEW"``).
    """
    update_content_in_file(file_path, table_to_md.to_markdown(index=False), suffix)
