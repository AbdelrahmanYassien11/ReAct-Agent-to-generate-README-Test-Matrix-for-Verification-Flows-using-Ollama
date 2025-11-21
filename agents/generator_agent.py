"""
agents/generator_agent.py

Top-level agent glue that wires the ReAct executor, prompts, tools and LLM.
"""
from llm_ollama import OllamaLLM
from agent_loop import ReActExecutor
from tools import TOOL_REGISTRY
from prompts import SYSTEM_PROMPT, TASK_PROMPT
from utils import safe_write
import json

class GeneratorAgent:
    def __init__(self, model: str = "phi3", outdir: str = "output"):
        self.llm = OllamaLLM(model=model)
        self.outdir = outdir
        self.executor = ReActExecutor(llm_call=self.llm, tools=TOOL_REGISTRY)

    def run(self, spec: dict):
        system_prompt = SYSTEM_PROMPT + "\n" + TASK_PROMPT
        res = self.executor.run(system_prompt, spec)
        # save history optionally
        safe_write(f"{self.outdir}/last_response.txt", json.dumps(res, indent=2))
        # return paths if tools wrote files
        return [f"{self.outdir}/README_generated.md", f"{self.outdir}/TEST_MATRIX_generated.md"]

    def explain(self, spec: dict):
        # call explain tool directly via LLM-friendly prompt
        prompt = "Explain the verification plan briefly:\n" + str(spec)
        return self.llm(prompt)

    def debug(self, spec: dict):
        prompt = "Debug the verification plan for obvious issues:\n" + str(spec)
        return self.llm(prompt)

    def rerun_from_response(self, spec: dict, previous_response: str):
        # run executor again seeded with previous response appended to system prompt
        system_prompt = SYSTEM_PROMPT + "\nSeeded with previous_response:\n" + previous_response + "\n" + TASK_PROMPT
        res = self.executor.run(system_prompt, spec)
        safe_write(f"{self.outdir}/last_response_rerun.txt", json.dumps(res, indent=2))
        return [f"{self.outdir}/README_generated.md", f"{self.outdir}/TEST_MATRIX_generated.md"]
