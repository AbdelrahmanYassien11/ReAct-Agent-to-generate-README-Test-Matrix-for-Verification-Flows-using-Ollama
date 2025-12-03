"""
tools.py - LINEAR 4-step pipeline with dual-model architecture
ALL tools use CONTENT MODEL for content generation
Tools receive file paths explicitly from routing model
Step 1: Parse entire spec -> write parsed_spec.json
Step 2: Read file from step 1 -> write test_requirements.json
Step 3: Read file from step 2 -> write test_scenarios.json
Step 4: Read file from step 3 -> write TEST_MATRIX.md
"""

import os
import json
import re
from typing import Dict, Any
from .extract_code_from_output import extract_code_block


# ============================================================================
# STEP 4: FORMAT AND WRITE MARKDOWN (NO LLM NEEDED)
# ============================================================================
def format_and_write_tool(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format ALL scenarios as markdown table and write to file.
    Pure formatting - no LLM needed.

    Input: {"input_file": "output/test_scenarios.json", "outdir": "output"}
    Output: {"success": true, "file_path": "output/TEST_MATRIX.md", "scenarios_count": N}
    """
    input_file = inp.get("input_file")
    outdir = inp.get("outdir", "output")

    if not input_file:
        return {"error": "input_file required (path to test_scenarios.json)"}

    if not os.path.exists(input_file):
        return {"error": f"File not found: {input_file}"}

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            scenarios_data = json.load(f)
    except Exception as e:
        return {"error": f"Failed to read {input_file}: {str(e)}"}

    all_scenarios = scenarios_data.get("all_scenarios", [])

    if not all_scenarios:
        return {"error": "No scenarios found in input file"}

    # Build markdown table
    table = """# Test Matrix

| Scenario ID | Feature | Preconditions | Stimulus | Test Steps | Expected Result | Coverage Bin | Priority |
|-------------|---------|---------------|----------|------------|-----------------|--------------|----------|
"""

    for s in all_scenarios:
        table += (
            f"| {s.get('scenario_id', 'T000')} "
            f"| {s.get('feature', '')} "
            f"| {s.get('preconditions', '')} "
            f"| {s.get('stimulus', '')} "
            f"| {s.get('test_steps', '')} "
            f"| {s.get('expected_result', '')} "
            f"| {s.get('coverage_bin', '')} "
            f"| {s.get('priority', '')} |\n"
        )

    # Format with dynamic spacing
    formatted = _format_table(table)

    # Write to file
    os.makedirs(outdir, exist_ok=True)
    file_path = f"{outdir}/TEST_MATRIX.md"

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(formatted)

        print(f"  STEP 4 COMPLETE: Wrote {len(all_scenarios)} scenarios")
        print(f"  Output file: {file_path}")

        return {
            "success": True,
            "file_path": file_path,
            "scenarios_count": len(all_scenarios),
        }
    except Exception as e:
        return {"error": f"Write failed: {str(e)}"}


def _format_table(table_text: str) -> str:
    """Format table with dynamic column widths."""
    lines = table_text.split("\n")
    table_lines = [l for l in lines if l.strip().startswith("|")]

    if len(table_lines) < 2:
        return table_text

    rows = []
    for line in table_lines:
        cells = [c.strip() for c in line.split("|")[1:-1]]
        rows.append(cells)

    num_cols = len(rows[0]) if rows else 0
    col_widths = [0] * num_cols

    for row in rows:
        for i, cell in enumerate(row):
            if i < num_cols and "---" not in cell:
                col_widths[i] = max(col_widths[i], len(cell))

    for i in range(num_cols):
        col_widths[i] += max(3, int(col_widths[i] * 0.1))

    formatted_lines = []
    for row in rows:
        formatted_cells = []
        for i, cell in enumerate(row):
            if i < num_cols:
                if "---" in cell:
                    formatted_cells.append("-" * col_widths[i])
                else:
                    formatted_cells.append(cell.ljust(col_widths[i]))
        formatted_lines.append("| " + " | ".join(formatted_cells) + " |")

    return "\n".join(formatted_lines)
