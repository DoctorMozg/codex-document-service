#!/usr/bin/env python3

from pathlib import Path
from uuid import UUID

import click
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from starlette import status

console = Console()


def format_response_error(response: httpx.Response) -> str:
    try:
        error_data = response.json()
        return (
            f"[red]Error {response.status_code}:[/red] "
            f"{error_data.get('detail', 'Unknown error')}"
        )
    except Exception:  # noqa: BLE001
        return f"[red]HTTP {response.status_code}:[/red] {response.text}"


def make_request(method: str, url: str, **kwargs) -> httpx.Response:  # type: ignore # noqa: ANN003
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Making request...", total=None)
            response = httpx.request(method, url, timeout=30.0, **kwargs)
            progress.update(task, completed=100)
    except httpx.RequestError as e:
        console.print(f"[red]Request failed:[/red] {e}")
        msg = f"Request failed: {e}"
        raise click.ClickException(msg) from e
    else:
        return response


@click.group()
@click.option(
    "--server",
    default="http://localhost:8000",
    help="Server URL",
    show_default=True,
)
@click.pass_context
def cli(ctx: click.Context, server: str) -> None:
    ctx.ensure_object(dict)
    ctx.obj["server"] = server.rstrip("/")

    console.print(
        Panel.fit(
            "[bold blue]Document RAG Service CLI[/bold blue]\n"
            f"[dim]Server: {server}[/dim]",
            style="blue",
        ),
    )


@cli.command()
@click.pass_context
def health(ctx: click.Context) -> None:
    server = ctx.obj["server"]

    response = make_request("GET", f"{server}/health")

    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        console.print(
            Panel(
                f"[green]✓ Service is healthy[/green]\n"
                f"Status: {data.get('status', 'unknown')}\n"
                f"Service: {data.get('service', 'unknown')}",
                title="Health Check",
                style="green",
            ),
        )
    else:
        console.print(format_response_error(response))


@cli.command()
@click.option("--question", "-q", help="Question to ask about the documents")
@click.pass_context
def query(ctx: click.Context, question: str) -> None:
    server = ctx.obj["server"]

    if not question:
        question = Prompt.ask("[blue]Enter your question about the documents[/blue]")

    if not question.strip():
        console.print("[red]Question cannot be empty[/red]")
        return

    payload = {"question": question}
    response = make_request("POST", f"{server}/api/v1/query", json=payload)

    if response.status_code == status.HTTP_200_OK:
        data = response.json()

        console.print(
            Panel(
                f"[bold]Question:[/bold] {data['query']}\n\n"
                f"[bold]Answer:[/bold] {data['answer']}\n\n"
                f"[bold]Confidence:[/bold] {data['confidence']:.2%}\n"
                f"[bold]Relevant:[/bold] {'✓' if data['is_relevant'] else '✗'}",
                title="Query Result",
                style="green" if data["is_relevant"] else "yellow",
            ),
        )

        if data["sources"]:
            table = Table(
                title="Sources",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Document", style="cyan")
            table.add_column("Relevance", justify="center")
            table.add_column("Text Snippet", max_width=50)

            for source in data["sources"]:
                table.add_row(
                    source["document_name"],
                    f"{source['relevance_score']:.2%}",
                    source["text_snippet"],
                )

            console.print(table)
    else:
        console.print(format_response_error(response))


@cli.command()
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="PDF file to upload",
)
@click.pass_context
def upload(ctx: click.Context, file: Path) -> None:
    server = ctx.obj["server"]

    if not file.name.lower().endswith(".pdf"):
        console.print("[red]Only PDF files are supported[/red]")
        return

    try:
        with Path(file).open("rb") as f:
            files = {"file": (file.name, f, "application/pdf")}
            response = make_request("POST", f"{server}/api/v1/upload", files=files)

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            console.print(
                Panel(
                    f"[green]✓ Upload successful[/green]\n\n"
                    f"[bold]Document ID:[/bold] {data['document_uid']}\n"
                    f"[bold]Filename:[/bold] {data['filename']}\n"
                    f"[bold]Message:[/bold] {data['message']}",
                    title="Upload Result",
                    style="green",
                ),
            )
        else:
            console.print(format_response_error(response))

    except Exception as e:  # noqa: BLE001
        console.print(f"[red]Upload failed:[/red] {e}")


@cli.command()
@click.pass_context
def list_docs(ctx: click.Context) -> None:
    server = ctx.obj["server"]

    response = make_request("GET", f"{server}/api/v1/documents")

    if response.status_code == status.HTTP_200_OK:
        data = response.json()

        if not data["documents"]:
            console.print(
                Panel(
                    "[yellow]No documents found[/yellow]",
                    title="Documents",
                    style="yellow",
                ),
            )
            return

        table = Table(
            title=f"Documents ({data['total_count']} total)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Name", style="cyan")
        table.add_column("Document ID", style="dim")
        table.add_column("Upload Date", justify="center")
        table.add_column("Size", justify="right")

        for doc in data["documents"]:
            size_mb = doc["size_bytes"] / (1024 * 1024)
            table.add_row(
                doc["name"],
                str(doc["uid"]),
                doc["upload_date"],
                f"{size_mb:.2f} MB",
            )

        console.print(table)
    else:
        console.print(format_response_error(response))


