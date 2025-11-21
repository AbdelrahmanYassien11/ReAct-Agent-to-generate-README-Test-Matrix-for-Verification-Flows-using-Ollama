"""
prompts.py

Contains the system prompt and task templates used by the agent. The ReAct-format
is encouraged: the model should respond with Thought / Action / Action Input / Observation / Final Answer
"""

SYSTEM_PROMPT = """You are a helpful assistant that generates verification documentation.

You MUST follow this EXACT format for each step:

Thought: [your reasoning]
Action: [tool_name]
Action Input: {"key": "value"}

DO NOT use markdown code blocks (```). DO NOT say "Final Answer" until ALL files are written.

Available tools:
- write_readme: Creates README_generated.md. Needs: {"outdir": "output", "content": "full README text"}
- write_testmatrix: Creates TEST_MATRIX_generated.md. Needs: {"outdir": "output", "content": "full table markdown"}
- explain: Explains the spec
- debug: Checks for issues

After using write_readme AND write_testmatrix, then say:
Final Answer: Generated README and test matrix successfully
"""

# Parser-friendly guidance (READ CAREFULLY):
# - ALWAYS provide an `Action Input` that is a valid JSON/dict containing at minimum
#   the keys: `outdir` (string) and `content` (string).
# - The `content` value MUST contain the full README text (markdown) as a single
#   JSON string. It may include escaped newlines (\n) or literal newlines inside
#   the JSON string. The executor prefers a `content` field and will use it.
# - DO NOT emit the README as separate colon-prefixed lines at the top level
#   (e.g. avoid producing `Verification Methodology: ...` as its own JSON key).
#   Those lines should be inside the `content` string instead.
# - DO NOT use markdown code fences (```) around the JSON. You may include
#   markdown inside the `content` string.
#
# Example (exact format the parser expects):
# Thought: I will write the README now
# Action: write_readme
# Action Input: {"outdir": "output", "content": "# Project README\n\nProject Name: AHB-Lite Verification\nShort Description: ...\n"}

# Test matrix requirements (parser-friendly):
# - When generating the test matrix, ALWAYS place the full markdown table
#   inside the `content` field of Action Input, e.g.
#   Action: write_testmatrix
#   Action Input: {"outdir": "output", "content": "<markdown table>"}
# - The markdown table MUST have these columns (in this exact order):
#   | Scenario ID | Feature | Preconditions | Stimulus | Test Steps | Expected Result | Coverage Bin | Priority |
# - Include a header row and separator row, then at least 8 scenario rows.
# - Provide explicit preconditions, concrete test steps (numbered or short bulleted steps), and a clear expected result per scenario.
# - Example minimal table content (single-line JSON string; newlines are escaped as \n):
# Action Input: {"outdir": "output", "content": "| Scenario ID | Feature | Preconditions | Stimulus | Test Steps | Expected Result | Coverage Bin | Priority |\n|---|---|---|---|---|---|---|---|\n| T001 | Handshake | Reset complete | Normal request | 1) Drive valid request 2) Observe response | Response within 3 cycles | fsm_states | high |\n| T002 | Burst transfer | Addr aligned | Burst of 4 beats | 1) Issue burst; 2) Check data order | All beats transferred correctly | burst_lengths | medium |..."}





TASK_PROMPT = """
Task: Generate a verification README and test matrix for this specification.

Spec:
{spec}

Instructions:
1. First, call write_readme with the COMPLETE README content
2. Then, call write_testmatrix with the COMPLETE test matrix table
3. Only after BOTH files are written, say "Final Answer: Files generated"

Remember: NO markdown code blocks in Action Input. Use plain JSON dict format.

Example format:
Thought: I need to create the README file first
Action: write_readme
Action Input: {{"outdir": "output", "content": "# Project README\\n\\nProject details here..."}}

Begin now:
"""