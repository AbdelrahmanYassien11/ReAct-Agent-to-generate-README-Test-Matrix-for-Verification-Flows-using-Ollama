"""
cli.py - Click-based CLI with dual-model support
"""
import click
from agents.generator_agent import GeneratorAgent
from utils import load_spec

@click.group()
@click.option("--model", default="phi3", help="Ollama model for agent routing")
@click.option("--content-model", default=None, help="Separate model for content generation (optional)")
@click.pass_context
def cli(ctx, model, content_model):
    ctx.ensure_object(dict)
    ctx.obj["model"] = model
    ctx.obj["content_model"] = content_model

@cli.command()
@click.argument("spec", default="examples/example_spec.py")
@click.option("--outdir", default="output")
def generate(spec, outdir):
    """Generate test matrix from specification using ReAct agent."""
    s = load_spec(spec)
    ctx = click.get_current_context()
    
    agent = GeneratorAgent(
        model=ctx.obj["model"],
        content_model=ctx.obj["content_model"],
        outdir=outdir
    )
    
    click.echo(f"\nGenerating test matrix for: {s.get('project_name', 'N/A')}")
    outs = agent.run(s)
    
    if outs:
        click.echo("\n✓ Generated:")
        for o in outs:
            click.echo(f"  - {o}")
    else:
        click.echo("\n✗ Generation failed")

@cli.command()
@click.argument("spec", default="examples/example_spec.py")
def explain(spec):
    """Explain what the ReAct agent will do."""
    s = load_spec(spec)
    ctx = click.get_current_context()
    
    agent = GeneratorAgent(
        model=ctx.obj["model"],
        content_model=ctx.obj["content_model"]
    )
    click.echo(agent.explain(s))

if __name__ == "__main__":
    cli()