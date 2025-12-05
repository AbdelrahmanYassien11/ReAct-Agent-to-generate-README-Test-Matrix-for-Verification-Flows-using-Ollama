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
# STEP 2: EXTRACT TEST REQUIREMENTS (CONTENT MODEL)
# ============================================================================
def extract_test_requirements_tool(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze ALL features and generate test requirements for ALL at once.
    Uses CONTENT MODEL for analysis.

    Input: {"input_file": "output/parsed_spec.json"}
    Output: {"success": true, "output_file": "output/test_requirements.json", "total_requirements": N}
    """
    input_file = inp.get("input_file")
    content_llm = inp.get("content_llm")

    if not input_file:
        return {"error": "input_file required (path to parsed_spec.json)"}

    if not content_llm:
        return {"error": "content_llm required"}

    if not os.path.exists(input_file):
        return {"error": f"File not found: {input_file}"}

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            parsed_spec = json.load(f)
    except Exception as e:
        return {"error": f"Failed to read {input_file}: {str(e)}"}

    features = parsed_spec.get("features", [])
    coverage = parsed_spec.get("coverage", [])
    dut = parsed_spec.get("dut", "DUT")

    if not features:
        return {"error": "No features found in input file"}

    # Build prompt for CONTENT MODEL
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

1. Provide requirements for ALL {len(features)} features
2. Output your response in JSON format only in between triple back ticks like ``` content ```
3. Dont output any other accompanying text"""

    try:
        print(f"  Using CONTENT model to analyze {len(features)} features...")
        response = content_llm(prompt)
        # print(response)
        response = extract_code_block(response)
        # print(type(response))
        # print(response)

        try:
            all_requirements = json.loads(response)
            if not isinstance(all_requirements, list):
                raise ValueError("Expected array")
            print("[SUCCESS] [TOOL] [EXTRACT REQUIREMENTS]")
        except Exception as e:
            print("[FAIL] [TOOL] [EXTRACT REQUIREMENTS]")
            error_message = f"Requirements extraction failed: {str(e)}"
            # return {"error": error_message}  # Return the error message before exiting
            os._exit(0)  # To be commented

        result = {
            "all_requirements": all_requirements,
            "total_requirements": len(all_requirements),
        }

        # Save requirements
        output_file = "output/test_requirements.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(
            f"  STEP 2 COMPLETE: Generated requirements for {len(all_requirements)} features"
        )
        print(f"  Output file: {output_file}")

        return {
            "success": True,
            "output_file": output_file,
            "total_requirements": len(all_requirements),
        }

    except Exception as e:
        return {"error": f"Requirements extraction failed: {str(e)}"}
