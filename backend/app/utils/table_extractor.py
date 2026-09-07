"""
Smart Inbox Assistant — Table Extractor Utility
Extracts tabular data from PDF text using heuristics.
"""
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def extract_tables_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract table-like structures from text using heuristics.
    Handles pipe-delimited, tab-delimited, and space-aligned tables.
    """
    if not text:
        return []

    tables = []
    lines = text.split("\n")
    current_table: List[List[str]] = []
    in_table = False
    table_start_line = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect pipe-delimited tables
        if "|" in stripped and stripped.count("|") >= 2:
            # Skip separator lines (like |---|---|)
            if re.match(r"^[\|\-\s:]+$", stripped):
                continue
            if not in_table:
                in_table = True
                current_table = []
                table_start_line = i + 1
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            if cells:
                current_table.append(cells)

        # Detect tab-delimited tables
        elif "\t" in stripped and stripped.count("\t") >= 1:
            if not in_table:
                in_table = True
                current_table = []
                table_start_line = i + 1
            cells = [c.strip() for c in stripped.split("\t") if c.strip()]
            if cells:
                current_table.append(cells)

        else:
            if in_table and len(current_table) >= 2:
                tables.append({
                    "rows": current_table,
                    "row_count": len(current_table),
                    "col_count": max(len(r) for r in current_table) if current_table else 0,
                    "start_line": table_start_line,
                    "header": current_table[0] if current_table else [],
                })
            in_table = False
            current_table = []

    # Handle table at end of text
    if in_table and len(current_table) >= 2:
        tables.append({
            "rows": current_table,
            "row_count": len(current_table),
            "col_count": max(len(r) for r in current_table) if current_table else 0,
            "start_line": table_start_line,
            "header": current_table[0] if current_table else [],
        })

    logger.info(f"Found {len(tables)} table(s) in text")
    return tables
