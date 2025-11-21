"""
llm_ollama.py

Small wrapper around the `ollama` CLI. If `ollama` is not available, returns an error message.
"""
import subprocess

class OllamaLLM:
    def __init__(self, model: str = "phi3"):
        self.model = model

    def __call__(self, prompt: str) -> str:
        # Call `ollama run <model>` and stream prompt via stdin
        try:
            proc = subprocess.run(["ollama", "run", self.model], input=prompt.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1000)
            out = proc.stdout.decode().strip()
            if not out:
                err = proc.stderr.decode().strip()
                return f"[ollama_no_output] stderr={err}"
            return out
        except FileNotFoundError:
            return "[ollama_not_installed] Please install ollama: https://ollama.com"
        except Exception as e:
            return f"[ollama_error] {e}"
