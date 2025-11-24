#!/usr/bin/env python3
"""
main.py - TRUE ReAct agent with explicit data flow
"""
import argparse
from agents.generator_agent import GeneratorAgent

def main():
    parser = argparse.ArgumentParser(
        description="TRUE ReAct Agent for Test Matrix Generation"
    )
    parser.add_argument(
        "command",
        choices=["generate", "explain"],
        help="Action to perform"
    )
    parser.add_argument(
        "--spec",
        default="examples/example_spec.py",
        help="Path to spec file"
    )
    parser.add_argument(
        "--model",
        default="phi3",
        help="Routing model (decides which tools to call)"
    )
    parser.add_argument(
        "--content-model",
        default=None,
        help="Content generation model (generates scenario details)"
    )
    parser.add_argument(
        "--outdir",
        default="output",
        help="Output directory"
    )

    args = parser.parse_args()

    agent = GeneratorAgent(
        model=args.model,
        content_model=args.content_model,
        outdir=args.outdir
    )

    if args.command == "generate":
        print(f"\nGenerating test matrix from: {args.spec}")
        if args.content_model:
            print(f"Dual-model setup:")
            print(f"  - Routing: {args.model}")
            print(f"  - Content: {args.content_model}")
        
        outputs = agent.run(args.spec)
        
        if outputs:
            print("\n✓ Generated:")
            for f in outputs:
                print(f"  - {f}")
        else:
            print("\n✗ Failed. Check output/execution_history.json")

    elif args.command == "explain":
        print(agent.explain(args.spec))

if __name__ == "__main__":
    main()