# format_and_write_tool.py
import json
import os
from typing import Dict, Any


def format_and_write_tool(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format all scenarios as markdown table and return a file object.
    The ReAct executor will handle writing the file to disk.

    Input:
        {
            "outdir": "output"
        }

    Output:
        {
            "filename": "TEST_MATRIX.md",
            "content": "<markdown text>"
        }
    """

    outdir = inp.get("outdir", "output")
    test_scenarios_file = os.path.join(outdir, "test_scenarios.json")

    if not os.path.exists(test_scenarios_file):
        return {"error": f"{test_scenarios_file} not found"}

    try:
        with open(test_scenarios_file, "r") as f:
            scenarios = json.load(f)
    except Exception as e:
        return {"error": f"Failed to read {test_scenarios_file}: {str(e)}"}

    if not scenarios:
        return {"error": "No scenarios found in the test_scenarios.json file"}

    table = """| Scenario ID | Feature | Preconditions | Stimulus | Test Steps | Expected Result | Coverage Bin | Priority |
|-------------|---------|---------------|----------|------------|-----------------|--------------|----------|
"""

    for s in scenarios:
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

    formatted = _format_table(table)

    return {"filename": "TEST_MATRIX.md", "content": formatted}


def _format_table(table_text: str) -> str:
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
