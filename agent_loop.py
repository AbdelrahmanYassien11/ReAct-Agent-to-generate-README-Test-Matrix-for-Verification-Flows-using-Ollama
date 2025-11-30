"""
agent_loop.py - ReAct executor with dual-model architecture
ROUTING MODEL: Used only for orchestration (this loop)
CONTENT MODEL: Injected into tools for content generation
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
        max_steps: int = 6,
        content_llm: Callable = None,
    ):
        """
        Initialize ReAct executor with dual-model setup.

        Args:
            llm_call: ROUTING MODEL - for orchestration/ReAct decisions only
            tools: Dictionary of available tools
            max_steps: Maximum number of steps
            content_llm: CONTENT MODEL - for actual content generation in tools
        """
        self.llm = llm_call  # ROUTING MODEL - orchestration only
        self.content_llm = content_llm or llm_call  # CONTENT MODEL - content generation
        self.tools = tools
        self.max_steps = max_steps
        self.history = []
        self.failures = []

        print(f"\nReAct Executor initialized:")
        print(
            f"  Routing model: {getattr(llm_call, 'model', 'unknown')} (orchestration)"
        )
        print(
            f"  Content model: {getattr(self.content_llm, 'model', 'unknown')} (generation)"
        )

    # ---------------------------------------------------------
    # Parse: Action
    # ---------------------------------------------------------
    def _parse_action(self, text: str) -> Optional[str]:
        match = re.search(r"Action:\s*(\w+)", text)
        return match.group(1).strip() if match else None

    # ---------------------------------------------------------
    # Parse: Action Input JSON
    # ---------------------------------------------------------
    def _parse_action_input(self, text: str) -> Dict[str, Any]:
        match = re.search(r"Action Input:\s*(\{[\s\S]*?\})", text)
        if not match:
            return {}
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except:
            try:
                return json.loads(json_str.replace("'", '"'))
            except:
                return {}

    # ---------------------------------------------------------
    # Main ReAct Loop (ROUTING MODEL ONLY)
    # ---------------------------------------------------------
    def run(self, system_prompt: str, spec_path: str, outdir: str = "output") -> dict:
        reset_state()

        os.makedirs(outdir, exist_ok=True)
        os.makedirs(f"{outdir}/steps", exist_ok=True)

        prompt = system_prompt.replace("{spec_path}", spec_path)

        for step in range(self.max_steps):
            step_num = step + 1
            print(f"\n{'='*60}")
            print(f"STEP {step_num}/{self.max_steps}")
            print(f"{'='*60}")

            # ----------------------------------------------
            # 1. CALL ROUTING MODEL (orchestration only)
            # ----------------------------------------------
            try:
                print("Calling ROUTING model for orchestration decision...")
                response = self.llm(prompt)
                print(f"  Routing decision made: {response[:150]}...")
            except Exception as e:
                error_msg = f"Routing model error: {str(e)}"
                print(f"ERROR: {error_msg}")
                return {"status": "FAILED", "error": error_msg, "steps": step_num}

            self.history.append(("routing_llm", response))

            # Save routing model output
            with open(
                f"{outdir}/steps/step_{step_num:02d}_routing.txt", "w", encoding="utf-8"
            ) as f:
                f.write(response)

            # Check Final Answer
            if "Final Answer:" in response:
                final_text = response.split("Final Answer:")[1].strip()
                print(f"\nFINAL ANSWER RECEIVED at step {step_num}")
                print(f"  {final_text[:200]}...")

                # Check if this is premature (no tools executed yet)
                if step_num == 1:
                    print(
                        f"\nERROR: Routing model provided Final Answer WITHOUT executing any tools!"
                    )
                    print(
                        f"  This is a routing model failure - it should call tools first."
                    )
                    print(f"  The model is not following the ReAct format.")
                    return {
                        "status": "FAILED",
                        "error": "Routing model gave Final Answer without executing tools",
                        "final_answer": final_text,
                        "steps": step_num,
                        "failures": [
                            {
                                "step": step_num,
                                "type": "premature_final_answer",
                                "error": "Routing model did not follow ReAct format - gave Final Answer without calling any tools",
                            }
                        ],
                    }

                # Otherwise it's legitimate
                return {
                    "status": "SUCCESS",
                    "final_answer": final_text,
                    "steps": step_num,
                    "failures": self.failures,
                }

            # ----------------------------------------------
            # 2. PARSE ACTION (from routing model decision)
            # ----------------------------------------------
            action = self._parse_action(response)
            action_input = self._parse_action_input(response)

            if not action:
                error_msg = "No Action found in routing model response"
                print(f"\nERROR: {error_msg}")
                print(f"  Routing model response didn't contain 'Action: tool_name'")
                print(f"  Response preview: {response[:500]}")
                return {
                    "status": "FAILED",
                    "error": error_msg,
                    "steps": step_num,
                    "failures": [
                        {
                            "step": step_num,
                            "type": "no_action_found",
                            "error": error_msg,
                            "response_preview": response[:500],
                        }
                    ],
                }

            tool = self.tools.get(action)
            if not tool:
                error_msg = f"Unknown tool: {action}"
                print(f"ERROR: {error_msg}")
                return {"status": "FAILED", "error": error_msg, "steps": step_num}

            print(f"\nExecuting tool: {action}")
            print(f"  Action input keys: {list(action_input.keys())}")
            if not action_input or (len(action_input) == 0):
                print(f"  WARNING: Action Input is empty!")
                print(f"  Routing model response preview:")
                print(
                    f"  {response[-500:]}"
                )  # Show last 500 chars to see the Action Input
            else:
                print(f"  Action input preview: {str(action_input)[:200]}...")

            # ----------------------------------------------
            # 3. INJECT CONTENT MODEL into tool
            # ----------------------------------------------
            # All tools that need LLM get the CONTENT MODEL
            action_input["content_llm"] = self.content_llm

            # ----------------------------------------------
            # 4. EXECUTE TOOL (with content model)
            # ----------------------------------------------
            try:
                print(f"  Calling tool function with content model...")
                observation = tool(action_input)
                print(f"\nTool Response:")

                if "error" in observation:
                    print(f"  ERROR: {observation['error']}")
                    print(f"  Full observation: {json.dumps(observation, indent=2)}")
                    # Track failure
                    self.failures.append(
                        {
                            "step": step_num,
                            "action": action,
                            "error": observation["error"],
                            "type": "tool_error",
                        }
                    )
                else:
                    print(f"  Tool completed successfully")
                    if "total_features" in observation:
                        print(f"    Features parsed: {observation['total_features']}")
                    if "total_requirements" in observation:
                        print(
                            f"    Requirements generated: {observation['total_requirements']}"
                        )
                    if "total_scenarios" in observation:
                        print(
                            f"    Scenarios generated: {observation['total_scenarios']}"
                        )
                    if "scenarios_count" in observation:
                        print(
                            f"    Scenarios written: {observation['scenarios_count']}"
                        )
                    if "file_path" in observation:
                        print(f"    Output file: {observation['file_path']}")

            except Exception as e:
                observation = {"error": str(e)}
                print(f"  EXCEPTION during tool execution: {str(e)}")
                print(f"  Exception type: {type(e).__name__}")
                import traceback

                print(f"  Traceback:\n{traceback.format_exc()}")
                # Track failure
                self.failures.append(
                    {
                        "step": step_num,
                        "action": action,
                        "error": str(e),
                        "type": "exception",
                    }
                )

            # Save tool output
            with open(
                f"{outdir}/steps/step_{step_num:02d}_tool.json", "w", encoding="utf-8"
            ) as f:
                json.dump(observation, f, indent=2)

            print(f"  Saved tool output to: step_{step_num:02d}_tool.json")

            self.history.append(("tool", observation))

            # ----------------------------------------------
            # 5. BUILD NEXT PROMPT for ROUTING MODEL
            # ----------------------------------------------
            # Pass full observation to routing model so it can extract data
            obs_str = json.dumps(observation)

            prompt += f"\n{response}\n" f"Observation: {obs_str}\n\n"

        error_msg = "Max steps reached without Final Answer"
        print(f"\nERROR: {error_msg}")
        print(f"  Completed {self.max_steps} steps without reaching Final Answer")
        print(f"  Total failures: {len(self.failures)}")
        return {
            "status": "FAILED",
            "error": error_msg,
            "steps": self.max_steps,
            "failures": self.failures,
        }
