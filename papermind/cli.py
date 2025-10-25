"""Command-line interface for Papermind."""

import sys
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from pathlib import Path

from papermind.claude import ClaudeClient, PromptType
from papermind.zotero import ZoteroDatabase
from papermind.obsidian import sync_to_obsidian, sync_notes_to_zotero
from papermind.config import get_config

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

console = Console()


def require_configuration():
    """
    Check if Papermind is configured. If not, prompt user to configure.

    Returns:
        tuple: (zotero_path, api_key) from configuration
    """
    config = get_config()

    if not config.is_configured():
        console.print("[yellow]⚠ Papermind is not configured yet.[/yellow]")
        console.print("Please run: [cyan]papermind configure[/cyan]\n")
        sys.exit(1)

    return config.get_zotero_path(), config.get_api_key()


def select_from_list(items, title, display_fn, allow_all=False):
    """
    Display a numbered list and let user select one item.

    Args:
        items: List of items to choose from
        title: Title to display
        display_fn: Function to format each item for display
        allow_all: If True, add an "All" option

    Returns:
        Selected item or None if cancelled, or 'all' if all selected
    """
    if not items:
        console.print(f"[yellow]No {title.lower()} found.[/yellow]")
        return None

    console.print(f"\n[bold blue]{title}[/bold blue]\n")

    # Display numbered list
    table = Table(show_header=False, box=None)
    table.add_column("Number", style="cyan", width=6)
    table.add_column("Item", style="white")

    if allow_all:
        table.add_row("0", "[bold]All items[/bold]")

    for idx, item in enumerate(items, start=1):
        table.add_row(str(idx), display_fn(item))

    console.print(table)

    # Get user selection
    max_choice = len(items)
    min_choice = 0 if allow_all else 1

    while True:
        choice = Prompt.ask(
            f"\n[cyan]Select {title.lower()}[/cyan]",
            default=str(min_choice) if min_choice == 0 else "1"
        )

        if choice.lower() in ['q', 'quit', 'exit', 'cancel']:
            return None

        try:
            choice_num = int(choice)
            if choice_num == 0 and allow_all:
                return 'all'
            if min_choice <= choice_num <= max_choice:
                return items[choice_num - 1]
            console.print(f"[red]Please enter a number between {min_choice} and {max_choice}[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")


