"""
tools.py - LINEAR 5-step pipeline with dual-model architecture
ALL tools use CONTENT MODEL for content generation
Tools receive content_llm and use it for all LLM calls
Step 1: Parse entire PDF -> extract ALL features (content model)
Step 2: Analyze ALL features -> generate requirements for ALL (content model)
Step 3: Generate ALL test scenarios for ALL features (content model)
Step 4: Format ALL scenarios -> write markdown (no LLM needed)
Step 5: Done
"""

import os
import json
import re
from typing import Dict, Any


def reset_state():
    pass  # No state needed in linear pipeline


# ============================================================================
# STEP 1: PARSE ENTIRE SPEC (CONTENT MODEL)
# ============================================================================
def parse_spec_tool(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse entire spec and extract ALL features at once.
    Uses CONTENT MODEL for extraction.

    Input: {"spec_path": "path/to/spec.pdf", "content_llm": <callable>}
    Output: {
        "project": "...",
        "dut": "...",
        "features": ["feature1", "feature2", ...],
        "coverage": ["bin1", "bin2", ...],
        "total_features": N
    }
    """
    spec_path = inp.get("spec_path")
    content_llm = inp.get("content_llm")

    if not spec_path:
        return {"error": "spec_path required"}

    if not content_llm:
        return {"error": "content_llm required - this tool uses content model"}

    try:
        # Read the file
        with open(spec_path, "r", encoding="utf-8") as f:
            spec_content = f.read()

        # If it's a Python spec file
        if spec_path.endswith(".py"):
            namespace = {}
            exec(spec_content, namespace)

            if "spec" not in namespace:
                return {"error": "No 'spec' variable found"}

            spec = namespace["spec"]
            result = {
                "project": spec.get("project_name", "Unknown"),
                "dut": spec.get("dut", "Unknown"),
                "features": spec.get("features", []),
                "coverage": spec.get("coverage", []),
                "methodology": spec.get("methodology", "UVM"),
                "total_features": len(spec.get("features", [])),
            }

        # If it's a PDF/text file, use CONTENT MODEL to extract
        else:
            prompt = f"""Extract ALL features from this specification document.

Document content:
{spec_content[:3000]}  

Output ONLY JSON:
{{
  "project": "project name",
  "dut": "DUT name",
  "features": ["feature1", "feature2", "feature3", ...],
  "coverage": ["coverage_bin1", "coverage_bin2", ...],
  "methodology": "UVM|SystemVerilog|etc"
}}

Extract ALL features found in the document."""

            print("  Using CONTENT model for spec parsing...")
            response = content_llm(prompt)
            response = re.sub(r"```json|```", "", response).strip()

            try:
                result = json.loads(response)
                result["total_features"] = len(result.get("features", []))
            except:
                return {"error": "Failed to parse content model response"}

        # Save parsed spec
        os.makedirs("output", exist_ok=True)
        with open("output/parsed_spec.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"  STEP 1 COMPLETE: Parsed {result['total_features']} features")
        print(f"  Saved to: output/parsed_spec.json")
        return result

    except Exception as e:
        return {"error": f"Parse failed: {str(e)}"}


# ============================================================================
# STEP 2: EXTRACT TEST REQUIREMENTS FOR ALL FEATURES (CONTENT MODEL)
# ============================================================================
def extract_test_requirements_tool(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze ALL features and generate test requirements for ALL at once.
    Uses CONTENT MODEL for analysis.

    Input: {"parsed_spec": <output from step 1>, "content_llm": <callable>}
    Output: {
        "all_requirements": [
            {"feature": "...", "scenario_types": [...], "test_focus": "...", ...},
            ...
        ],
        "total_requirements": N
    }
    """
    parsed_spec = inp.get("parsed_spec")
    content_llm = inp.get("content_llm")

    print(f"  DEBUG: Received input keys: {list(inp.keys())}")
    print(f"  DEBUG: parsed_spec type: {type(parsed_spec)}")

    if not parsed_spec:
        print(f"  ERROR: parsed_spec is missing from input!")
        print(f"  Available keys: {list(inp.keys())}")
        return {"error": "parsed_spec required"}

    if not content_llm:
        return {"error": "content_llm required - this tool uses content model"}

    # Handle string input
    if isinstance(parsed_spec, str):
        try:
            parsed_spec = json.loads(parsed_spec)
        except:
            return {"error": "Invalid JSON in parsed_spec"}

    features = parsed_spec.get("features", [])
    coverage = parsed_spec.get("coverage", [])
    dut = parsed_spec.get("dut", "DUT")

    if not features:
        return {"error": "No features found in parsed_spec"}

    # Build ONE prompt that asks CONTENT MODEL to analyze ALL features
    features_list = "\n".join([f"- {f}" for f in features])
    coverage_list = ", ".join(coverage) if coverage else "general coverage"

    prompt = f"""You are a verification engineer. Analyze test requirements for ALL these features.

DUT: {dut}
Coverage bins: {coverage_list}

Features to analyze:
{features_list}

For EACH feature, provide test requirements.

Output ONLY JSON array:
[
  {{
    "feature": "feature1",
    "scenarios_needed": 2,
    "scenario_types": ["normal_operation", "edge_case"],
    "coverage_mapping": {{"normal_operation": "bin1", "edge_case": "bin2"}},
    "test_focus": "what to test"
  }},
  {{
    "feature": "feature2",
    ...
  }}
]

Provide requirements for ALL {len(features)} features."""

    try:
        print(f"  Using CONTENT model to analyze {len(features)} features...")
        response = content_llm(prompt)
        response = re.sub(r"```json|```", "", response).strip()

        try:
            all_requirements = json.loads(response)
            if not isinstance(all_requirements, list):
                raise ValueError("Expected array")
        except:
            # Fallback: generate simple requirements
            print(
                "  WARNING: Content model response invalid, using fallback requirements"
            )
            all_requirements = []
            for i, feature in enumerate(features):
                all_requirements.append(
                    {
                        "feature": feature,
                        "scenarios_needed": 2,
                        "scenario_types": ["normal_operation", "edge_case"],
                        "coverage_mapping": {
                            "normal_operation": (
                                coverage[i % len(coverage)] if coverage else "general"
                            ),
                            "edge_case": (
                                coverage[(i + 1) % len(coverage)]
                                if coverage
                                else "general"
                            ),
                        },
                        "test_focus": f"Test {feature} functionality",
                    }
                )

        result = {
            "all_requirements": all_requirements,
            "total_requirements": len(all_requirements),
        }

        # Save requirements
        with open("output/test_requirements.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(
            f"  STEP 2 COMPLETE: Generated requirements for {len(all_requirements)} features"
        )
        print(f"  Saved to: output/test_requirements.json")
        return result

    except Exception as e:
        return {"error": f"Requirements extraction failed: {str(e)}"}


# ============================================================================
# STEP 3: GENERATE ALL TEST SCENARIOS (CONTENT MODEL)
# ============================================================================
def generate_test_scenarios_tool(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate ALL test scenarios for ALL features at once.
    Uses CONTENT MODEL for scenario generation.

    Input: {"requirements": <output from step 2>, "content_llm": <callable>}
    Output: {
        "all_scenarios": [...],
        "total_scenarios": N
    }
    """
    requirements_data = inp.get("requirements")
    content_llm = inp.get("content_llm")

    print(f"  DEBUG: Received input keys: {list(inp.keys())}")
    print(f"  DEBUG: requirements type: {type(requirements_data)}")

    if not requirements_data:
        print(f"  ERROR: requirements is missing from input!")
        print(f"  Available keys: {list(inp.keys())}")
        return {"error": "requirements required"}

    if not content_llm:
        return {"error": "content_llm required - this tool uses content model"}

    # Handle string input
    if isinstance(requirements_data, str):
        try:
            requirements_data = json.loads(requirements_data)
        except:
            return {"error": "Invalid JSON in requirements"}

    all_requirements = requirements_data.get("all_requirements", [])

    if not all_requirements:
        return {"error": "No requirements found"}

    # Build list of scenarios needed
    scenarios_needed = []
    for req in all_requirements:
        feature = req.get("feature")
        scenario_types = req.get("scenario_types", [])
        coverage_mapping = req.get("coverage_mapping", {})
        test_focus = req.get("test_focus", "")

        for scenario_type in scenario_types:
            scenarios_needed.append(
                {
                    "feature": feature,
                    "type": scenario_type,
                    "coverage": coverage_mapping.get(scenario_type, "general"),
                    "focus": test_focus,
                }
            )

    # Create prompt for CONTENT MODEL to generate ALL scenarios
    prompt = f"""Generate test scenarios for ALL features. Create {len(scenarios_needed)} scenarios total.

Output ONLY JSON array (one scenario per feature+type):
[
"""

    for i, sc in enumerate(scenarios_needed, 1):
        prompt += f"""  {{
    "scenario_id": "T{i:03d}",
    "feature": "{sc['feature']}",
    "scenario_type": "{sc['type']}",
    "preconditions": "specific conditions for {sc['feature']}",
    "stimulus": "specific trigger for {sc['type']}",
    "test_steps": "1) detailed action 2) check response 3) verify timing 4) confirm completion",
    "expected_result": "specific outcome for {sc['feature']}",
    "coverage_bin": "{sc['coverage']}",
    "priority": "high|medium|low"
  }}{"," if i < len(scenarios_needed) else ""}
"""

    prompt += """]

Generate ALL scenarios with meaningful, specific content (not placeholders).
Each scenario should be detailed and actionable."""

    try:
        print(f"  Using CONTENT model to generate {len(scenarios_needed)} scenarios...")
        response = content_llm(prompt)
        response = re.sub(r"```json|```", "", response).strip()

        try:
            all_scenarios = json.loads(response)
            if not isinstance(all_scenarios, list):
                raise ValueError("Expected array")
        except:
            # Fallback: generate basic scenarios
            print("  WARNING: Content model response invalid, using fallback scenarios")
            all_scenarios = []
            for i, sc in enumerate(scenarios_needed, 1):
                all_scenarios.append(
                    {
                        "scenario_id": f"T{i:03d}",
                        "feature": sc["feature"],
                        "scenario_type": sc["type"],
                        "preconditions": f"DUT initialized and ready for {sc['feature']} testing",
                        "stimulus": f"Trigger {sc['feature']} operation in {sc['type']} mode",
                        "test_steps": f"1) Initiate {sc['feature']} 2) Monitor DUT response 3) Verify timing requirements 4) Confirm proper completion",
                        "expected_result": f"{sc['feature']} completes successfully with correct behavior",
                        "coverage_bin": sc["coverage"],
                        "priority": (
                            "high" if sc["type"] == "normal_operation" else "medium"
                        ),
                    }
                )

        result = {"all_scenarios": all_scenarios, "total_scenarios": len(all_scenarios)}

        # Save scenarios
        with open("output/test_scenarios.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"  STEP 3 COMPLETE: Generated {len(all_scenarios)} test scenarios")
        print(f"  Saved to: output/test_scenarios.json")
        return result

    except Exception as e:
        return {"error": f"Scenario generation failed: {str(e)}"}


# ============================================================================
# STEP 4: FORMAT AND WRITE MARKDOWN (NO LLM NEEDED)
# ============================================================================
def format_and_write_tool(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format ALL scenarios as markdown table and write to file.
    Pure formatting - no LLM needed.

    Input: {"scenarios": <output from step 3>, "outdir": "output"}
    Output: {"file_path": "...", "scenarios_count": N, "success": true}
    """
    scenarios_data = inp.get("scenarios")
    outdir = inp.get("outdir", "output")

    print(f"  DEBUG: Received input keys: {list(inp.keys())}")
    print(f"  DEBUG: scenarios type: {type(scenarios_data)}")

    if not scenarios_data:
        print(f"  ERROR: scenarios is missing from input!")
        print(f"  Available keys: {list(inp.keys())}")
        return {"error": "scenarios required"}

    # Handle string input
    if isinstance(scenarios_data, str):
        try:
            scenarios_data = json.loads(scenarios_data)
        except:
            return {"error": "Invalid JSON in scenarios"}

    all_scenarios = scenarios_data.get("all_scenarios", [])

    if not all_scenarios:
        return {"error": "No scenarios found"}

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

        print(f"  STEP 4 COMPLETE: Wrote {len(all_scenarios)} scenarios to {file_path}")

        return {
            "file_path": file_path,
            "scenarios_count": len(all_scenarios),
            "success": True,
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


# ============================================================================
# TOOL REGISTRY
# ============================================================================
TOOL_REGISTRY = {
    "parse_spec": parse_spec_tool,  # Step 1 - uses content model
    "extract_test_requirements": extract_test_requirements_tool,  # Step 2 - uses content model
    "generate_test_scenarios": generate_test_scenarios_tool,  # Step 3 - uses content model
    "format_and_write": format_and_write_tool,  # Step 4 - no LLM needed
}
