# generate_test_scenarios_tool.py
import json
import os
import re
from typing import Dict, Any


def generate_test_scenarios_tool(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate test scenarios for each feature and its scenario types from the input JSON file containing test requirements.
    Outputs valid test scenarios for each feature into a single JSON file called `test_scenarios.json`.
    """

    input_json_file = inp.get("input_json_file")
    content_llm = inp.get("content_llm")

    if not all([input_json_file, content_llm]):
        return {"error": "input_json_file and content_llm are required"}

    try:
        with open(input_json_file, "r") as file:
            features = json.load(file)
    except Exception as e:
        return {"error": f"Failed to read input JSON file: {str(e)}"}

    output_dir = "output/scenarios"
    os.makedirs(output_dir, exist_ok=True)

    all_scenarios = []

    for feature_data in features:
        feature = feature_data.get("feature")
        test_requirements = feature_data.get("test_requirements")

        if not feature or not test_requirements:
            continue

        scenario_types = test_requirements.get("scenario_types", [])
        coverage_mapping = test_requirements.get("coverage_mapping", {})
        test_focus = test_requirements.get("test_focus", "")

        for scenario_type in scenario_types:
            coverage_bin = coverage_mapping.get(scenario_type, "general")
            scenario_id = f"T{len(all_scenarios) + 1:03d}"

            prompt = f"""Generate ONE test scenario as JSON only (no explanations):

Scenario ID: {scenario_id}
Feature: {feature}
Type: {scenario_type}
Focus: {test_focus}
Coverage: {coverage_bin}

{{
  "scenario_id": "{scenario_id}",
  "feature": "{feature}",
  "preconditions": "specific initial conditions",
  "stimulus": "specific trigger",
  "test_steps": "1) specific action 2) check response 3) verify timing 4) confirm state",
  "expected_result": "specific expected outcome with metrics",
  "coverage_bin": "{coverage_bin}",
  "priority": "high|medium|low"
}}

Requirements: test_steps MUST have 4 numbered steps."""

            try:
                response = content_llm(prompt)
                response = re.sub(r"```json|```", "", response).strip()

                try:
                    data = json.loads(response)
                except:
                    match = re.search(r"\{[\s\S]*\}", response)
                    if match:
                        data = json.loads(match.group(0))
                    else:
                        data = {
                            "scenario_id": scenario_id,
                            "feature": feature,
                            "preconditions": f"DUT initialized for {feature}",
                            "stimulus": f"Trigger {feature} operation",
                            "test_steps": (
                                f"1) Initiate {feature} 2) Monitor response "
                                f"3) Verify timing 4) Confirm completion"
                            ),
                            "expected_result": f"{feature} completes successfully",
                            "coverage_bin": coverage_bin,
                            "priority": "high",
                        }

                all_scenarios.append(data)

            except Exception as e:
                return {"error": f"Failed to generate or save test scenario: {str(e)}"}

    output_file_path = os.path.join(output_dir, "test_scenarios.json")
    try:
        with open(output_file_path, "w") as output_file:
            json.dump(all_scenarios, output_file, indent=2)
    except Exception as e:
        return {"error": f"Failed to write test scenarios to file: {str(e)}"}

    return {
        "success": f"Test scenarios successfully generated and saved in {output_file_path}",
        "scenarios_count": len(all_scenarios),
    }
