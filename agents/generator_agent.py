"""
agents/generator_agent.py - TRUE ReAct agent with comprehensive failure reporting
"""

from llm_ollama import OllamaLLM
from agent_loop import ReActExecutor
from tools import TOOL_REGISTRY
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
            max_steps=25,
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
                    "steps_taken": result["steps"],
                    "max_steps": self.executor.max_steps,
                    "failures_count": len(result.get("failures", [])),
                    "failures": result.get("failures", []),
                    "final_answer": result.get("final_answer", "")[:500],
                },
                indent=2,
            ),
        )

        # ========================================
        # PRINT RESULTS
        # ========================================
        print(f"\n{'='*60}")
        print(f"EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Status: {result['status']}")
        print(f"Steps: {result['steps']}/{self.executor.max_steps}")

        failures = result.get("failures", [])
        if failures:
            print(f"\n⚠ Failures encountered: {len(failures)}")
            for i, failure in enumerate(failures[:5], 1):  # Show first 5
                print(
                    f"  {i}. Step {failure.get('step')}: {failure.get('type')} - {failure.get('message', failure.get('error', 'Unknown'))}"
                )
            if len(failures) > 5:
                print(f"  ... and {len(failures) - 5} more (see {summary_path})")

        # ========================================
        # CHECK OUTPUT FILES
        # ========================================
        test_matrix_path = f"{self.outdir}/TEST_MATRIX.md"
        files_generated = []

        if os.path.exists(test_matrix_path):
            files_generated.append(test_matrix_path)
            print(f"\n✓ Test matrix generated: {test_matrix_path}")
        else:
            print(f"\n✗ Test matrix NOT generated")

        # Check for other outputs
        for subdir in ["parsed_spec", "requirements", "scenarios"]:
            subdir_path = f"{self.outdir}/{subdir}"
            if os.path.exists(subdir_path):
                files = [
                    f for f in os.listdir(subdir_path) if f.endswith((".json", ".md"))
                ]
                if files:
                    print(f"✓ {subdir}: {len(files)} files")
                    files_generated.extend([f"{subdir_path}/{f}" for f in files])

        # ========================================
        # FINAL VERDICT
        # ========================================
        print(f"\n{'='*60}")
        if result["status"] == "SUCCESS" and os.path.exists(test_matrix_path):
            print(f"✓✓✓ SUCCESS - Test matrix generated successfully!")
            print(f"{'='*60}")
            return files_generated
        elif result["status"] == "SUCCESS":
            print(f"⚠⚠⚠ PARTIAL SUCCESS - Agent completed but no test matrix found")
            print(f"{'='*60}")
            return files_generated
        else:
            print(f"✗✗✗ FAILED - Agent did not complete task")
            print(f"Reason: {result.get('failure_reason', 'Unknown')}")
            if failures:
                print(f"Failed at step: {result.get('failed_at_step')}")
                print(
                    f"Last error: {failures[-1].get('message', failures[-1].get('error', 'Unknown'))}"
                )
            print(f"\nCheck these files for details:")
            print(f"  - {self.outdir}/progress.md")
            print(f"  - {summary_path}")
            print(f"  - {self.outdir}/steps/ (individual step outputs)")
            print(f"{'='*60}")
            return []

    def explain(self, spec_path):
        return f"""TRUE ReAct Agent (4 Tools)

Spec: {spec_path}
Routing: {self.llm.model}
Content: {self.content_llm.model}

Tools:
1. parse_spec - Parse file
2. extract_test_requirements - Analyze feature (LLM)
3. generate_test_scenario - Create scenario (LLM)
4. format_and_write - Write markdown

Output Structure:
- progress.md - Step-by-step progress log
- execution_summary.json - Final status and failures
- steps/ - Individual step outputs
- parsed_spec/ - Parsed specification
- requirements/ - Test requirements per feature
- scenarios/ - Individual test scenarios
- TEST_MATRIX.md - Final output"""
