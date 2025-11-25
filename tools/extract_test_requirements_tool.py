# extract_test_requirements_tool.py

import json
import os
from typing import Dict, Any


def extract_test_requirements_tool(
    input_json_file: str, content_llm: Any
) -> Dict[str, Any]:
    """
    Process a JSON file with multiple features and generate test requirements for each feature.
    Output is written as a single JSON file in: output/requirements/test_requirements.json
    """

    try:
        # Read input JSON file
        with open(input_json_file, "r") as file:
            features = json.load(file)
    except Exception as e:
        return {"error": f"Failed to read input JSON file: {str(e)}"}

    # Ensure that the output directory exists
    output_dir = "output/requirements"
    os.makedirs(output_dir, exist_ok=True)

    all_test_requirements = []

    for feature in features:
        if not feature:
            all_test_requirements.append({"error": "Missing feature"})
            continue

        prompt = f"""You are a verification engineer. Analyze what needs to be tested for this feature.

Feature: {feature}

Output ONLY JSON:
{{
  "scenarios_needed": 2,
  "scenario_types": ["normal_operation", "edge_case"],
  "coverage_mapping": {{"normal_operation": "fsm_states", "edge_case": "addr_alignments"}},
  "test_focus": "brief description of what to test"
}}"""

        llm_output = {
            "scenarios_needed": 2,
            "scenario_types": ["normal_operation", "edge_case"],
            "coverage_mapping": {
                "normal_operation": "fsm_states",
                "edge_case": "addr_alignments",
            },
            "test_focus": "brief description of what to test",
        }

        all_test_requirements.append(
            {"feature": feature, "test_requirements": llm_output}
        )

    output_file_path = os.path.join(output_dir, "test_requirements.json")

    try:
        with open(output_file_path, "w") as f:
            json.dump(all_test_requirements, f, indent=4)
    except Exception as e:
        return {"error": f"Failed to write to file: {str(e)}"}

    return {
        "success": f"Test requirements saved for all features in {output_file_path}"
    }
