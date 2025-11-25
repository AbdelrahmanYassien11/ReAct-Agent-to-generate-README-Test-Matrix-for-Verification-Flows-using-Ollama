"""
agent_loop.py - ReAct executor with full observability and failure tracking
"""

import re
import json
import os
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from tools import reset_state


class ReActExecutor:
    def __init__(
        self,
        llm_call: Callable,
        tools: Dict,
        max_steps: int = 25,
        content_llm: Callable = None,
    ):
        self.llm = llm_call
        self.content_llm = content_llm or llm_call
        self.tools = tools
        self.max_steps = max_steps
        self.history = []
        self.failures = []

    def _parse_action(self, text: str) -> Optional[str]:
        match = re.search(r"Action:\s*(\w+)", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _parse_action_input(self, text: str) -> Dict[str, Any]:
        match = re.search(
            r"Action Input:\s*(\{[^}]*\})", text, re.IGNORECASE | re.DOTALL
        )
        if not match:
            match = re.search(r"Action Input:\s*(\{[\s\S]*?\})", text, re.IGNORECASE)

        if match:
            json_str = match.group(1).strip()
            json_str = re.sub(r"```json|```|`", "", json_str)
            json_str = json_str.replace("\n", " ")

            try:
                return json.loads(json_str)
            except:
                try:
                    json_str = json_str.replace("'", '"')
                    return json.loads(json_str)
                except:
                    pass

        return {}

    def run(self, system_prompt: str, spec_path: str, outdir: str = "output") -> dict:
        reset_state()

        # Setup directories
        os.makedirs(outdir, exist_ok=True)
        os.makedirs(f"{outdir}/steps", exist_ok=True)

        # Start progress tracking
        progress_path = f"{outdir}/progress.md"
        with open(progress_path, "w", encoding="utf-8") as p:
            p.write(f"# ReAct Agent Execution\n\n")
            p.write(f"**Spec:** `{spec_path}`\n")
            p.write(f"**Started:** {datetime.utcnow().isoformat()}Z\n")
            p.write(f"**Max Steps:** {self.max_steps}\n\n")

        prompt = system_prompt

        for step in range(self.max_steps):
            step_num = step + 1
            print(f"\n{'='*60}")
            print(f"STEP {step_num}/{self.max_steps}")
            print(f"{'='*60}")

            # ========================================
            # LLM CALL
            # ========================================
            try:
                response = self.llm(prompt)
            except Exception as e:
                error_msg = f"LLM call failed: {str(e)}"
                self.failures.append(
                    {"step": step_num, "type": "llm_error", "message": error_msg}
                )
                print(f"✗ {error_msg}")

                # Save error
                with open(f"{outdir}/steps/step_{step_num:02d}_ERROR.txt", "w") as f:
                    f.write(f"LLM Error: {error_msg}\n")

                return {
                    "status": "FAILED",
                    "failure_reason": "LLM call error",
                    "failed_at_step": step_num,
                    "failures": self.failures,
                    "history": self.history,
                    "steps": step_num,
                }

            # Save LLM response
            with open(
                f"{outdir}/steps/step_{step_num:02d}_llm.txt", "w", encoding="utf-8"
            ) as f:
                f.write(response)

            display = response[:300] + "..." if len(response) > 300 else response
            print(f"\nAgent response:\n{display}")

            self.history.append(("llm", response))

            # ========================================
            # CHECK FOR COMPLETION
            # ========================================
            if "Final Answer:" in response:
                final = re.search(
                    r"Final Answer:\s*(.+)", response, re.IGNORECASE | re.DOTALL
                )
                if final:
                    final_text = final.group(1).strip()
                    print(f"\n✓ COMPLETED: {final_text[:150]}")

                    # Update progress
                    with open(progress_path, "a", encoding="utf-8") as p:
                        p.write(f"\n## ✓ COMPLETED at Step {step_num}\n")
                        p.write(f"**Final Answer:** {final_text[:200]}\n")

                    return {
                        "status": "SUCCESS",
                        "final_answer": final_text,
                        "history": self.history,
                        "failures": self.failures,
                        "steps": step_num,
                    }

            # ========================================
            # PARSE ACTION
            # ========================================
            action = self._parse_action(response)
            action_input = self._parse_action_input(response)

            print(f"\nAction: {action}")
            print(f"Input keys: {list(action_input.keys())}")

            if not action:
                error_msg = "No action found in response"
                self.failures.append(
                    {"step": step_num, "type": "parse_error", "message": error_msg}
                )
                observation = {"error": error_msg}
                print(f"✗ {error_msg}")
            else:
                tool = self.tools.get(action)
                if not tool:
                    error_msg = f"Unknown tool '{action}'"
                    available = ", ".join(self.tools.keys())
                    self.failures.append(
                        {
                            "step": step_num,
                            "type": "unknown_tool",
                            "action": action,
                            "available_tools": list(self.tools.keys()),
                        }
                    )
                    observation = {"error": f"{error_msg}. Available: {available}"}
                    print(f"✗ {error_msg}")
                else:
                    # ========================================
                    # EXECUTE TOOL
                    # ========================================
                    try:
                        # Inject content_llm for tools that need it
                        if action in [
                            "extract_test_requirements",
                            "generate_test_scenario",
                        ]:
                            action_input["content_llm"] = self.content_llm

                        observation = tool(action_input)

                        # Check if tool returned error
                        if isinstance(observation, dict) and "error" in observation:
                            self.failures.append(
                                {
                                    "step": step_num,
                                    "type": "tool_error",
                                    "action": action,
                                    "error": observation["error"],
                                }
                            )
                            print(f"✗ Tool error: {observation['error']}")
                        elif isinstance(observation, str) and observation.startswith(
                            "[Error"
                        ):
                            self.failures.append(
                                {
                                    "step": step_num,
                                    "type": "tool_error",
                                    "action": action,
                                    "error": observation,
                                }
                            )
                            print(f"✗ Tool error: {observation}")
                        else:
                            # Success - write file if returned
                            if (
                                isinstance(observation, dict)
                                and "filename" in observation
                            ):
                                file_path = os.path.join(
                                    outdir, observation["filename"]
                                )
                                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.write(observation["content"])
                                print(f"✓ Wrote: {file_path}")
                            else:
                                print(f"✓ Tool succeeded")

                    except Exception as e:
                        error_msg = f"Tool execution exception: {str(e)}"
                        self.failures.append(
                            {
                                "step": step_num,
                                "type": "tool_exception",
                                "action": action,
                                "exception": str(e),
                            }
                        )
                        observation = {"error": error_msg}
                        print(f"✗ {error_msg}")

            # ========================================
            # SAVE OBSERVATION
            # ========================================
            obs_path = f"{outdir}/steps/step_{step_num:02d}_tool.json"
            with open(obs_path, "w", encoding="utf-8") as f:
                if isinstance(observation, dict):
                    json.dump(observation, f, indent=2)
                else:
                    json.dump({"observation": observation}, f, indent=2)

            self.history.append(("tool", observation))

            # ========================================
            # UPDATE PROGRESS LOG
            # ========================================
            with open(progress_path, "a", encoding="utf-8") as p:
                status_icon = (
                    "✗"
                    if (isinstance(observation, dict) and "error" in observation)
                    else "✓"
                )
                p.write(f"\n## {status_icon} Step {step_num}\n")
                p.write(f"- **Action:** `{action}`\n")

                # Filter out non-serializable objects before logging
                log_input = {
                    k: v for k, v in action_input.items() if k != "content_llm"
                }
                p.write(f"- **Input:** `{json.dumps(log_input)[:100]}`\n")

                if isinstance(observation, dict) and "error" in observation:
                    p.write(f"- **Error:** {observation['error']}\n")
                elif isinstance(observation, dict) and "filename" in observation:
                    p.write(f"- **Output:** `{observation['filename']}`\n")
                p.write(f"- **Details:** `{obs_path}`\n")

            # ========================================
            # BUILD NEXT PROMPT
            # ========================================
            obs_str = (
                json.dumps(observation)[:1000]
                if isinstance(observation, dict)
                else str(observation)[:1000]
            )
            prompt += f"\n{response}\nObservation: {obs_str}\n\n"

            # Context management
            if len(prompt) > 5000:
                prompt = (
                    system_prompt
                    + "\n\n[Earlier steps omitted for brevity]\n\n"
                    + prompt[-3000:]
                )

        # ========================================
        # MAX STEPS REACHED
        # ========================================
        print(f"\n✗ FAILED: Max steps ({self.max_steps}) reached without completion")

        with open(progress_path, "a", encoding="utf-8") as p:
            p.write(f"\n## ✗ FAILED - Max Steps Reached\n")
            p.write(f"Agent did not complete task in {self.max_steps} steps\n")

        return {
            "status": "FAILED",
            "failure_reason": "max_steps_reached",
            "failed_at_step": self.max_steps,
            "failures": self.failures,
            "history": self.history,
            "steps": self.max_steps,
        }