def get_collections(db):
    """Get all collections from Zotero database."""
    import sqlite3
    conn = db._get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT collectionID, collectionName, parentCollectionID
        FROM collections
        WHERE collectionID NOT IN (SELECT collectionID FROM deletedCollections)
        ORDER BY collectionName
    """)

    collections = []
    for row in cursor.fetchall():
        collections.append({
            'id': row['collectionID'],
            'name': row['collectionName'],
            'parent': row['parentCollectionID']
        })

    conn.close()
    return collections


@click.group()
@click.version_option(version="0.1.0")
def main():
    """
    Papermind - AI-powered CLI tool for analyzing academic papers.

    Integrates Claude AI with your Zotero library to provide intelligent
    analysis, summaries, and insights from your research papers.
    """
    pass


@main.command()
@click.option(
    '--zotero-path',
    type=click.Path(exists=True),
    help='Path to Zotero data directory',
)
@click.option(
    '--api-key',
    help='Claude API key (or set ANTHROPIC_API_KEY env var)',
)
@click.option(
    '--obsidian-vault',
    type=click.Path(exists=True),
    help='Path to Obsidian vault directory',
)
@click.option(
    '--show',
    is_flag=True,
    help='Show current configuration',
)
@click.option(
    '--reset',
    is_flag=True,
    help='Reset configuration',
)
def configure(zotero_path, api_key, obsidian_vault, show, reset):
    """
    Configure Papermind settings.

    Stores Zotero path, Claude API key, and Obsidian vault path for future use.

    Examples:
        papermind configure
        papermind configure --zotero-path /path/to/zotero
        papermind configure --api-key sk-ant-...
        papermind configure --obsidian-vault /path/to/vault
        papermind configure --show
        papermind configure --reset
    """
    config = get_config()

    # Show current configuration
    if show:
        console.print("[bold blue]Current Configuration[/bold blue]\n")
        zotero = config.get_zotero_path()
        api = config.get_api_key()
        vault = config.get_obsidian_vault_path()

        if zotero:
            console.print(f"[green]✓[/green] Zotero path: {zotero}")
        else:
            console.print("[yellow]✗[/yellow] Zotero path: Not configured")

        if api:
            masked_key = api[:10] + "..." + api[-4:] if len(api) > 14 else "***"
            console.print(f"[green]✓[/green] Claude API key: {masked_key}")
        else:
            console.print("[yellow]✗[/yellow] Claude API key: Not configured")

        if vault:
            console.print(f"[green]✓[/green] Obsidian vault: {vault}")
        else:
            console.print("[yellow]✗[/yellow] Obsidian vault: Not configured")

        console.print(f"\nConfig file: {config.config_file}")
        return

    # Reset configuration
    if reset:
        if Prompt.ask("\n[yellow]Are you sure you want to reset all configuration?[/yellow]",
                      choices=["y", "n"], default="n") == "y":
            config.clear()
            console.print("[green]✓ Configuration reset[/green]")
        return

    # Interactive configuration
    console.print("[bold blue]Papermind Configuration[/bold blue]\n")

    # Configure Zotero path
    if zotero_path:
        try:
            config.set_zotero_path(zotero_path)
            console.print(f"[green]✓[/green] Zotero path set to: {zotero_path}")
        except ValueError as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            sys.exit(1)
    else:
        current = config.get_zotero_path()
        if current:
            console.print(f"Current Zotero path: {current}")
            if Prompt.ask("Update Zotero path?", choices=["y", "n"], default="n") == "y":
                new_path = Prompt.ask("Enter new Zotero data directory path")
                try:
                    config.set_zotero_path(new_path)
                    console.print(f"[green]✓[/green] Zotero path updated")
                except ValueError as e:
                    console.print(f"[red]✗ Error:[/red] {e}")
                    sys.exit(1)
        else:
            console.print("[yellow]Zotero path not configured[/yellow]")
            if Prompt.ask("Configure now?", choices=["y", "n"], default="y") == "y":
                new_path = Prompt.ask("Enter Zotero data directory path")
                try:
                    config.set_zotero_path(new_path)
                    console.print(f"[green]✓[/green] Zotero path set")
                except ValueError as e:
                    console.print(f"[red]✗ Error:[/red] {e}")
                    sys.exit(1)

    # Configure API key
    if api_key:
        try:
            config.set_api_key(api_key)
            console.print(f"[green]✓[/green] Claude API key configured")
        except ValueError as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            sys.exit(1)
    else:
        current = config.get_api_key()
        if current:
            masked = current[:10] + "..." + current[-4:] if len(current) > 14 else "***"
            console.print(f"Current API key: {masked}")
            if Prompt.ask("Update API key?", choices=["y", "n"], default="n") == "y":
                new_key = Prompt.ask("Enter new Claude API key", password=True)
                try:
                    config.set_api_key(new_key)
                    console.print(f"[green]✓[/green] API key updated")
                except ValueError as e:
                    console.print(f"[red]✗ Error:[/red] {e}")
                    sys.exit(1)
        else:
            console.print("[yellow]Claude API key not configured[/yellow]")
            console.print("(You can also set the ANTHROPIC_API_KEY environment variable)")
            if Prompt.ask("Configure API key now?", choices=["y", "n"], default="y") == "y":
                new_key = Prompt.ask("Enter Claude API key", password=True)
                try:
                    config.set_api_key(new_key)
                    console.print(f"[green]✓[/green] API key configured")
                except ValueError as e:
                    console.print(f"[red]✗ Error:[/red] {e}")
                    sys.exit(1)

    # Configure Obsidian vault path
    if obsidian_vault:
        try:
            config.set_obsidian_vault_path(obsidian_vault)
            console.print(f"[green]✓[/green] Obsidian vault path set to: {obsidian_vault}")
        except ValueError as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            sys.exit(1)
    else:
        current = config.get_obsidian_vault_path()
        if current:
            console.print(f"Current Obsidian vault path: {current}")
            if Prompt.ask("Update Obsidian vault path?", choices=["y", "n"], default="n") == "y":
                new_path = Prompt.ask("Enter new Obsidian vault directory path")
                try:
                    config.set_obsidian_vault_path(new_path)
                    console.print(f"[green]✓[/green] Obsidian vault path updated")
                except ValueError as e:
                    console.print(f"[red]✗ Error:[/red] {e}")
                    sys.exit(1)
        else:
            console.print("[yellow]Obsidian vault path not configured (optional)[/yellow]")
            if Prompt.ask("Configure now?", choices=["y", "n"], default="n") == "y":
                new_path = Prompt.ask("Enter Obsidian vault directory path")
                try:
                    config.set_obsidian_vault_path(new_path)
                    console.print(f"[green]✓[/green] Obsidian vault path set")
                except ValueError as e:
                    console.print(f"[red]✗ Error:[/red] {e}")
                    sys.exit(1)

    console.print("\n[green]Configuration complete![/green]")
    console.print(f"Settings saved to: {config.config_file}")


@main.command()
@click.option(
    '--save-to-zotero/--no-save-to-zotero',
    default=True,
    help='Save analysis as a note in Zotero',
)
@click.option(
    '--output',
    type=click.Path(),
    help='Save analysis to a file',
)
def select(save_to_zotero, output):
    """
    Interactive mode - select collection, paper, and analysis type.

    This is the easiest way to use Papermind. It guides you through:
    1. Selecting a collection (or all papers)
    2. Selecting a paper from the collection
    3. Selecting the type of analysis
    4. Running the analysis

    Example:
        papermind select
    """
    from papermind.pdf import extract_text_from_pdf

    zotero_path, api_key = require_configuration()

    try:
        db = ZoteroDatabase(zotero_path)

        # Step 1: Select collection
        console.print("[bold]Welcome to Papermind Interactive Mode![/bold]\n")
        console.print("Let's analyze a paper from your Zotero library.\n")

        collections = get_collections(db)

        # Add "All Papers" option at the beginning
        all_option = {'id': None, 'name': 'All Papers', 'parent': None}
        collections.insert(0, all_option)

        selected_collection = select_from_list(
            collections,
            "Collections",
            lambda c: c['name'],
            allow_all=False
        )

        if selected_collection is None:
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Step 2: Select paper
        collection_name = selected_collection['name'] if selected_collection['id'] else None

        console.print(f"\n[blue]Loading papers from '{selected_collection['name']}'...[/blue]")

        items = db.list_items(
            collection=collection_name,
            limit=100
        )

        if not items:
            console.print("[yellow]No papers found in this collection.[/yellow]")
            return

        selected_paper = select_from_list(
            items,
            "Papers",
            lambda p: f"{p.get('title', 'Untitled')[:70]} - {p.get('authors', 'Unknown')[:25]} ({p.get('year', 'N/A')})",
            allow_all=False
        )

        if selected_paper is None:
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Step 3: Select analysis type
        analysis_types = [
            {'key': 'quick_summary', 'name': 'Quick Summary', 'desc': 'Brief overview and key takeaways'},
            {'key': 'comprehensive', 'name': 'Comprehensive Analysis', 'desc': 'Full detailed analysis'},
            {'key': 'technical_deep_dive', 'name': 'Technical Deep Dive', 'desc': 'In-depth technical details'},
            {'key': 'literature_review', 'name': 'Literature Review', 'desc': 'Context within existing research'},
            {'key': 'methodology', 'name': 'Methodology Analysis', 'desc': 'Research methods and design'},
            {'key': 'citation_analysis', 'name': 'Citation Analysis', 'desc': 'Citations and related work'},
        ]

        selected_type = select_from_list(
            analysis_types,
            "Analysis Type",
            lambda t: f"{t['name']:<30} - {t['desc']}",
            allow_all=False
        )

        if selected_type is None:
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Step 4: Analyze the paper
        item_id = selected_paper['itemID']
        analysis_type = selected_type['key']

        console.print("\n" + "="*70)
        console.print(f"[bold green]Analyzing Paper[/bold green]")
        console.print("="*70)
        console.print(f"[bold]Title:[/bold] {selected_paper.get('title', 'N/A')}")
        console.print(f"[bold]Authors:[/bold] {selected_paper.get('authors', 'N/A')}")
        console.print(f"[bold]Analysis Type:[/bold] {selected_type['name']}")
        console.print("="*70 + "\n")

        # Get the full item with PDF path
        item = db.get_item(item_id)

        if not item.get('pdf_path'):
            console.print("[red]No PDF attached to this item.[/red]")
            sys.exit(1)

        console.print(f"[blue]Extracting text from PDF...[/blue]")
        paper_text = extract_text_from_pdf(item['pdf_path'])

        if not paper_text or len(paper_text.strip()) < 100:
            console.print("[red]Failed to extract text from PDF or PDF is too short.[/red]")
            sys.exit(1)

        # Analyze with Claude
        console.print(f"[blue]Analyzing with Claude ({selected_type['name']})...[/blue]")
        client = ClaudeClient(api_key=api_key)

        prompt_type_map = {
            'comprehensive': PromptType.COMPREHENSIVE,
            'quick_summary': PromptType.QUICK_SUMMARY,
            'technical_deep_dive': PromptType.TECHNICAL_DEEP_DIVE,
            'literature_review': PromptType.LITERATURE_REVIEW,
            'methodology': PromptType.METHODOLOGY,
            'citation_analysis': PromptType.CITATION_ANALYSIS,
        }

        result = client.analyze_paper(
            paper_text=paper_text,
            metadata={
                'title': item.get('title', ''),
                'authors': item.get('authors', ''),
                'year': item.get('year', ''),
                'publication': item.get('publication', ''),
                'DOI': item.get('DOI', ''),
                'url': item.get('url', ''),
            },
            prompt_type=prompt_type_map[analysis_type],
        )

        # Display analysis
        console.print("\n" + "="*70)
        console.print("[bold green]Analysis Complete[/bold green]")
        console.print("="*70)
        console.print(f"Model: {result['model']}")
        console.print(f"Tokens: {result['input_tokens']} in, {result['output_tokens']} out")
        console.print("="*70 + "\n")
        console.print(result['analysis'])
        console.print("\n" + "="*70)

        # Save to Zotero
        if save_to_zotero:
            console.print("\n[blue]Saving analysis as note to Zotero...[/blue]")
            note_title = f"AI Analysis ({selected_type['name']})"
            db.add_note(item_id, result['analysis'], note_title)
            console.print("[green]✓ Note saved to Zotero[/green]")

        # Save to file
        if output:
            console.print(f"\n[blue]Saving analysis to {output}...[/blue]")
            Path(output).write_text(result['analysis'], encoding='utf-8')
            console.print(f"[green]✓ Saved to {output}[/green]")

        # Show usage stats
        stats = client.get_usage_stats()
        console.print(f"\n[dim]Total tokens used: {stats['total_tokens']}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@main.command()
@click.option(
    '--collection',
    help='Filter by collection name',
)
@click.option(
    '--tag',
    multiple=True,
    help='Filter by tag (can be used multiple times)',
)
@click.option(
    '--limit',
    type=int,
    default=100,
    help='Maximum number of items to display',
)
def list(collection, tag, limit):
    """
    List papers in your Zotero library.

    Examples:
        papermind list
        papermind list --collection "Machine Learning"
        papermind list --tag important --tag unread
    """
    zotero_path, _ = require_configuration()

    try:
        db = ZoteroDatabase(zotero_path)
        items = db.list_items(
            collection=collection,
            tags=list(tag) if tag else None,
            limit=limit
        )

        if not items:
            console.print("[yellow]No items found.[/yellow]")
            return

        # Display results in a table
        table = Table(title=f"Zotero Library ({len(items)} items)")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Authors", style="green")
        table.add_column("Year", style="yellow")

        for item in items:
            table.add_row(
                str(item.get('itemID', '')),
                item.get('title', 'N/A')[:60],
                item.get('authors', 'N/A')[:30],
                str(item.get('year', 'N/A'))
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument('item_id', type=int)
def show(item_id):
    """
    Show detailed information about a specific paper.

    ITEM_ID: The Zotero item ID

    Example:
        papermind show 12345
    """
    zotero_path, _ = require_configuration()

    try:
        db = ZoteroDatabase(zotero_path)
        item = db.get_item(item_id)

        if not item:
            console.print(f"[red]Item {item_id} not found.[/red]")
            sys.exit(1)

        console.print(f"\n[bold]Title:[/bold] {item.get('title', 'N/A')}")
        console.print(f"[bold]Authors:[/bold] {item.get('authors', 'N/A')}")
        console.print(f"[bold]Year:[/bold] {item.get('year', 'N/A')}")
        console.print(f"[bold]Publication:[/bold] {item.get('publication', 'N/A')}")
        console.print(f"[bold]DOI:[/bold] {item.get('DOI', 'N/A')}")
        console.print(f"[bold]URL:[/bold] {item.get('url', 'N/A')}")

        if 'abstract' in item and item['abstract']:
            console.print(f"\n[bold]Abstract:[/bold]\n{item['abstract']}")

        if 'pdf_path' in item and item['pdf_path']:
            console.print(f"\n[bold]PDF:[/bold] {item['pdf_path']}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument('item_id', type=int)
@click.option(
    '--type',
    'analysis_type',
    type=click.Choice([
        'comprehensive',
        'quick_summary',
        'technical_deep_dive',
        'literature_review',
        'methodology',
        'citation_analysis'
    ]),
    default='comprehensive',
    help='Type of analysis to perform',
)
@click.option(
    '--save-to-zotero/--no-save-to-zotero',
    default=True,
    help='Save analysis as a note in Zotero',
)
@click.option(
    '--output',
    type=click.Path(),
    help='Save analysis to a file',
)
def analyze(item_id, analysis_type, save_to_zotero, output):
    """
    Analyze a paper with Claude AI.

    ITEM_ID: The Zotero item ID to analyze

    Examples:
        papermind analyze 12345
        papermind analyze 12345 --type quick_summary
        papermind analyze 12345 --output report.md
    """
    from papermind.pdf import extract_text_from_pdf

    zotero_path, api_key = require_configuration()

    try:
        # Get paper from Zotero
        console.print(f"[blue]Loading paper {item_id} from Zotero...[/blue]")
        db = ZoteroDatabase(zotero_path)
        item = db.get_item(item_id)

        if not item:
            console.print(f"[red]Item {item_id} not found.[/red]")
            sys.exit(1)

        # Extract PDF text
        if not item.get('pdf_path'):
            console.print("[red]No PDF attached to this item.[/red]")
            sys.exit(1)

        console.print(f"[blue]Extracting text from PDF...[/blue]")
        paper_text = extract_text_from_pdf(item['pdf_path'])

        if not paper_text or len(paper_text.strip()) < 100:
            console.print("[red]Failed to extract text from PDF or PDF is too short.[/red]")
            sys.exit(1)

        # Analyze with Claude
        console.print(f"[blue]Analyzing with Claude ({analysis_type})...[/blue]")
        client = ClaudeClient(api_key=api_key)

        prompt_type_map = {
            'comprehensive': PromptType.COMPREHENSIVE,
            'quick_summary': PromptType.QUICK_SUMMARY,
            'technical_deep_dive': PromptType.TECHNICAL_DEEP_DIVE,
            'literature_review': PromptType.LITERATURE_REVIEW,
            'methodology': PromptType.METHODOLOGY,
            'citation_analysis': PromptType.CITATION_ANALYSIS,
        }

        result = client.analyze_paper(
            paper_text=paper_text,
            metadata={
                'title': item.get('title', ''),
                'authors': item.get('authors', ''),
                'year': item.get('year', ''),
                'publication': item.get('publication', ''),
                'DOI': item.get('DOI', ''),
                'url': item.get('url', ''),
            },
            prompt_type=prompt_type_map[analysis_type],
        )

        # Display analysis
        console.print("\n" + "="*70)
        console.print("[bold green]Analysis Complete[/bold green]")
        console.print("="*70)
        console.print(f"Model: {result['model']}")
        console.print(f"Tokens: {result['input_tokens']} in, {result['output_tokens']} out")
        console.print("="*70 + "\n")
        console.print(result['analysis'])
        console.print("\n" + "="*70)

        # Save to Zotero
        if save_to_zotero:
            console.print("\n[blue]Saving analysis as note to Zotero...[/blue]")
            note_title = f"AI Analysis ({analysis_type})"
            db.add_note(item_id, result['analysis'], note_title)
            console.print("[green]✓ Note saved to Zotero[/green]")

        # Save to file
        if output:
            console.print(f"\n[blue]Saving analysis to {output}...[/blue]")
            Path(output).write_text(result['analysis'], encoding='utf-8')
            console.print(f"[green]✓ Saved to {output}[/green]")

        # Show usage stats
        stats = client.get_usage_stats()
        console.print(f"\n[dim]Total tokens used: {stats['total_tokens']}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@main.command()
@click.option(
    '--collection',
    help='Process items in this collection',
)
@click.option(
    '--tag',
    multiple=True,
    help='Process items with these tags',
)
@click.option(
    '--limit',
    type=int,
    help='Maximum number of items to process',
)
@click.option(
    '--type',
    'analysis_type',
    type=click.Choice([
        'comprehensive',
        'quick_summary',
        'technical_deep_dive',
        'literature_review',
        'methodology',
        'citation_analysis'
    ]),
    default='quick_summary',
    help='Type of analysis to perform',
)
def batch(collection, tag, limit, analysis_type):
    """
    Batch process multiple papers.

    Examples:
        papermind batch --collection "To Read" --type quick_summary
        papermind batch --tag important --limit 10
    """
    from rich.progress import Progress

    zotero_path, api_key = require_configuration()

    try:
        db = ZoteroDatabase(zotero_path)
        items = db.list_items(
            collection=collection,
            tags=list(tag) if tag else None,
            limit=limit
        )

        if not items:
            console.print("[yellow]No items found to process.[/yellow]")
            return

        console.print(f"[blue]Processing {len(items)} items...[/blue]\n")

        with Progress() as progress:
            task = progress.add_task("[cyan]Analyzing papers...", total=len(items))

            for item in items:
                item_id = item.get('itemID')
                title = item.get('title', 'Unknown')[:40]

                progress.console.print(f"Processing: {title}...")

                # TODO: Implement batch processing
                # For now, just show progress
                progress.update(task, advance=1)

        console.print("\n[green]Batch processing complete![/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option(
    '--vault-path',
    type=click.Path(exists=True),
    help='Path to Obsidian vault (or configure with: papermind configure)',
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be synced without making changes',
)
def sync(vault_path, dry_run):
    """
    Sync Zotero library to Obsidian vault.

    Creates a structured Obsidian vault with:
    - zotero/{item_key}/paper.md - Papers with frontmatter metadata
    - zotero/{item_key}/*.pdf - PDF attachments
    - collections/{collection_name}.md - Dataview query files

    The sync uses Dataview queries for dynamic collection views.
    Make sure you have the Dataview plugin installed in Obsidian.

    Examples:
        papermind sync
        papermind sync --vault-path /path/to/vault
        papermind sync --dry-run
    """
    zotero_path, _ = require_configuration()

    config = get_config()

    # Determine vault path
    if not vault_path:
        vault_path = config.get_obsidian_vault_path()

    if not vault_path:
        console.print("[yellow]Obsidian vault path not configured.[/yellow]")
        console.print("Please either:")
        console.print("  1. Run: [cyan]papermind configure[/cyan] to set the vault path")
        console.print("  2. Use: [cyan]papermind sync --vault-path /path/to/vault[/cyan]")
        sys.exit(1)

    try:
        db = ZoteroDatabase(zotero_path)

        if dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

        console.print(f"[blue]Syncing Zotero library to Obsidian vault...[/blue]")
        console.print(f"[blue]Vault: {vault_path}[/blue]\n")

        # Perform sync
        stats = sync_to_obsidian(db, vault_path, dry_run=dry_run)

        # Display results
        console.print("\n" + "="*70)
        console.print("[bold green]Sync Complete[/bold green]")
        console.print("="*70)
        console.print(f"[green]✓[/green] Papers synced: {stats['papers_synced']}")
        console.print(f"[green]✓[/green] Files copied: {stats['files_copied']}")
        console.print(f"[green]✓[/green] Collections created: {stats['collections_created']}")

        if stats['errors']:
            console.print(f"\n[yellow]⚠ Errors encountered: {len(stats['errors'])}[/yellow]")
            for error in stats['errors'][:5]:  # Show first 5 errors
                console.print(f"  [red]•[/red] {error}")
            if len(stats['errors']) > 5:
                console.print(f"  [dim]... and {len(stats['errors']) - 5} more[/dim]")

        console.print("="*70)

        if not dry_run:
            console.print("\n[green]Your Zotero library has been synced to Obsidian![/green]")
            console.print("[dim]Make sure you have the Dataview plugin installed in Obsidian.[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@main.command()
@click.option(
    '--vault-path',
    type=click.Path(exists=True),
    help='Path to Obsidian vault (or configure with: papermind configure)',
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be synced without making changes',
)
@click.option(
    '--overwrite',
    is_flag=True,
    help='Overwrite existing notes with same title in Zotero',
)
def sync_notes(vault_path, dry_run, overwrite):
    """
    Sync notes/reports from Obsidian back to Zotero.

    Scans zotero/{item_key}/ directories for .md files (excluding paper.md)
    and saves them as notes in Zotero. This allows you to:

    1. Use Claude CLI to generate reports in paper directories
    2. Sync those reports back to Zotero as notes

    Notes are identified by their filename. If a note with the same title
    already exists in Zotero, it will be skipped unless --overwrite is used.

    Examples:
        papermind sync-notes
        papermind sync-notes --vault-path /path/to/vault
        papermind sync-notes --dry-run
        papermind sync-notes --overwrite
    """
    zotero_path, _ = require_configuration()

    config = get_config()

    # Determine vault path
    if not vault_path:
        vault_path = config.get_obsidian_vault_path()

    if not vault_path:
        console.print("[yellow]Obsidian vault path not configured.[/yellow]")
        console.print("Please either:")
        console.print("  1. Run: [cyan]papermind configure[/cyan] to set the vault path")
        console.print("  2. Use: [cyan]papermind sync-notes --vault-path /path/to/vault[/cyan]")
        sys.exit(1)

    try:
        db = ZoteroDatabase(zotero_path)

        if dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

        console.print(f"[blue]Syncing notes from Obsidian to Zotero...[/blue]")
        console.print(f"[blue]Vault: {vault_path}[/blue]\n")

        # Perform sync
        stats = sync_notes_to_zotero(db, vault_path, dry_run=dry_run, overwrite=overwrite)

        # Display results
        console.print("\n" + "="*70)
        console.print("[bold green]Sync Complete[/bold green]")
        console.print("="*70)
        console.print(f"[green]✓[/green] Notes synced: {stats['notes_synced']}")
        console.print(f"[yellow]⊘[/yellow] Notes skipped: {stats['notes_skipped']}")

        if stats['errors']:
            console.print(f"\n[yellow]⚠ Errors encountered: {len(stats['errors'])}[/yellow]")
            for error in stats['errors'][:5]:  # Show first 5 errors
                console.print(f"  [red]•[/red] {error}")
            if len(stats['errors']) > 5:
                console.print(f"  [dim]... and {len(stats['errors']) - 5} more[/dim]")

        console.print("="*70)

        if not dry_run and stats['notes_synced'] > 0:
            console.print("\n[green]Your notes have been synced to Zotero![/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
