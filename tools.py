"""
tools.py - Optimized TRUE ReAct tools
Simplified data flow, faster execution, better error handling
"""
import os
import json
import re
from typing import Dict, Any

_scenario_buffer = []
_current_scenario_id = 1
_spec_data = None

def reset_scenario_buffer():
    global _scenario_buffer, _current_scenario_id, _spec_data
    _scenario_buffer = []
    _current_scenario_id = 1
    _spec_data = None


def load_spec_tool(inp: Dict[str, Any]) -> str:
    """
    Load and validate spec file.
    Input: {"spec_path": "examples/example_spec.py"}
    Output: Success message with spec summary
    """
    global _spec_data
    
    spec_path = inp.get("spec_path")
    spec_dict = inp.get("spec_dict")
    
    if spec_dict:
        _spec_data = spec_dict
    elif spec_path:
        try:
            with open(spec_path, 'r') as f:
                code = f.read()
            namespace = {}
            exec(code, namespace)
            if 'spec' not in namespace:
                return "[Error: No 'spec' variable in file]"
            _spec_data = namespace['spec']
        except Exception as e:
            return f"[Error loading spec: {e}]"
    else:
        return "[Error: No spec_path or spec_dict provided]"
    
    features = _spec_data.get("features", [])
    coverage = _spec_data.get("coverage", [])
    
    return f"""Spec loaded successfully:
Project: {_spec_data.get('project_name', 'Unknown')}
Features: {', '.join(features)}
Coverage: {', '.join(coverage)}
Scenarios needed: {len(features) * 2}"""


def get_next_task_tool(inp: Dict[str, Any]) -> str:
    """
    Get next task to work on.
    Input: {}
    Output: JSON with task info or completion message
    """
    if not _spec_data:
        return "[Error: Load spec first using load_spec]"
    
    features = _spec_data.get("features", [])
    coverage = _spec_data.get("coverage", [])
    
    # Count scenarios per feature
    counts = {}
    for s in _scenario_buffer:
        feat = s.get("feature", "")
        counts[feat] = counts.get(feat, 0) + 1
    
    # Find feature needing scenarios
    for feature in features:
        count = counts.get(feature, 0)
        if count < 2:
            scenario_type = "normal" if count == 0 else "edge_case"
            coverage_bin = coverage[len(_scenario_buffer) % len(coverage)] if coverage else "general"
            
            return json.dumps({
                "task": "generate_scenario",
                "feature": feature,
                "type": scenario_type,
                "coverage_bin": coverage_bin,
                "progress": f"{len(_scenario_buffer)}/{len(features)*2}"
            })
    
    return json.dumps({"task": "complete", "total_scenarios": len(_scenario_buffer)})


def generate_scenario_tool(inp: Dict[str, Any]) -> str:
    """
    Generate scenario using content LLM.
    Input: {"feature": "handshake", "type": "normal", "coverage_bin": "fsm_states"}
    Output: JSON with scenario details
    """
    feature = inp.get("feature")
    scenario_type = inp.get("type", "normal")
    coverage_bin = inp.get("coverage_bin", "general")
    content_llm = inp.get("content_llm")
    
    if not feature:
        return "[Error: No feature specified]"
    if not content_llm:
        return "[Error: content_llm not available]"
    if not _spec_data:
        return "[Error: Load spec first]"
    
    dut = _spec_data.get("dut", "DUT")
    
    # Simplified prompt
    prompt = f"""Generate test scenario as JSON only (no other text):

Feature: {feature}
Type: {scenario_type}
DUT: {dut}
Coverage: {coverage_bin}

{{
  "preconditions": "initial conditions",
  "stimulus": "trigger event",
  "test_steps": "1) action 2) check 3) verify 4) confirm",
  "expected_result": "expected outcome",
  "priority": "high|medium|low"
}}"""
    
    try:
        response = content_llm(prompt)
        response = re.sub(r'```json|```', '', response).strip()
        
        # Try parsing
        try:
            data = json.loads(response)
        except:
            # Extract JSON from text
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                data = json.loads(match.group(0))
            else:
                # Generate fallback
                data = {
                    "preconditions": f"DUT ready for {feature} test",
                    "stimulus": f"Trigger {feature} operation",
                    "test_steps": f"1) Initiate {feature} 2) Monitor response 3) Check timing 4) Verify completion",
                    "expected_result": f"{feature.title()} completes successfully",
                    "priority": "high"
                }
        
        # Add metadata
        data["feature"] = feature
        data["coverage_bin"] = coverage_bin
        
        return json.dumps(data)
        
    except Exception as e:
        return f"[Error: {e}]"


def add_scenario_tool(inp: Dict[str, Any]) -> str:
    """
    Add scenario to buffer.
    Input: {"scenario_json": "<from generate_scenario>"}
    Output: Confirmation
    """
    global _current_scenario_id
    
    scenario_json = inp.get("scenario_json")
    if not scenario_json:
        return "[Error: No scenario_json provided]"
    
    try:
        data = json.loads(scenario_json)
    except:
        return "[Error: Invalid JSON]"
    
    required = ["feature", "preconditions", "stimulus", "test_steps", "expected_result", "coverage_bin", "priority"]
    missing = [f for f in required if f not in data]
    if missing:
        return f"[Error: Missing {', '.join(missing)}]"
    
    scenario = {
        "scenario_id": f"T{_current_scenario_id:03d}",
        "feature": data["feature"],
        "preconditions": data["preconditions"],
        "stimulus": data["stimulus"],
        "test_steps": data["test_steps"],
        "expected_result": data["expected_result"],
        "coverage_bin": data["coverage_bin"],
        "priority": data["priority"]
    }
    
    _scenario_buffer.append(scenario)
    _current_scenario_id += 1
    
    return f"Added {scenario['scenario_id']} ({len(_scenario_buffer)} total)"


def write_file_tool(inp: Dict[str, Any]) -> str:
    """
    Write test matrix file.
    Input: {"outdir": "output"}
    Output: File path
    """
    outdir = inp.get("outdir", "output")
    
    if not _scenario_buffer:
        return "[Error: No scenarios to write]"
    
    table = """| Scenario ID | Feature | Preconditions | Stimulus | Test Steps | Expected Result | Coverage Bin | Priority |
|-------------|---------|---------------|----------|------------|-----------------|--------------|----------|
"""
    
    for s in _scenario_buffer:
        table += f"| {s['scenario_id']} | {s['feature']} | {s['preconditions']} | {s['stimulus']} | {s['test_steps']} | {s['expected_result']} | {s['coverage_bin']} | {s['priority']} |\n"
    
    # Format with spacing
    formatted = _format_table(table)
    
    path = os.path.join(outdir, "TEST_MATRIX.md")
    os.makedirs(outdir, exist_ok=True)
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(formatted)
        return f"SUCCESS: {path} ({len(_scenario_buffer)} scenarios)"
    except Exception as e:
        return f"[Error: {e}]"


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


TOOL_REGISTRY = {
    "load_spec": load_spec_tool,
    "get_next_task": get_next_task_tool,
    "generate_scenario": generate_scenario_tool,
    "add_scenario": add_scenario_tool,
    "write_file": write_file_tool,
}