#!/usr/bin/env python3
"""
main.py - entrypoint for the ReAct-style Ollama agent
Supports commands: generate, explain, debug, rerun
"""
import argparse
from agents.generator_agent import GeneratorAgent
from utils import load_spec

def main():
    parser = argparse.ArgumentParser(description="AI Agent for README + Test Matrix (Ollama, ReAct)")
    parser.add_argument("command", choices=["generate", "explain", "debug", "rerun"], help="Action to perform")
    parser.add_argument("--spec", default="examples/example_spec.py", help="Path to spec file (Python dict)")
    parser.add_argument("--model", default="phi3", help="Ollama model name (local)")
    parser.add_argument("--outdir", default="output", help="Output directory")
    parser.add_argument("--last_response", default=None, help="Path to a previous LLM response to rerun")

    args = parser.parse_args()

    spec = load_spec(args.spec)
    agent = GeneratorAgent(model=args.model, outdir=args.outdir)

    if args.command == "generate":
        outputs = agent.run(spec)
        print("Generated files:")
        for f in outputs:
            print(" -", f)

    elif args.command == "explain":
        print(agent.explain(spec))

    elif args.command == "debug":
        print(agent.debug(spec))

    elif args.command == "rerun":
        if not args.last_response:
            print("Provide --last_response path to rerun")
            return
        with open(args.last_response, "r", encoding="utf-8") as f:
            resp = f.read()
        outputs = agent.rerun_from_response(spec, resp)
        print("Rerun outputs:")
        for f in outputs:
            print(" -", f)

if __name__ == "__main__":
    main()
