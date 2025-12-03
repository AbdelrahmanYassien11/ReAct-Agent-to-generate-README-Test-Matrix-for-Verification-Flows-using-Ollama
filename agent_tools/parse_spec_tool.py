import sys
import os
import json
import re
from typing import Dict, Any
from .extract_code_from_output import extract_code_block


# ============================================================================
# STEP 1: PARSE ENTIRE SPEC (CONTENT MODEL)
# ============================================================================
def parse_spec_tool(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse entire spec and extract ALL features at once.
    Uses CONTENT MODEL for extraction.

    Input: {"spec_path": "path/to/spec.py"}
    Output: {"success": true, "output_file": "output/parsed_spec.json", "total_features": N}
    """
    spec_path = inp.get("spec_path")
    content_llm = inp.get("content_llm")

    if not spec_path:
        return {"error": "spec_path required"}

    if not content_llm:
        return {"error": "content_llm required"}

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
        output_file = "output/parsed_spec.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"  STEP 1 COMPLETE: Parsed {result['total_features']} features")
        print(f"  Output file: {output_file}")

        return {
            "success": True,
            "output_file": output_file,
            "total_features": result["total_features"],
        }

    except Exception as e:
        return {"error": f"Parse failed: {str(e)}"}
