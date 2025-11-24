# Test Matrix Generator (Ollama)

Simplified AI agent that uses a local Ollama model to generate verification test matrices from a Python spec dictionary.

## Key Changes

✓ Removed README generation - focuses only on test matrix
✓ Removed complex ReAct parsing - expects direct markdown output
✓ Optimized prompt to force model to output ONLY markdown tables
✓ Simplified executor - single LLM call, no iterative loop
✓ Removed unnecessary tools and parsing logic

## Quick Start

1. Install Ollama and pull a model:
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull phi3
```

2. Install optional dependencies:
```bash
pip install click
```

3. Generate test matrix:
```bash
python main.py generate --spec examples/example_spec.py --model phi3 --outdir output
```

Or use the click CLI:
```bash
python cli.py generate examples/example_spec.py --outdir output
```

## Output

Generated file: `output/TEST_MATRIX.md`

Contains a markdown table with these columns:
- Scenario ID
- Feature  
- Preconditions
- Stimulus
- Test Steps
- Expected Result
- Coverage Bin
- Priority

Minimum 8 test scenarios generated.

## Debugging

If generation fails, check `output/last_response.txt` for the raw LLM response.

The prompt is optimized to force clean markdown output with no extra text, but some models may still add commentary. The executor automatically strips common artifacts like code fences.

## Files

- `prompts.py` - Optimized prompt that demands markdown-only output
- `agent_loop.py` - Simple executor (no ReAct parsing)
- `tools.py` - Single tool for writing test matrix
- `generator_agent.py` - Main agent logic
- `main.py` / `cli.py` - Command-line interfaces
- `llm_ollama.py` - Ollama subprocess wrapper
- `utils.py` - Spec loader and file writing helpers

## Spec Format

Create a Python file with a `spec` dict:

```python
spec = {
    "project_name": "AHB-Lite Verification",
    "dut": "u_core.core_i.if_stage_i",
    "features": ["handshake", "burst transfers", "idle insertion"],
    "coverage": ["fsm_states", "burst_lengths", "addr_alignments"]
}
```

## Model Selection

Works with any Ollama model. Recommended:
- `phi3` - Fast, good quality
- `llama3.2` - Better for complex specs
- `mistral` - Alternative option

```bash
python main.py generate --model llama3.2 --spec myspec.py
```