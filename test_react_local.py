from agent_loop import ReActExecutor
from tools import TOOL_REGISTRY

# Mock LLM responses: first response contains two actions + Final Answer
responses = [
    """
Thought: I will create a README and then a test matrix.
Action: write_readme
Action Input: {"outdir": "output", "content": "# Sample README\nThis is a test."}

Action: write_testmatrix
Action Input: {"outdir": "output", "content": "# Test Matrix\n|Feature|Coverage|\n|f|c|"}

Final Answer: Files generated
""",
    # A subsequent reply (if the executor asks again) - should be ignored because final should have returned
    "Final Answer: Files generated"
]

def make_llm(resps):
    # return a callable that pops from responses
    def llm(prompt: str) -> str:
        if resps:
            return resps.pop(0)
        return "Final Answer: Files generated"
    return llm

if __name__ == '__main__':
    llm = make_llm(responses)
    exec = ReActExecutor(llm_call=llm, tools=TOOL_REGISTRY, max_steps=4)
    spec = {"project_name": "test"}
    out = exec.run("System prompt placeholder", spec)
    print("EXECUTOR OUTPUT:", out)
