"""
tools.py

Tool implementations that the ReAct agent can call.
Each tool receives a dict (action input) and returns a string (observation).
"""
import os
from typing import Dict, Any

def write_readme_tool(inp: Dict[str, Any]) -> str:
    """Write README file with verification documentation."""
    outdir = inp.get("outdir", "output")
    content = inp.get("content", "")
    
    if not content or (isinstance(content, str) and not content.strip()):
        return f"[error: no content provided] input_keys={list(inp.keys())} content_repr={repr(content)}"
    
    path = os.path.join(outdir, "README_generated.md")
    os.makedirs(outdir, exist_ok=True)
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"SUCCESS: wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"[error: {e}]"

def write_testmatrix_tool(inp: Dict[str, Any]) -> str:
    """Write test matrix file with coverage table."""
    outdir = inp.get("outdir", "output")
    content = inp.get("content", "")
    
    if not content or (isinstance(content, str) and not content.strip()):
        return f"[error: no content provided] input_keys={list(inp.keys())} content_repr={repr(content)}"
    
    path = os.path.join(outdir, "TEST_MATRIX_generated.md")
    os.makedirs(outdir, exist_ok=True)
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"SUCCESS: wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"[error: {e}]"

def explain_tool(inp: Dict[str, Any]) -> str:
    """Explain the specification."""
    spec = inp.get("spec") or {}
    features = spec.get('features', [])
    coverage = spec.get('coverage', [])
    
    explanation = f"Specification Summary:\n"
    explanation += f"- Project: {spec.get('project_name', 'N/A')}\n"
    explanation += f"- Features to verify: {len(features)} items\n"
    explanation += f"- Coverage bins: {len(coverage)} items\n"
    explanation += f"- Methodology: {spec.get('methodology', 'N/A')}\n"
    
    return explanation

def debug_tool(inp: Dict[str, Any]) -> str:
    """Debug the specification for common issues."""
    spec = inp.get("spec") or {}
    problems = []
    
    if not spec.get("features"):
        problems.append("no features listed")
    if not spec.get("coverage"):
        problems.append("no coverage bins listed")
    if not spec.get("project_name"):
        problems.append("no project name")
    if not spec.get("methodology"):
        problems.append("no methodology specified")
    
    if problems:
        return "ISSUES FOUND: " + ", ".join(problems)
    return "OK: No obvious issues found"

# Tool registry used by ReAct executor
TOOL_REGISTRY = {
    "write_readme": write_readme_tool,
    "write_testmatrix": write_testmatrix_tool,
    "explain": explain_tool,
    "debug": debug_tool,
}