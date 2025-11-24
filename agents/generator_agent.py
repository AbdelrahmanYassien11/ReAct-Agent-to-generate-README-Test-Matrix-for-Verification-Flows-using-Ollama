"""
agents/generator_agent.py - Optimized TRUE ReAct agent
"""
from llm_ollama import OllamaLLM
from agent_loop import ReActExecutor
from tools import TOOL_REGISTRY
from prompts import SYSTEM_PROMPT, TASK_PROMPT
from utils import safe_write
import json

class GeneratorAgent:
    def __init__(self, model="phi3", content_model=None, outdir="output"):
        self.llm = OllamaLLM(model=model)
        self.content_llm = OllamaLLM(model=content_model or model)
        self.outdir = outdir
        self.executor = ReActExecutor(
            llm_call=self.llm,
            tools=TOOL_REGISTRY,
            max_steps=30,
            content_llm=self.content_llm
        )
        print(f"Agent ready: Routing={model}, Content={content_model or model}")

    def run(self, spec_path):
        prompt = SYSTEM_PROMPT + "\n" + TASK_PROMPT.format(spec_path=spec_path)
        
        print(f"\nStarting ReAct agent")
        print(f"Spec: {spec_path}")
        print(f"Max steps: {self.executor.max_steps}\n")
        
        result = self.executor.run(prompt, spec_path)
        
        # Save history
        history_path = f"{self.outdir}/execution_history.json"
        safe_write(history_path, json.dumps({
            "status": result["status"],
            "steps": result["steps"],
            "final_answer": result["final_answer"][:500],
            "tool_calls": len([h for h in result["history"] if h[0] == "tool"])
        }, indent=2))
        
        print(f"\nStatus: {result['status']}")
        print(f"Steps: {result['steps']}")
        
        return [f"{self.outdir}/TEST_MATRIX.md"] if result["status"] == "success" else []

    def explain(self, spec_path):
        return f"""ReAct Agent
Spec: {spec_path}
Models: {self.llm.model} (routing), {self.content_llm.model} (content)
Flow: load_spec → loop(get_next_task → generate → add) → write_file"""