"""agent_loop.py

Robust ReAct executor with explicit fallback tool auto-detection (Option A).

Features:
- Extracts Action name if present.
- Parses Action Input robustly (handles code fences, partial JSON).
- If Action name is missing or empty, infers tool from Action Input 'content':
    * If content looks like a README (contains '# Project README' or 'Project Name:')
      -> assume write_readme
    * If content looks like a table (contains markdown table '|' header or '# Test Matrix')
      -> assume write_testmatrix
    * Else, fall back to 'write_readme' for free text content.
- Provides detailed debug prints and returns a history dict.
"""
import re
import json
import ast
from typing import Callable, Dict, Any, Optional

ACTION_RE = re.compile(r"^\s*Action:\s*(\w+)", re.IGNORECASE | re.MULTILINE)
BRACE_RE = re.compile(r"\{[\s\S]*?\}", re.MULTILINE)

def _looks_like_readme(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    # Common README cues
    if '# project readme' in lower or 'project name:' in lower or 'short description' in lower:
        return True
    # If it's free-form markdown (no table) prefer README
    if '|' not in text and len(text.splitlines()) > 3:
        return True
    return False

def _looks_like_testmatrix(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    # Table cues or explicit title
    if '# test matrix' in lower:
        return True
    if '|' in text and ('burst' in lower or 'handshake' in lower or 'feature' in lower):
        return True
    return False

class ReActExecutor:
    def __init__(self, llm_call: Callable[[str], str], tools: Dict[str, Callable[[Dict[str, Any]], str]], max_steps: int = 8):
        self.llm = llm_call
        self.tools = tools
        self.max_steps = max_steps

    def _extract_action(self, text: str) -> Optional[str]:
        m = ACTION_RE.search(text)
        if m:
            return m.group(1).strip()
        # If no clear Action line, look for "Action:" followed by whitespace then a code block/JSON
        for line in text.splitlines():
            if line.strip().lower().startswith('action:'):
                # attempt to find the first word after colon on same line
                parts = line.split(':',1)
                if len(parts) > 1:
                    candidate = parts[1].strip()
                    if candidate:
                        return candidate.split()[0]
                # no candidate on same line
                return None
        return None

    def _find_largest_json_like(self, text: str) -> Optional[str]:
        # Prefer largest balanced {...} block
        candidates = BRACE_RE.findall(text)
        if candidates:
            candidates.sort(key=len, reverse=True)
            return candidates[0]
        # Fallback: look for contiguous lines starting with { until matching }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        return None

    def _parse_action_input(self, text: str) -> Dict[str, Any]:
        # Prefer an explicit "Action Input:" block. Models sometimes emit
        # double-braced JSON like `{{...}}` or include the JSON inside
        # surrounding text/code fences. Try to find the JSON nearest the
        # "Action Input:" token and parse it robustly.
        # Remove common code fence markers to simplify matching.
        cleaned = re.sub(r'```(?:json|python)?', '', text, flags=re.IGNORECASE).strip()

        # Find the first "Action Input:" occurrence and attempt to parse the
        # JSON-like payload that follows it.
        m = re.search(r"Action Input:\s*(?P<after>[\s\S]*)", cleaned, re.IGNORECASE)
        if m:
            after = m.group('after')
            # If model used double braces ({{ .. }}), collapse them to single braces
            after = after.replace('{{', '{').replace('}}', '}')
            # Try to find the largest {...} block in the 'after' text
            candidate = self._find_largest_json_like(after)
            if candidate:
                try:
                    return json.loads(candidate)
                except Exception:
                    try:
                        return ast.literal_eval(candidate)
                    except Exception:
                        pass
            # If there's no {...} block, try to parse a following inline dict-like
            # by collecting lines up to the next blank line or next 'Action'/'Thought'.
            lines = after.splitlines()
            block = []
            for ln in lines:
                if not ln.strip():
                    break
                # stop if next step begins
                if re.match(r'^(Thought:|Action:|Final Answer:)', ln.strip(), re.IGNORECASE):
                    break
                block.append(ln)
            block_text = '\n'.join(block).strip()
            # Collapse double braces in this smaller block too
            block_text = block_text.replace('{{', '{').replace('}}', '}')
            candidate = self._find_largest_json_like(block_text)
            if candidate:
                try:
                    return json.loads(candidate)
                except Exception:
                    try:
                        return ast.literal_eval(candidate)
                    except Exception:
                        pass

        # Fallback: original heuristic key:value extraction across the whole
        # cleaned text, but restrict to short lines to avoid capturing the
        # entire LLM thought as keys.
        heur = {}
        for line in cleaned.splitlines():
            if ':' in line and len(line) < 400:
                k, v = line.split(':', 1)
                key = k.strip().strip('"\'')
                val = v.strip()
                # strip surrounding quotes if present
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                heur[key] = val
        return heur

    def _infer_tool_from_content(self, action_input: Dict[str, Any]) -> Optional[str]:
        content = action_input.get('content') or ''
        if _looks_like_readme(content):
            return 'write_readme'
        if _looks_like_testmatrix(content):
            return 'write_testmatrix'
        # If content is short but includes 'table' or pipes, prefer testmatrix
        if isinstance(content, str) and '|' in content:
            return 'write_testmatrix'
        # default
        return 'write_readme'

    def _extract_actions_and_inputs(self, text: str):
        """Return a list of (action, action_input_dict, raw_ai_text) found in `text`.

        This scans for multiple `Action:` occurrences and captures the nearest
        following `Action Input:` block for each, so a single LLM response that
        contains multiple actions will have them executed in order.
        """
        results = []
        for m in re.finditer(r"^\s*Action:\s*(\w+)", text, re.IGNORECASE | re.MULTILINE):
            action = m.group(1).strip()
            # search for Action Input after this match
            after_pos = m.end()
            ai_m = re.search(r"Action Input:\s*", text[after_pos:], re.IGNORECASE)
            if ai_m:
                ai_start = after_pos + ai_m.end()
                # end at next top-level token or end of text
                end_m = re.search(r"(?m)^\s*(Action:|Thought:|Final Answer:)", text[ai_start:])
                ai_end = ai_start + end_m.start() if end_m else len(text)
                raw_ai = text[ai_start:ai_end]
                parsed = self._parse_action_input("Action Input: " + raw_ai)
            else:
                raw_ai = ''
                parsed = {}
            results.append((action, parsed, raw_ai))
        return results

    def run(self, system_prompt: str, spec: dict):
        prompt = system_prompt + '\n\nSPEC:\n' + json.dumps(spec, indent=2)
        history = []

        for step in range(self.max_steps):
            print(f"\n=== STEP {step+1}/{self.max_steps} ===")
            resp = self.llm(prompt)
            print("LLM Response (preview):\n" + (resp[:500] + '...' if len(resp) > 500 else resp))
            history.append(("LLM", resp))
            # NOTE: Do not treat 'Final Answer:' as terminal before processing
            # any Action lines present in the same LLM response. Some models
            # include multiple actions in one response; extract and execute
            # all Action/Action Input pairs sequentially.
            actions = self._extract_actions_and_inputs(resp)
            if not actions:
                # fallback for older single-action behavior
                action = self._extract_action(resp)
                action_input = self._parse_action_input(resp)
                actions = [(action, action_input, None)]

            observations = []
            for (action, action_input, raw_ai) in actions:
                print("Parsed Action:", action)
                print("Parsed Action Input keys:", list(action_input.keys()))

                if not action:
                    inferred = self._infer_tool_from_content(action_input)
                    print(f"⚠ Action missing in LLM response — inferred '{inferred}' from content.")
                    action = inferred

                tool = self.tools.get(action)
                if not tool:
                    observation = f"[tool_not_found: {action}]"
                    print("✗", observation)
                else:
                    try:
                        observation = tool(action_input)
                        print("✓ Tool observation:", observation[:400] if len(observation) > 400 else observation)
                    except Exception as e:
                        observation = f"[tool_error: {e}]"
                        print("✗ Tool error:", e)

                observations.append(observation)
                history.append(("Tool", observation))

            # Append the response and aggregated observations to the prompt once
            obs_text = "\n".join(["Observation: " + str(o) for o in observations]) + "\n"
            prompt += "\n" + resp + "\n" + obs_text

            # Now check for Final Answer in the response after tools/observations
            if 'Final Answer:' in resp:
                idx = resp.index('Final Answer:') + len('Final Answer:')
                final_text = resp[idx:].strip()
                print(f"✓ Final Answer detected: {final_text[:200]}")
                return {"final": final_text, "history": history}

        print("\n⚠ Max steps reached without Final Answer.")
        return {"final": "[max_steps_reached]", "history": history}
