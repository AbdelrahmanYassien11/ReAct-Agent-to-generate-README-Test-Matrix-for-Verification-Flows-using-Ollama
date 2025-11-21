"""
cli.py - click-based CLI for convenience (optional)

Install click: pip install click
"""
import click
from agents.generator_agent import GeneratorAgent
from utils import load_spec

@click.group()
@click.option("--model", default="phi3", help="Ollama model name")
@click.pass_context
def cli(ctx, model):
    ctx.ensure_object(dict)
    ctx.obj["model"] = model

@cli.command()
@click.argument("spec", default="examples/example_spec.py")
@click.option("--outdir", default="output")
def generate(spec, outdir):
    s = load_spec(spec)
    agent = GeneratorAgent(model=click.get_current_context().obj["model"], outdir=outdir)
    outs = agent.run(s)
    click.echo("Generated:")
    for o in outs:
        click.echo(" - " + o)

@cli.command()
@click.argument("spec", default="examples/example_spec.py")
def explain(spec):
    s = load_spec(spec)
    agent = GeneratorAgent(model=click.get_current_context().obj["model"])
    click.echo(agent.explain(s))

if __name__ == "__main__":
    cli()