@cli.command()
@click.argument("document_id")
@click.pass_context
def info(ctx: click.Context, document_id: str) -> None:
    server = ctx.obj["server"]

    try:
        UUID(document_id)
    except ValueError:
        console.print("[red]Invalid document ID format[/red]")
        return

    response = make_request("GET", f"{server}/api/v1/documents/{document_id}/info")

    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        size_mb = data["size_bytes"] / (1024 * 1024)

        console.print(
            Panel(
                f"[bold]Name:[/bold] {data['name']}\n"
                f"[bold]Document ID:[/bold] {data['uid']}\n"
                f"[bold]Upload Date:[/bold] {data['upload_date']}\n"
                f"[bold]Size:[/bold] {size_mb:.2f} MB ({data['size_bytes']:,} bytes)",
                title="Document Information",
                style="blue",
            ),
        )
    else:
        console.print(format_response_error(response))


@cli.command()
@click.argument("document_id")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.pass_context
def download(ctx: click.Context, document_id: str, output: Path) -> None:
    server = ctx.obj["server"]

    try:
        UUID(document_id)
    except ValueError:
        console.print("[red]Invalid document ID format[/red]")
        return

    response = make_request("GET", f"{server}/api/v1/documents/{document_id}/download")

    if response.status_code == status.HTTP_200_OK:
        if output.exists() and not Confirm.ask(
            f"[yellow]File {output} exists. Overwrite?[/yellow]",
        ):
            return

        with Path(output).open("wb") as f:
            f.write(response.content)

        size_mb = len(response.content) / (1024 * 1024)
        console.print(
            Panel(
                f"[green]✓ Download successful[/green]\n\n"
                f"[bold]Saved to:[/bold] {output}\n"
                f"[bold]Size:[/bold] {size_mb:.2f} MB",
                title="Download Complete",
                style="green",
            ),
        )
    else:
        console.print(format_response_error(response))


@cli.command()
@click.argument("document_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete(ctx: click.Context, document_id: str, yes: bool) -> None:  # noqa: FBT001
    server = ctx.obj["server"]

    try:
        UUID(document_id)
    except ValueError:
        console.print("[red]Invalid document ID format[/red]")
        return

    if not yes and not Confirm.ask(
        f"[red]Are you sure you want to delete document {document_id}?[/red]",
    ):
        console.print("[yellow]Operation cancelled[/yellow]")
        return

    response = make_request("DELETE", f"{server}/api/v1/documents/{document_id}")

    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        console.print(
            Panel(
                f"[green]✓ {data['message']}[/green]\n\n"
                f"[bold]Document ID:[/bold] {data['document_uid']}",
                title="Deletion Complete",
                style="green",
            ),
        )
    else:
        console.print(format_response_error(response))


@cli.command()
@click.pass_context
def interactive(ctx: click.Context) -> None:  # noqa: C901, PLR0912
    ctx.obj["server"]

    console.print(
        Panel(
            "[bold blue]Interactive Mode[/bold blue]\n"
            "Type commands or 'help' for options, 'exit' to quit",
            style="blue",
        ),
    )

    while True:
        try:
            command = Prompt.ask("\n[bold cyan]docrag>[/bold cyan]", default="help")

            if command.lower() in ["exit", "quit", "q"]:
                console.print("[yellow]Goodbye![/yellow]")
                break
            if command.lower() in ["help", "h"]:
                table = Table(
                    title="Available Commands",
                    show_header=True,
                    header_style="bold magenta",
                )
                table.add_column("Command", style="cyan")
                table.add_column("Description")

                table.add_row("health", "Check service health")
                table.add_row("query", "Ask questions about documents")
                table.add_row("upload", "Upload a PDF document")
                table.add_row("list", "List all documents")
                table.add_row("info <doc_id>", "Get document information")
                table.add_row("download <doc_id>", "Download a document")
                table.add_row("delete <doc_id>", "Delete a document")
                table.add_row("help", "Show this help")
                table.add_row("exit", "Exit interactive mode")

                console.print(table)
            else:
                # Parse and execute commands
                parts = command.split()
                cmd = parts[0].lower()

                if cmd == "health":
                    ctx.invoke(health)
                elif cmd == "query":
                    ctx.invoke(query)
                elif cmd == "upload":
                    ctx.invoke(upload)
                elif cmd == "list":
                    ctx.invoke(list_docs)
                elif cmd == "info" and len(parts) > 1:
                    ctx.invoke(info, document_id=parts[1])
                elif cmd == "download" and len(parts) > 1:
                    ctx.invoke(download, document_id=parts[1])
                elif cmd == "delete" and len(parts) > 1:
                    ctx.invoke(delete, document_id=parts[1])
                else:
                    console.print(
                        "[red]Unknown command. Type 'help' for options.[/red]",
                    )

        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    cli()
