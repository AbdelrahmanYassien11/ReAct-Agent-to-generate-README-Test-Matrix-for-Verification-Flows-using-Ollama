"""
agent_loop.py - Optimized ReAct executor
Faster parsing, better context management
"""
import re
import json
from typing import Callable, Dict, Any, Optional
from tools import reset_scenario_buffer

class ReActExecutor:
    def __init__(self, llm_call: Callable, tools: Dict, max_steps: int = 30, content_llm: Callable = None):
        self.llm = llm_call
        self.content_llm = content_llm or llm_call
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def _parse_action(self, text: str) -> Optional[str]:
        match = re.search(r'Action:\s*(\w+)', text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _parse_action_input(self, text: str) -> Dict[str, Any]:
        # Find Action Input block
        match = re.search(r'Action Input:\s*(\{[^}]*\})', text, re.IGNORECASE | re.DOTALL)
        if not match:
            # Try multiline
            match = re.search(r'Action Input:\s*(\{[\s\S]*?\n\})', text, re.IGNORECASE)
        
        if match:
            json_str = match.group(1).strip()
            json_str = re.sub(r'```json|```', '', json_str)
            json_str = json_str.replace('\n', ' ')
            
            try:
                return json.loads(json_str)
            except:
                try:
                    json_str = json_str.replace("'", '"')
                    return json.loads(json_str)
                except:
                    pass
        
        return {}

    def run(self, system_prompt: str, spec_path: str) -> dict:
        reset_scenario_buffer()
        
        prompt = system_prompt
        
        for step in range(self.max_steps):
            print(f"\n{'='*60}")
            print(f"STEP {step + 1}/{self.max_steps}")
            print(f"{'='*60}")
            
            response = self.llm(prompt)
            
            # Truncate very long responses
            display = response[:400] + "..." if len(response) > 400 else response
            print(f"\nAgent: {display}")
            
            self.history.append(("llm", response))
            
            # Check for completion
            if "Final Answer:" in response:
                final_match = re.search(r'Final Answer:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
                if final_match:
                    final_text = final_match.group(1).strip()[:200]
                    print(f"\n✓ COMPLETE: {final_text}")
                    return {
                        "status": "success",
                        "final_answer": final_text,
                        "history": self.history,
                        "steps": step + 1
                    }
            
            # Parse and execute
            action = self._parse_action(response)
            action_input = self._parse_action_input(response)
            
            print(f"Action: {action}")
            print(f"Input: {list(action_input.keys())}")
            
            if not action:
                observation = "[Error: No action found. Use format 'Action: tool_name']"
            else:
                tool = self.tools.get(action)
                if not tool:
                    observation = f"[Error: Unknown tool '{action}']"
                else:
                    try:
                        # Inject content_llm only where needed
                        if action == "generate_scenario":
                            action_input["content_llm"] = self.content_llm
                        
                        observation = tool(action_input)
                        
                        # Truncate long observations
                        display_obs = observation[:300] + "..." if len(observation) > 300 else observation
                        print(f"Result: {display_obs}")
                    except Exception as e:
                        observation = f"[Error: {str(e)[:100]}]"
                        print(f"Error: {observation}")
            
            self.history.append(("tool", observation))
            
            # Build next prompt - keep it concise
            prompt += f"\n{response}\nObservation: {observation}\n\n"
            
            # Truncate context if getting too long (keep last 3000 chars)
            if len(prompt) > 3000:
                prompt = system_prompt + "\n\n[Previous steps truncated]\n\n" + prompt[-2000:]
        
        print(f"\n⚠ Max steps reached")
        return {
            "status": "max_steps_reached",
            "final_answer": "[Incomplete]",
            "history": self.history,
            "steps": self.max_steps
        }