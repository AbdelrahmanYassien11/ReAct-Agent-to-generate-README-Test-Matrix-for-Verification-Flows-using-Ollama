"""
utils.py

Essential helpers for loading specs and writing files.
"""
import os
from typing import Dict

def load_spec(path: str) -> Dict:
    """Load Python spec file and return the spec dict."""
    ns = {}
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    exec(code, ns)
    if "spec" not in ns:
        raise ValueError("Spec file must define a top-level variable named 'spec'")
    return ns["spec"]

def safe_write(path: str, content: str) -> None:
    """Write file, creating directories if needed."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)