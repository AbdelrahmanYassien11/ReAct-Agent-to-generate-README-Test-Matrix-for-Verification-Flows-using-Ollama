"""
llm_ollama.py - Ollama wrapper with better timeout handling
"""
import subprocess

class OllamaLLM:
    def __init__(self, model: str = "phi3"):
        self.model = model

    def __call__(self, prompt: str) -> str:
        try:
            # Increased timeout to 600 seconds (10 minutes)
            proc = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=1000
            )
            
            out = proc.stdout.decode().strip()
            
            if not out:
                err = proc.stderr.decode().strip()
                return f"[Error: No output. stderr={err[:200]}]"
            
            return out
            
        except FileNotFoundError:
            return "[Error: Ollama not installed. Visit https://ollama.com]"
        except subprocess.TimeoutExpired:
            return "[Error: Timeout after 10 minutes. Model may be stuck or prompt too complex]"
        except Exception as e:
            return f"[Error: {str(e)[:200]}]"