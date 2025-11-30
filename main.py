#!/usr/bin/env python3
"""
main.py - TRUE ReAct agent with explicit dual-model architecture
Routing model: Orchestration only (ReAct decisions)
Content model: All content generation (parsing, extracting, generating)
"""
import argparse
from agents.generator_agent import GeneratorAgent


def main():
    parser = argparse.ArgumentParser(
        description="TRUE ReAct Agent for Test Matrix Generation with Dual-Model Architecture"
    )
    parser.add_argument(
        "command", choices=["generate", "explain"], help="Action to perform"
    )
    parser.add_argument(
        "--spec", default="examples/example_spec.py", help="Path to spec file"
    )
    parser.add_argument(
        "--model",
        default="phi3",
        help="Routing model (orchestration/ReAct decisions only)",
    )
    parser.add_argument(
        "--content-model",
        default=None,
        help="Content model (parsing, extraction, generation). If not set, uses routing model for both.",
    )
    parser.add_argument("--outdir", default="output", help="Output directory")

    args = parser.parse_args()

    # Use routing model for both if content model not specified
    content_model = args.content_model if args.content_model else args.model

    agent = GeneratorAgent(
        model=args.model, content_model=content_model, outdir=args.outdir
    )

    if args.command == "generate":
        print(f"\nGenerating test matrix from: {args.spec}")
        print(f"\nModel Architecture:")
        print(f"  Routing (ReAct orchestration): {args.model}")
        print(f"  Content (parsing/generation):  {content_model}")
        if args.model != content_model:
            print(f"  Dual-model mode enabled")
        else:
            print(f"  ℹ Single-model mode (same model for both)")

        outputs = agent.run(args.spec)

        if outputs:
            print("\n Generated:")
            for f in outputs:
                print(f"  - {f}")
        else:
            print("\n Failed. Check output/execution_summary.json")

    elif args.command == "explain":
        print(agent.explain(args.spec))


if __name__ == "__main__":
    main()
