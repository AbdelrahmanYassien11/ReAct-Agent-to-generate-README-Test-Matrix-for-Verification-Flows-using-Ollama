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
# STEP 3: GENERATE ALL TEST SCENARIOS (CONTENT MODEL)
# ============================================================================
def generate_test_scenarios_tool(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate ALL test scenarios for ALL features at "output/test_requriements.json" at once.
    Uses CONTENT MODEL for scenario generation.

    Input: {"input_file": "output/test_requirements.json"}
    Output: {"success": true, "output_file": "output/test_scenarios.json", "total_scenarios": N}

    """
    input_file = inp.get("input_file")
    content_llm = inp.get("content_llm")

    if not input_file:
        print("[FAIL] [INPUT_FILE] [FILE] [TOOL] [Test Scenarios]")
        return {"error": "input_file required (path to test_requirements.json)"}

    if not content_llm:
        print("[FAIL] [Content LLM] [TOOL] [Test Scenarios]")
        return {"error": "content_llm required"}

    if not os.path.exists(input_file):
        print("[FAIL] [INPUT_FILE] [PATH] [TOOL] [Test Scenarios]")
        return {"error": f"File not found: {input_file}"}

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            requirements_data = json.load(f)
    except Exception as e:
        print("[FAIL] [INPUT FILE LOADING] [TOOL] [Test Scenarios]")
        return {"error": f"Failed to read {input_file}: {str(e)}"}

    all_requirements = requirements_data.get("all_requirements", [])

    if not all_requirements:
        print("[FAIL] [REQUIREMENTS LOADING] [TOOL] [Test Scenarios]")
        return {"error": "No requirements found in input file"}

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

    # Create prompt for CONTENT MODEL
    prompt = f"""Generate test scenarios for ALL features. 
    Create {len(scenarios_needed)} scenarios total.

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

1. Generate ALL scenarios with meaningful, specific content (not placeholders).
2. Each scenario should be detailed and actionable.
3. Output your response in JSON format only in between triple back ticks like ``` content ```
4. Dont output any other accompanying text
"""
    try:
        print(f"  Using CONTENT model to generate {len(scenarios_needed)} scenarios...")
        response = content_llm(prompt)
        response = extract_code_block(response)

        try:
            all_scenarios = json.loads(response)
            if not isinstance(all_scenarios, list):
                raise ValueError("Expected array")
            print("[SUCCESS] [TOOL] [GENERATE SCENARIOS]")

        except:
            # Fallback: generate simple requirements
            print("[FAIL] [TOOL] [EXTRACT REQUIREMENTS]")
            error_message = f"Scenarios Generation failed: {str(e)}"
            # return {"error": error_message}  # Return the error message before exiting
            os._exit(0)  # To be commented

        result = {"all_scenarios": all_scenarios, "total_scenarios": len(all_scenarios)}

        # Save scenarios
        output_file = "output/test_scenarios.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"  STEP 3 COMPLETE: Generated {len(all_scenarios)} test scenarios")
        print(f"  Output file: {output_file}")

        return {
            "success": True,
            "output_file": output_file,
            "total_scenarios": len(all_scenarios),
        }

    except Exception as e:
        return {"error": f"Scenario generation failed: {str(e)}"}
