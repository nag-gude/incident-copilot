"""Incident Copilot CLI - incident-copilot status, anomalies, predict, explain, remediate."""

import os
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

API_URL = os.getenv("INCIDENT_COPILOT_API_URL", "http://localhost:8000")

app = typer.Typer(name="incident-copilot", help="Incident Copilot CLI")
console = Console()


def get_client():
    return httpx.Client(base_url=API_URL, timeout=10.0)


@app.command()
def status():
    """Cluster health overview."""
    with get_client() as c:
        try:
            r = c.get("/status")
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]. Is the API running at {API_URL}?")
            raise typer.Exit(1)

    console.print("[bold]Incident Copilot - Status[/bold]\n")
    services = data.get("services", {})
    for name, s in services.items():
        color = "green" if s == "ok" else "red"
        console.print(f"  {name}: [{color}]{s}[/{color}]")

    pred = data.get("latest_prediction")
    if pred:
        console.print(f"\n[bold]Latest prediction:[/bold] {pred.get('failure_probability', 'N/A')}% failure probability")


@app.command()
def anomalies(limit: int = typer.Option(20, "--limit", "-l")):
    """List detected anomalies."""
    with get_client() as c:
        try:
            r = c.get(f"/anomalies?limit={limit}")
            r.raise_for_status()
            items = r.json()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    if not items:
        console.print("[dim]No anomalies.[/dim]")
        return

    table = Table(title="Anomalies")
    table.add_column("ID", style="dim")
    table.add_column("Metric/Log")
    table.add_column("Actual")
    table.add_column("Expected")
    table.add_column("Score")
    table.add_column("Severity")
    for a in items:
        table.add_row(
            a.get("id", "")[:8],
            a.get("metric_or_log", ""),
            str(a.get("actual_value", "")),
            str(a.get("expected_value", "")),
            str(a.get("deviation_score", "")),
            a.get("severity", ""),
        )
    console.print(table)


@app.command()
def predict():
    """Run failure prediction and show result."""
    with get_client() as c:
        try:
            r = c.get("/predict")
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"[bold]Failure probability:[/bold] {data.get('failure_probability', 0)}%")
    console.print(f"[bold]Contributing factors:[/bold] {', '.join(data.get('contributing_factors', []))}")


@app.command()
def explain(
    incident_id: Optional[str] = typer.Argument(None),
    service: Optional[str] = typer.Option(None, "--service", "-s"),
):
    """Explain incident (root cause, evidence, recommendations). Creates incident if no ID."""
    with get_client() as c:
        try:
            if incident_id:
                incidents = c.get("/incidents").json()
                inc = next((i for i in incidents if i["id"] == incident_id), None)
                if not inc:
                    console.print(f"[red]Incident {incident_id} not found.[/red]")
                    raise typer.Exit(1)
                console.print(f"[bold]Incident:[/bold] {inc.get('root_cause', 'N/A')}")
                return
            r = c.post("/explain", json={"service": service})
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPStatusError as e:
            console.print(f"[red]HTTP error: {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"[bold]Incident ID:[/bold] {data.get('id')}")
    console.print(f"[bold]Root cause:[/bold] {data.get('root_cause')}")
    console.print(f"[bold]Recommendations:[/bold]")
    for rec in data.get("recommendations", []):
        console.print(f"  - {rec}")
    if data.get("youcom_citations"):
        console.print("[bold]You.com citations:[/bold]")
        for c in data["youcom_citations"][:3]:
            console.print(f"  - {c.get('title', '')}: {c.get('url', '')}")


@app.command()
def remediate(
    incident_id: str = typer.Argument(..., help="Incident ID"),
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute remediation script (requires AUTO_REMEDIATE_EXECUTE_ENABLED)"),
):
    """Generate remediation script via Cline CLI for incident."""
    url = f"/remediate/{incident_id}"
    if execute:
        url += "?execute=true"
    with get_client() as c:
        try:
            r = c.post(url, timeout=60)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"[bold]Remediation script for {incident_id}:[/bold]\n")
    console.print(data.get("script", ""))
    if data.get("execution"):
        ex = data["execution"]
        if ex.get("error"):
            console.print(f"\n[red]Execution: {ex['error']}[/red]")
        elif "returncode" in ex:
            rc = ex["returncode"]
            console.print(f"\n[bold]Execution result (returncode={rc}):[/bold]")
            if ex.get("stdout"):
                console.print(ex["stdout"])
            if ex.get("stderr"):
                console.print(f"[yellow]{ex['stderr']}[/yellow]")


if __name__ == "__main__":
    app()
