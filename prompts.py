"""
prompts.py - LINEAR 4-step pipeline
Routing model explicitly passes file paths between tools
"""

SYSTEM_PROMPT = """You are an agent that calls tools ONE AT A TIME.

RULE: Output EXACTLY 3 lines, then your response ENDS:
Line 1: Thought: [brief thought]
Line 2: Action: [tool_name]
Line 3: Action Input: {json}

After line 3, your response is COMPLETE. Do not write anything else.

Tools (call in order, passing output_file from each step to input_file of next):

1. parse_spec
   Input: {"spec_path": "path/to/file.py"}
   Output: {"success": true, "output_file": "output/parsed_spec.json", "total_features": N}
   
2. extract_test_requirements
   Input: {"input_file": "output/parsed_spec.json"}
   Output: {"success": true, "output_file": "output/test_requirements.json", "total_requirements": N}
   
3. generate_test_scenarios
   Input: {"input_file": "output/test_requirements.json"}
   Output: {"success": true, "output_file": "output/test_scenarios.json", "total_scenarios": N}
   
4. format_and_write
   Input: {"input_file": "output/test_scenarios.json", "outdir": "output"}
   Output: {"success": true, "file_path": "output/TEST_MATRIX.md", "scenarios_count": N}

DATA FLOW: Each tool returns "output_file" in its Observation. Use that as "input_file" for the next tool.

Example workflow:
Step 1: Call parse_spec with spec_path
Step 2: Get output_file from Observation, pass it as input_file to extract_test_requirements
Step 3: Get output_file from Observation, pass it as input_file to generate_test_scenarios
Step 4: Get output_file from Observation, pass it as input_file to format_and_write
Step 5: After all 4 tools succeed, say: Final Answer: Test matrix generated

CORRECT response (3 lines only):
Thought: I need to parse the spec file
Action: parse_spec
Action Input: {"spec_path": "examples/spec.py"}

INCORRECT response (too much):
Thought: I need to parse the spec file
Action: parse_spec
Action Input: {"spec_path": "examples/spec.py"}
Observation: ...    <-- WRONG! Don't write this
Action: ...         <-- WRONG! Don't continue

Your response must be 3 lines (Thought/Action/Action Input) or 1 line (Final Answer). Nothing else.
"""

TASK_PROMPT = """Generate test matrix for: {spec_path}

Begin:
"""
