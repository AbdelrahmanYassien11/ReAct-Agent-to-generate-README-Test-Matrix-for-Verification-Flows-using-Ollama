"""
agents/generator_agent.py - TRUE ReAct agent with comprehensive debugging
"""

from llm_ollama import OllamaLLM
from agent_loop import ReActExecutor
from agent_tools.tools import TOOL_REGISTRY
from prompts import SYSTEM_PROMPT, TASK_PROMPT
from utils import safe_write
import json
import os


class GeneratorAgent:
    def __init__(self, model="llama3.2", content_model=None, outdir="output"):
        self.llm = OllamaLLM(model=model)
        self.content_llm = OllamaLLM(model=content_model or model)
        self.outdir = outdir
        self.executor = ReActExecutor(
            llm_call=self.llm,
            tools=TOOL_REGISTRY,
            max_steps=4,  # 4 tools + final answer + 1 buffer
            content_llm=self.content_llm,
        )
        print(f"Agent initialized:")
        print(f"  Routing: {model}")
        print(f"  Content: {content_model or model}")
        print(f"  Tools: {', '.join(TOOL_REGISTRY.keys())}")

    def run(self, spec_path):
        prompt = SYSTEM_PROMPT + "\n" + TASK_PROMPT.format(spec_path=spec_path)

        print(f"\n{'='*60}")
        print(f"TRUE ReAct Agent - Starting")
        print(f"{'='*60}")
        print(f"Spec: {spec_path}")
        print(f"Output dir: {self.outdir}")
        print(f"Max steps: {self.executor.max_steps}\n")

        result = self.executor.run(prompt, spec_path, self.outdir)

        # ========================================
        # SAVE EXECUTION SUMMARY
        # ========================================
        summary_path = f"{self.outdir}/execution_summary.json"
        safe_write(
            summary_path,
            json.dumps(
                {
                    "status": result["status"],
                    "steps_taken": result.get("steps", 0),
                    "max_steps": self.executor.max_steps,
                    "failures_count": len(result.get("failures", [])),
                    "failures": result.get("failures", []),
                    "final_answer": result.get("final_answer", "")[:500],
                    "error": result.get("error", ""),
                },
                indent=2,
            ),
        )

        # ========================================
        # PRINT DETAILED RESULTS
        # ========================================
        print(f"\n{'='*60}")
        print(f"EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Status: {result['status']}")
        print(f"Steps: {result.get('steps', 0)}/{self.executor.max_steps}")

        if result.get("error"):
            print(f"Error: {result['error']}")

        failures = result.get("failures", [])
        if failures:
            print(f"\nFailures encountered: {len(failures)}")
            for i, failure in enumerate(failures, 1):
                print(f"\n  Failure {i}:")
                print(f"    Step: {failure.get('step')}")
                print(f"    Action: {failure.get('action')}")
                print(f"    Type: {failure.get('type')}")
                print(f"    Error: {failure.get('error')}")
                if i >= 5:
                    print(f"\n  ... and {len(failures) - 5} more (see {summary_path})")
                    break

        # ========================================
        # CHECK OUTPUT FILES
        # ========================================
        print(f"\n{'='*60}")
        print(f"OUTPUT FILES CHECK")
        print(f"{'='*60}")

        test_matrix_path = f"{self.outdir}/TEST_MATRIX.md"
        files_generated = []

        # Check test matrix
        if os.path.exists(test_matrix_path):
            files_generated.append(test_matrix_path)
            size = os.path.getsize(test_matrix_path)
            print(f"[OK] TEST_MATRIX.md exists ({size} bytes)")
        else:
            print(f"[MISSING] TEST_MATRIX.md NOT found")

        # Check intermediate outputs
        intermediate_files = {
            "parsed_spec.json": "Parsed specification",
            "test_requirements.json": "Test requirements",
            "test_scenarios.json": "Test scenarios",
        }

        print(f"\nIntermediate files:")
        for filename, description in intermediate_files.items():
            filepath = f"{self.outdir}/{filename}"
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  [OK] {filename} ({size} bytes) - {description}")
                files_generated.append(filepath)
            else:
                print(f"  [MISSING] {filename} - {description}")

        # Check step outputs
        steps_dir = f"{self.outdir}/steps"
        if os.path.exists(steps_dir):
            step_files = [
                f for f in os.listdir(steps_dir) if f.endswith((".json", ".txt"))
            ]
            print(f"\nStep outputs: {len(step_files)} files in {steps_dir}/")
            if step_files:
                print(f"  Latest: {sorted(step_files)[-1]}")

        # ========================================
        # DIAGNOSE WHY IT FAILED
        # ========================================
        if result["status"] != "SUCCESS":
            print(f"\n{'='*60}")
            print(f"FAILURE DIAGNOSIS")
            print(f"{'='*60}")

            # Check which step failed
            if failures:
                last_failure = failures[-1]
                print(f"Last failure at step {last_failure.get('step')}:")
                print(f"  Action: {last_failure.get('action')}")
                print(f"  Error: {last_failure.get('error')}")

                # Check the tool output file
                step_num = last_failure.get("step")
                tool_file = f"{self.outdir}/steps/step_{step_num:02d}_tool.json"
                if os.path.exists(tool_file):
                    print(f"\n  Tool output saved to: {tool_file}")
                    with open(tool_file, "r", encoding="utf-8") as f:
                        tool_output = json.load(f)
                        print(f"  Tool response: {json.dumps(tool_output, indent=4)}")

            # Suggest next steps
            print(f"\nDebugging suggestions:")
            print(f"  1. Check {self.outdir}/steps/ for detailed step outputs")
            print(f"  2. Check {summary_path} for full execution details")
            print(f"  3. Look at the routing model responses in step_XX_routing.txt")
            print(f"  4. Look at the tool responses in step_XX_tool.json")

        # ========================================
        # FINAL VERDICT
        # ========================================
        print(f"\n{'='*60}")
        if result["status"] == "SUCCESS" and os.path.exists(test_matrix_path):
            print(f"SUCCESS - Test matrix generated successfully!")
            print(f"{'='*60}")
            return files_generated
        elif result["status"] == "SUCCESS":
            print(f"PARTIAL SUCCESS - Agent completed but no test matrix found")
            print(f"{'='*60}")
            return files_generated
        else:
            print(f"FAILED - Agent did not complete task")
            print(f"{'='*60}")
            return []

    def explain(self, spec_path):
        return f"""TRUE ReAct Agent (4 Tools)

Spec: {spec_path}
Routing: {self.llm.model}
Content: {self.content_llm.model}

Tools:
1. parse_spec - Parse file (content model)
2. extract_test_requirements - Analyze features (content model)
3. generate_test_scenarios - Create scenarios (content model)
4. format_and_write - Write markdown (no LLM)

Output Structure:
- execution_summary.json - Final status and failures
- steps/ - Individual step outputs (routing + tool)
- 01_parsed_spec.json - Parsed specification
- 02_test_requirements.json - Test requirements
- 03_test_scenarios.json - Test scenarios
- TEST_MATRIX.md - Final output"""
