# Code Overview — beginner-friendly guide

This file explains the purpose and relationships of the main files in this repository, and how to run and debug the ReAct-style Ollama agent. It's written for engineers new to Python and AI agents.

Repository purpose
- This project runs a ReAct-style AI agent (local Ollama model) that reads a Python `spec` dictionary and generates two files:
  - `output/README_generated.md` — a verification README describing the plan
  - `output/TEST_MATRIX_generated.md` — a test matrix listing scenarios and expected results

Key files and what they do
- `agent_loop.py` — ReAct executor (core loop)
  - Calls the LLM with a system + task prompt, parses model replies for `Thought:`, `Action:`, and `Action Input:`.
  - Executes tools from `tools.py` and appends observations to the prompt so the agent can iterate.
  - Contains parsing heuristics for extracting JSON-like `Action Input` blocks and infers tools when missing.

- `prompts.py` — system and task prompts
  - `SYSTEM_PROMPT` and `TASK_PROMPT` control how the model should format responses.
  - This project uses strict format enforcement: the model should reply with `Thought:`, `Action:`, and `Action Input: {...}`.
  - Prompts now explicitly require the README and test matrix be placed inside a `content` field of `Action Input` so the executor can parse reliably.

- `tools.py` — available tools the agent may call
  - `write_readme` and `write_testmatrix` write files in the `output` folder.
  - `explain` and `debug` provide small, internal helpers for reasoning about the spec.
  - Tools accept a single dict argument and return a string observation (success/error message).

- `llm_ollama.py` — Ollama CLI wrapper
  - Calls the `ollama` CLI: `ollama run <model>` via `subprocess.run`.
  - If `ollama` is not installed, it returns a helpful message string instead of raising.

- `agents/generator_agent.py` — high-level glue
  - Creates the LLM wrapper, the `ReActExecutor`, and exposes `run`, `explain`, `debug`, and `rerun_from_response` methods.
  - Writes `output/last_response.txt` (history) for debugging.

- `main.py` and `cli.py` — command-line entrypoints
  - `main.py` uses `argparse`; `cli.py` uses `click` for convenience.
  - Typical commands:
    - `python main.py generate --spec examples/example_spec.py --model phi3:latest --outdir output`
    - or `python cli.py generate examples/example_spec.py --outdir output`

- `utils.py` — small helpers
  - `load_spec(path)` executes the Python file and returns the top-level `spec` dict.
  - `safe_write(path, content)` writes files creating directories as needed.

- `examples/example_spec.py` — spec format example
  - Define a top-level `spec` dict with keys such as `project_name`, `dut`, `features`, and `coverage`.

- `test_react_local.py` — mocked LLM test
  - A small script that simulates LLM responses (useful for offline testing without Ollama).

- `output/` — runtime artifacts
  - `last_response.txt` — saved LLM + tool execution history (first place to check on failures)
  - `README_generated.md`, `TEST_MATRIX_generated.md` — files produced by the agent

How the data flows (high-level)
1. `main.py` or `cli.py` loads the spec via `utils.load_spec`.
2. `GeneratorAgent` creates an `OllamaLLM` instance and `ReActExecutor`.
3. `ReActExecutor` sends the composed prompt (system + task + SPEC) to the LLM.
4. The model replies with `Action:` and `Action Input:` blocks.
5. The executor parses these, calls the corresponding tool from `tools.py`, and appends the observation to the prompt for the next step. This loop continues until the model emits `Final Answer:` or max steps are reached.

Debugging tips (practical)
- If files are missing: open `output/last_response.txt` and inspect the LLM's last reply and tool observations.
- Common parser failure modes:
  - The model writes the README content as separate key/value lines instead of a single `content` string. Fix: adjust `prompts.py` to insist the README/test-matrix be inside `"content"`.
  - The model uses markdown code fences around JSON — the executor tries to strip fences but check `Action Input:` formatting.
- Check `tools.py` error messages: they now include `input_keys` and `content_repr` to show what was actually passed.

Beginner Python notes
- To run the agent locally, create a virtual environment and install the dependency `click` (optional):
  ```powershell
  python -m venv .venv; .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
- If you don't have Ollama installed, `llm_ollama.py` returns a friendly error: install and pull `phi3:latest`.

Recommended iterative workflow
1. Run the agent: `python main.py generate --spec examples/example_spec.py --model phi3:latest --outdir output`.
2. If content is missing or low quality, open `output/last_response.txt` and see what the LLM returned.
3. Improve `prompts.py` — add stricter examples/templates and rerun.
4. Repeat until the generated README and TEST_MATRIX look correct.

If you'd like, I can also add inline docstrings/comments to specific Python files explaining function-by-function behavior; tell me which files you want annotated and I will add short, clear comments.
