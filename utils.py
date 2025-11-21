"""
utils.py

Helpers for loading a Python dict spec and safe file writing.
"""
import os
from typing import Dict

def load_spec(path: str) -> Dict:
    # exec the file in an isolated namespace and return spec variable
    ns = {}
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    exec(code, ns)
    if "spec" not in ns:
        raise ValueError("Spec file must define a top-level variable named 'spec'")
    return ns["spec"]

def safe_write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
