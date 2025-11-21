# AI Agent (Ollama) — README

This project is a ReAct-style AI agent that uses a local Ollama model to generate a
verification README and a TEST_MATRIX from a Python `spec` dictionary.

## Quick start

1. Install Ollama and pull a model (e.g., `phi3`): https://ollama.com
2. Create a Python venv and install optional deps: `pip install click requests pyyaml`
3. Run the agent:

```bash
python main.py generate --spec examples/example_spec.py --model phi3 --outdir output
```

or use the nicer click CLI (requires `pip install click`):

```bash
python cli.py generate examples/example_spec.py --outdir output
```

Generated files appear in `output/`.

## Notes
- This agent uses a strict ReAct format. The model's responses must contain `Action:` lines
  and `Action Input:` JSON-like dicts.
- Tools available: write_readme, write_testmatrix, explain, debug.
