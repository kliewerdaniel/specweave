from __future__ import annotations

import json
from pathlib import Path

import click

from specweave.config import settings


@click.group()
@click.option("--data-dir", type=click.Path(), default=None, help="Override data directory")
@click.pass_context
def cli(ctx: click.Context, data_dir: str | None) -> None:
    """SpecWeave — Self-verifying, speculative, multi-agent spec engine."""
    ctx.ensure_object(dict)
    if data_dir:
        settings.data_dir = Path(data_dir)
    ctx.obj["data_dir"] = settings.data_dir


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize a new SpecWeave project."""
    data_dir = ctx.obj["data_dir"]
    dirs = [
        data_dir,
        data_dir / "specs",
        data_dir / "agents",
        data_dir / "memory",
        data_dir / "memory" / "chromadb",
        data_dir / "adr",
        data_dir / "graph",
        data_dir / "tasks",
        data_dir / "templates",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    constitution = data_dir / "constitution.md"
    if not constitution.exists():
        constitution.write_text("# Project Constitution\n\n## Technology Stack\n- Language: Python 3.12+\n")

    bootstrap = data_dir / "bootstrap.md"
    if not bootstrap.exists():
        bootstrap.write_text("# Bootstrap\n\nAgent identity configuration.\n")

    click.echo(f"SpecWeave project initialized at {data_dir}")


@cli.group()
def spec() -> None:
    """Manage specs."""
    pass


@spec.command("create")
@click.option("--name", required=True, help="Project name")
@click.option("--title", required=True, help="Project title")
@click.option("--description", default="", help="Project description")
@click.option("--version", default="0.1.0", help="Version (semver)")
@click.option("--file", "spec_file", type=click.Path(exists=True), help="Read raw spec from file")
@click.pass_context
def spec_create(ctx: click.Context, name: str, title: str, description: str, version: str, spec_file: str | None) -> None:
    """Create a new spec."""
    raw_spec = ""
    if spec_file:
        raw_spec = Path(spec_file).read_text()

    spec_id = __import__("uuid").uuid4().hex
    spec_dir = ctx.obj["data_dir"] / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)

    spec_data = {
        "id": spec_id,
        "project_name": name,
        "project_title": title,
        "project_description": description,
        "version": version,
        "status": "draft",
        "raw_spec": raw_spec,
    }

    spec_path = spec_dir / f"{spec_id}.json"
    spec_path.write_text(json.dumps(spec_data, indent=2))
    click.echo(f"Spec created: {spec_id}")
    click.echo(json.dumps(spec_data, indent=2))


@spec.command("list")
@click.pass_context
def spec_list(ctx: click.Context) -> None:
    """List all specs."""
    spec_dir = ctx.obj["data_dir"] / "specs"
    if not spec_dir.exists():
        click.echo("No specs found.")
        return

    specs = []
    for f in sorted(spec_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            specs.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    if not specs:
        click.echo("No specs found.")
        return

    for s in specs:
        click.echo(f"  {s['id'][:8]}  {s['status']:12}  {s['project_title']}  v{s.get('version', '?')}")


@spec.command("get")
@click.argument("spec_id")
@click.pass_context
def spec_get(ctx: click.Context, spec_id: str) -> None:
    """Get spec details."""
    spec_dir = ctx.obj["data_dir"] / "specs"
    for f in spec_dir.glob("*.json"):
        if f.stem.startswith(spec_id):
            data = json.loads(f.read_text())
            click.echo(json.dumps(data, indent=2))
            return
    click.echo(f"Spec not found: {spec_id}", err=True)


@cli.command()
@click.argument("spec_id")
@click.pass_context
def compile(ctx: click.Context, spec_id: str) -> None:
    """Run the compiler pipeline on a spec."""
    from specweave.compiler import CompilerPipeline
    from specweave.persistence import GraphStore, SQLiteStore

    db = SQLiteStore(settings.sqlite_path)
    db.initialize()
    graph = GraphStore()

    spec_data = db.get_spec(spec_id)
    if spec_data is None:
        spec_dir = ctx.obj["data_dir"] / "specs"
        for f in spec_dir.glob("*.json"):
            if f.stem.startswith(spec_id):
                spec_data = json.loads(f.read_text())
                break

    if spec_data is None:
        click.echo(f"Spec not found: {spec_id}", err=True)
        return

    compiler = CompilerPipeline(db, graph)
    gates = compiler.run(spec_id, spec_data)

    for gate in gates:
        status_icon = "PASS" if gate["status"] == "passed" else "FAIL"
        click.echo(f"  [{status_icon}] {gate['gate_id']}")
        if gate.get("failure_reason"):
            click.echo(f"         {gate['failure_reason']}")

    final = "compiled" if all(g["status"] == "passed" for g in gates) else "failed"
    click.echo(f"\nFinal status: {final}")


@cli.command()
@click.argument("spec_id")
@click.option("--baseline", default=None, help="Baseline spec ID for drift comparison")
@click.pass_context
def detect(ctx: click.Context, spec_id: str, baseline: str | None) -> None:
    """Run contradiction/drift detection on a spec."""
    from specweave.detection import ContradictionDetector, DriftDetector
    from specweave.persistence import GraphStore, SQLiteStore

    db = SQLiteStore(settings.sqlite_path)
    db.initialize()
    graph = GraphStore()

    click.echo("Detecting contradictions...")
    contradiction_detector = ContradictionDetector(db, graph)
    contradictions = contradiction_detector.detect_contradictions(spec_id)
    click.echo(f"  Found {len(contradictions)} contradictions")
    for c in contradictions:
        click.echo(f"    - [{c.severity}] {c.description}")

    click.echo("Detecting drift...")
    drift_detector = DriftDetector(db)
    drifts = drift_detector.detect_drift(spec_id, baseline)
    click.echo(f"  Found {len(drifts)} drifts")
    for d in drifts:
        click.echo(f"    - {d.field}: {d.baseline_value} -> {d.current_value} (score: {d.drift_score:.2f})")


@cli.group()
def memory() -> None:
    """Manage sovereign memory."""
    pass


@memory.command("create-persona")
@click.option("--agent-id", required=True, help="Agent ID")
@click.option("--name", required=True, help="Persona name")
@click.option("--description", default="", help="Persona description")
@click.pass_context
def memory_create_persona(ctx: click.Context, agent_id: str, name: str, description: str) -> None:
    """Create a new persona."""
    from specweave.memory import MemoryManager, MemoryStore

    store = MemoryStore(settings.data_dir / "memory" / "specweave.db")
    store.initialize()
    manager = MemoryManager(store)
    persona = manager.create_persona(agent_id, name, description)
    click.echo(f"Persona created: {persona.id}")
    click.echo(json.dumps(persona.model_dump(mode="json"), indent=2))


@memory.command("list-personas")
@click.option("--agent-id", default=None, help="Filter by agent ID")
@click.pass_context
def memory_list_personas(ctx: click.Context, agent_id: str | None) -> None:
    """List personas."""
    from specweave.memory import MemoryManager, MemoryStore

    store = MemoryStore(settings.data_dir / "memory" / "specweave.db")
    store.initialize()
    manager = MemoryManager(store)
    personas = manager.list_personas(agent_id)
    if not personas:
        click.echo("No personas found.")
        return
    for p in personas:
        click.echo(f"  {p.id[:8]}  {p.name:20}  agent={p.agent_id}")


@memory.command("store")
@click.option("--persona-id", required=True, help="Persona ID")
@click.option("--key", required=True, help="Memory key")
@click.option("--value", required=True, help="Memory value")
@click.option("--context", default="", help="Memory context")
@click.pass_context
def memory_store(ctx: click.Context, persona_id: str, key: str, value: str, context: str) -> None:
    """Store a memory entry."""
    from specweave.memory import MemoryManager, MemoryStore

    store = MemoryStore(settings.data_dir / "memory" / "specweave.db")
    store.initialize()
    manager = MemoryManager(store)
    entry = manager.store_memory(persona_id, key, value, context)
    click.echo(f"Memory stored: {entry.id[:8]} key={entry.key}")


@memory.command("list-memories")
@click.option("--persona-id", required=True, help="Persona ID")
@click.pass_context
def memory_list_memories(ctx: click.Context, persona_id: str) -> None:
    """List memories for a persona."""
    from specweave.memory import MemoryManager, MemoryStore

    store = MemoryStore(settings.data_dir / "memory" / "specweave.db")
    store.initialize()
    manager = MemoryManager(store)
    memories = manager.get_memories(persona_id)
    if not memories:
        click.echo("No memories found.")
        return
    for m in memories:
        click.echo(f"  {m.id[:8]}  key={m.key}  context={m.context[:40]}")


@cli.command()
@click.pass_context
def audit(ctx: click.Context) -> None:
    """View audit trail."""
    from specweave.persistence import SQLiteStore

    db = SQLiteStore(settings.sqlite_path)
    db.initialize()

    specs = db.list_specs()
    for s in specs:
        records = db.get_audit_for_spec(s["id"])
        if records:
            click.echo(f"\n{s['project_title']} ({s['id'][:8]}):")
            for r in records:
                click.echo(f"  [{r['action']}] actor={r['actor']} at={r['created_at']}")


@cli.command()
@click.pass_context
def trust(ctx: click.Context) -> None:
    """View trust configuration."""
    from specweave.trust import discover_agents, read_bootstrap

    bootstrap = read_bootstrap()
    if bootstrap:
        click.echo(f"Bootstrap: {bootstrap['path']}")
    else:
        click.echo("No bootstrap.md found.")

    agents = discover_agents()
    if agents:
        click.echo(f"\nDiscovered agents ({len(agents)}):")
        for a in agents:
            click.echo(f"  - {a.agent_id} (path: {a.source_path})")
    else:
        click.echo("\nNo agents discovered.")


@cli.command()
@click.pass_context
def grammar(ctx: click.Context) -> None:
    """List available GBNF grammars."""
    from specweave.grammar.loader import get_available_grammars

    grammars = get_available_grammars()
    if grammars:
        click.echo("Available grammars:")
        for g in grammars:
            click.echo(f"  - {g}")
    else:
        click.echo("No grammars found.")


@cli.command()
@click.pass_context
def graph(ctx: click.Context) -> None:
    """View knowledge graph."""
    from specweave.persistence import GraphStore

    graph_store = GraphStore()
    nodes = graph_store.graph.nodes(data=True)
    if not nodes:
        click.echo("Graph is empty.")
        return

    click.echo("Knowledge graph nodes:")
    for node_id, data in nodes:
        node_type = data.get("node_type", "unknown")
        title = data.get("title", "")
        click.echo(f"  {node_id} ({node_type}): {title}")


@cli.command()
@click.argument("spec_id")
@click.argument("target_agent")
@click.option("--content", required=True, help="Sub-spec content")
@click.pass_context
def delegate(ctx: click.Context, spec_id: str, target_agent: str, content: str) -> None:
    """Delegate a sub-spec to another agent."""
    from specweave.gateway import A2AHandler
    from specweave.persistence import SQLiteStore

    db = SQLiteStore(settings.sqlite_path)
    db.initialize()
    a2a = A2AHandler(db)
    delegation = a2a.delegate(spec_id, content, target_agent)
    click.echo(f"Delegation created: {delegation['id'][:8]}")
    click.echo(f"  Target: {target_agent}")
    click.echo(f"  Status: {delegation['status']}")


@cli.command()
@click.argument("delegation_id")
@click.option("--result", required=True, help="Submission result")
@click.pass_context
def submit(ctx: click.Context, delegation_id: str, result: str) -> None:
    """Submit work for a delegation."""
    from specweave.gateway import A2AHandler
    from specweave.persistence import SQLiteStore

    db = SQLiteStore(settings.sqlite_path)
    db.initialize()
    a2a = A2AHandler(db)
    delegation = a2a.submit(delegation_id, result)
    if delegation is None:
        click.echo(f"Delegation not found: {delegation_id}", err=True)
        return
    click.echo(f"Delegation {delegation_id[:8]} submitted. Status: {delegation['status']}")


@cli.command()
@click.argument("spec_id")
@click.pass_context
def verify(ctx: click.Context, spec_id: str) -> None:
    """Verify a spec using neuro-symbolic checks."""
    from specweave.neuro_symbolic import NeuralChecker, SymbolicValidator
    from specweave.persistence import GraphStore, SQLiteStore

    db = SQLiteStore(settings.sqlite_path)
    db.initialize()
    graph = GraphStore()

    symbolic = SymbolicValidator(graph)
    results = symbolic.check_all()

    click.echo("Symbolic checks:")
    for r in results:
        status_icon = "PASS" if r["passed"] else "FAIL"
        click.echo(f"  [{status_icon}] {r['name']}")
        if r.get("failure_reason"):
            click.echo(f"         {r['failure_reason']}")

    all_passed = all(r["passed"] for r in results)
    click.echo(f"\nVerification: {'PASSED' if all_passed else 'FAILED'}")


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """View system status."""
    from specweave.grammar.loader import get_available_grammars
    from specweave.persistence import SQLiteStore
    from specweave.trust import discover_agents

    db_path = settings.sqlite_path
    db_exists = db_path.exists()

    click.echo("SpecWeave Status:")
    click.echo(f"  Data dir: {settings.data_dir}")
    click.echo(f"  Database: {'exists' if db_exists else 'not found'} ({db_path})")
    click.echo(f"  Ollama: {settings.ollama_host}")

    agents = discover_agents()
    click.echo(f"  Agents: {len(agents)}")

    grammars = get_available_grammars()
    click.echo(f"  Grammars: {len(grammars)}")

    if db_exists:
        db = SQLiteStore(db_path)
        db.initialize()
        specs = db.list_specs()
        click.echo(f"  Specs: {len(specs)}")


if __name__ == "__main__":
    cli()
