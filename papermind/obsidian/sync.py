"""Sync Zotero library to Obsidian vault."""

import shutil
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.progress import Progress
import re
from html.parser import HTMLParser

console = Console()


class HTMLStripper(HTMLParser):
    """Simple HTML tag stripper."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return ''.join(self.text)


def strip_html_tags(html_content: str) -> str:
    """Strip HTML tags from content."""
    stripper = HTMLStripper()
    try:
        stripper.feed(html_content)
        return stripper.get_data().strip()
    except Exception:
        # If HTML parsing fails, try simple regex
        return re.sub('<[^<]+?>', '', html_content).strip()


def sync_to_obsidian(
    zotero_db,
    vault_path: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sync Zotero library to Obsidian vault using Dataview structure.

    Creates:
    - zotero/{item_key}/paper.md with frontmatter metadata
    - zotero/{item_key}/{attachments}
    - collections/{collection_name}.md with Dataview queries

    Args:
        zotero_db: ZoteroDatabase instance
        vault_path: Path to Obsidian vault
        dry_run: If True, only show what would be synced without making changes

    Returns:
        Dict with sync statistics
    """
    vault = Path(vault_path)
    if not vault.exists():
        raise ValueError(f"Obsidian vault path does not exist: {vault_path}")

    stats = {
        'papers_synced': 0,
        'files_copied': 0,
        'collections_created': 0,
        'errors': []
    }

    # Create main directories
    zotero_base = vault / "Zotero"
    zotero_dir = zotero_base / "repo"
    collections_dir = zotero_base / "collections"

    if not dry_run:
        zotero_base.mkdir(exist_ok=True)
        zotero_dir.mkdir(exist_ok=True)
        collections_dir.mkdir(exist_ok=True)

    # Get all items from Zotero
    console.print("[blue]Fetching all items from Zotero...[/blue]")
    items = zotero_db.list_items(limit=999999)  # Large number to get all items

    if not items:
        console.print("[yellow]No items found in Zotero library.[/yellow]")
        return stats

    # Get all collections
    console.print("[blue]Fetching collections...[/blue]")
    collections = _get_collections_with_items(zotero_db)

    # Sync papers
    console.print(f"\n[blue]Syncing {len(items)} papers...[/blue]")

    with Progress() as progress:
        task = progress.add_task("[cyan]Syncing papers...", total=len(items))

        for item in items:
            try:
                files_copied = _sync_paper(item, zotero_dir, zotero_db, collections, dry_run)
                if files_copied is not None:
                    stats['papers_synced'] += 1
                    stats['files_copied'] += files_copied

            except Exception as e:
                error_msg = f"Error syncing item {item.get('itemID')}: {str(e)}"
                stats['errors'].append(error_msg)
                console.print(f"[red]{error_msg}[/red]")

            progress.update(task, advance=1)

    # Sync collections
    console.print(f"\n[blue]Creating {len(collections)} collection views...[/blue]")

    for collection_name, collection_data in collections.items():
        try:
            if _create_collection_view(
                collection_name,
                collection_data,
                collections_dir,
                dry_run
            ):
                stats['collections_created'] += 1
        except Exception as e:
            error_msg = f"Error creating collection view '{collection_name}': {str(e)}"
            stats['errors'].append(error_msg)
            console.print(f"[red]{error_msg}[/red]")

    return stats


def _sync_paper(
    item: Dict[str, Any],
    zotero_dir: Path,
    zotero_db,
    collections: Dict[str, Dict],
    dry_run: bool
) -> Optional[int]:
    """
    Sync a single paper to Obsidian.

    Args:
        item: Item data from Zotero
        zotero_dir: Path to zotero/ directory in vault
        zotero_db: ZoteroDatabase instance
        collections: Dict mapping collection names to their data
        dry_run: If True, don't make changes

    Returns:
        Number of files copied (0 if no files, None if failed)
    """
    item_key = item.get('key')
    if not item_key:
        return None

    files_copied = 0

    # Create item directory
    item_dir = zotero_dir / item_key

    if not dry_run:
        item_dir.mkdir(exist_ok=True)

    # Find which collections this item belongs to
    item_collections = _get_item_collections(item, collections)

    # Generate paper.md with frontmatter
    paper_content = _generate_paper_markdown(item, item_collections)

    if not dry_run:
        paper_file = item_dir / "paper.md"
        paper_file.write_text(paper_content, encoding='utf-8')

    # Save Zotero notes as individual .txt files
    try:
        notes = zotero_db.get_notes(item.get('itemID'))
        for i, note in enumerate(notes, 1):
            raw_content = note.get('content', '')

            # Strip HTML tags from content
            clean_content = strip_html_tags(raw_content)

            if not clean_content:
                continue  # Skip empty notes

            # Use first line or first 50 chars as title
            lines = clean_content.split('\n', 1)
            first_line = lines[0].strip()

            # Create title from first line (max 50 chars)
            if first_line:
                title = first_line[:50]
            else:
                title = f'note-{i}'

            # Sanitize filename
            safe_title = _sanitize_filename(title)

            # Add number suffix if multiple notes with same title
            note_filename = f"{safe_title}.md"
            if (item_dir / note_filename).exists() and not dry_run:
                note_filename = f"{safe_title}-{i}.md"

            if not dry_run:
                note_file = item_dir / note_filename
                note_file.write_text(clean_content, encoding='utf-8')
    except Exception as e:
        pass  # If notes can't be retrieved, continue without them

    # Copy all attachments
    attachments = item.get('attachments', [])
    for attachment in attachments:
        try:
            source_path = Path(attachment['path'])
            if source_path.exists() and source_path.is_file():
                if not dry_run:
                    dest_path = item_dir / source_path.name
                    # Only copy if doesn't exist or source is newer
                    if not dest_path.exists() or dest_path.stat().st_mtime < source_path.stat().st_mtime:
                        shutil.copy2(source_path, dest_path)
                        files_copied += 1
        except Exception:
            pass  # Skip problematic attachments

    return files_copied


def _generate_paper_markdown(
    item: Dict[str, Any],
    collections: List[str]
) -> str:
    """
    Generate markdown file content with frontmatter metadata.

    Args:
        item: Item data from Zotero
        collections: List of collection names this item belongs to

    Returns:
        Markdown content with YAML frontmatter
    """
    # Build frontmatter
    frontmatter = ["---"]

    # Required fields
    title = item.get('title', 'Untitled').replace('"', '\\"')
    frontmatter.append(f'title: "{title}"')

    # Authors
    authors_str = item.get('authors', '')
    if authors_str:
        # Split authors and format as YAML list
        authors = [a.strip() for a in authors_str.split(',') if a.strip()]
        if authors:
            frontmatter.append('authors:')
            for author in authors:
                frontmatter.append(f'  - "{author.replace(chr(34), chr(92)+chr(34))}"')

    # Collections
    if collections:
        frontmatter.append('collections:')
        for collection in collections:
            frontmatter.append(f'  - "{collection.replace(chr(34), chr(92)+chr(34))}"')

    # Year
    year = item.get('year', '')
    if year:
        frontmatter.append(f'year: {year}')

    # Publication
    publication = item.get('publication', '')
    if publication:
        frontmatter.append(f'publication: "{publication.replace(chr(34), chr(92)+chr(34))}"')

    # DOI
    doi = item.get('DOI', '')
    if doi:
        frontmatter.append(f'doi: "{doi}"')

    # URL
    url = item.get('url', '')
    if url:
        frontmatter.append(f'url: "{url}"')

    # Tags
    tags = item.get('tags', [])
    if tags:
        frontmatter.append('tags:')
        for tag in tags:
            frontmatter.append(f'  - "{tag.replace(chr(34), chr(92)+chr(34))}"')

    # Item ID and Key
    frontmatter.append(f'zotero_id: {item.get("itemID", "")}')
    frontmatter.append(f'zotero_key: "{item.get("key", "")}"')

    # Dates
    date_added = item.get('dateAdded', '')
    if date_added:
        frontmatter.append(f'date_added: "{date_added}"')

    date_modified = item.get('dateModified', '')
    if date_modified:
        frontmatter.append(f'date_modified: "{date_modified}"')

    frontmatter.append("---")

    # Build content body
    body_parts = ["\n"]

    # Abstract
    abstract = item.get('abstract', '') or item.get('abstractNote', '')
    if abstract:
        body_parts.append("## Abstract\n\n")
        body_parts.append(f"{abstract}\n\n")

    # Attachments section
    attachments = item.get('attachments', [])
    if attachments:
        body_parts.append("## Attachments\n\n")
        for attachment in attachments:
            file_path = Path(attachment['path'])
            file_name = file_path.name
            body_parts.append(f"- [[{file_name}]]\n")
        body_parts.append("\n")

    # Notes section
    body_parts.append("## Notes\n\n")
    body_parts.append("*Add your notes here. Use Claude CLI to generate reports.*\n")

    return '\n'.join(frontmatter) + ''.join(body_parts)


def _create_collection_view(
    collection_name: str,
    collection_data: Dict[str, Any],
    collections_dir: Path,
    dry_run: bool
) -> bool:
    """
    Create a Dataview query file for a collection.

    Args:
        collection_name: Name of the collection
        collection_data: Collection metadata and items
        collections_dir: Path to collections/ directory
        dry_run: If True, don't make changes

    Returns:
        True if created successfully
    """
    # Sanitize filename
    safe_name = _sanitize_filename(collection_name)
    collection_file = collections_dir / f"{safe_name}.md"

    # Build Dataview query
    content = [f"# {collection_name}\n"]

    # Add collection description if available
    if collection_data.get('description'):
        content.append(f"> {collection_data['description']}\n\n")

    # Add Dataview query
    content.append("```dataview\n")
    content.append("TABLE\n")
    content.append("  file.link as Paper,\n")
    content.append("  title as Title\n")
    content.append('FROM "Zotero/repo"\n')
    content.append(f'WHERE contains(collections, "{collection_name}")\n')
    content.append("SORT title ASC\n")
    content.append("```\n\n")

    # Add item count
    item_count = collection_data.get('item_count', 0)
    content.append(f"*{item_count} papers in this collection*\n")

    if not dry_run:
        collection_file.write_text(''.join(content), encoding='utf-8')

    return True


def _get_collections_with_items(zotero_db) -> Dict[str, Dict[str, Any]]:
    """
    Get all collections with their items.

    Args:
        zotero_db: ZoteroDatabase instance

    Returns:
        Dict mapping collection names to their data and item IDs
    """
    conn = zotero_db._get_connection()
    cursor = conn.cursor()

    # Get all collections
    cursor.execute("""
        SELECT collectionID, collectionName, parentCollectionID
        FROM collections
        WHERE collectionID NOT IN (SELECT collectionID FROM deletedCollections)
        ORDER BY collectionName
    """)

    collections = {}
    collection_id_map = {}

    for row in cursor.fetchall():
        coll_id = row['collectionID']
        coll_name = row['collectionName']

        collections[coll_name] = {
            'id': coll_id,
            'name': coll_name,
            'parent': row['parentCollectionID'],
            'items': [],
            'item_count': 0
        }
        collection_id_map[coll_id] = coll_name

    # Get items in each collection
    cursor.execute("""
        SELECT collectionID, itemID
        FROM collectionItems
        WHERE itemID NOT IN (SELECT itemID FROM deletedItems)
    """)

    for row in cursor.fetchall():
        coll_id = row['collectionID']
        item_id = row['itemID']

        if coll_id in collection_id_map:
            coll_name = collection_id_map[coll_id]
            collections[coll_name]['items'].append(item_id)
            collections[coll_name]['item_count'] += 1

    conn.close()
    return collections


def _get_item_collections(item: Dict[str, Any], collections: Dict[str, Dict]) -> List[str]:
    """
    Get list of collection names that contain this item.

    Args:
        item: Item data
        collections: Dict of all collections with their items

    Returns:
        List of collection names
    """
    item_id = item.get('itemID')
    if not item_id:
        return []

    item_collections = []
    for coll_name, coll_data in collections.items():
        if item_id in coll_data['items']:
            item_collections.append(coll_name)

    return item_collections


def _sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use as a filename.

    Args:
        name: Original name

    Returns:
        Sanitized filename-safe string
    """
    # Replace invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')

    # Remove leading/trailing spaces and dots
    name = name.strip('. ')

    # Limit length
    if len(name) > 200:
        name = name[:200]

    return name


def sync_notes_to_zotero(
    zotero_db,
    vault_path: str,
    dry_run: bool = False,
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Sync notes/reports from Obsidian vault back to Zotero.

    Scans zotero/{item_key}/ directories for .md files (excluding paper.md)
    and saves them as notes in Zotero.

    Args:
        zotero_db: ZoteroDatabase instance
        vault_path: Path to Obsidian vault
        dry_run: If True, only show what would be synced without making changes
        overwrite: If True, update existing notes with same title

    Returns:
        Dict with sync statistics
    """
    vault = Path(vault_path)
    if not vault.exists():
        raise ValueError(f"Obsidian vault path does not exist: {vault_path}")

    zotero_dir = vault / "Zotero" / "repo"
    if not zotero_dir.exists():
        console.print("[yellow]No Zotero/repo directory found in vault. Run 'papermind sync' first.[/yellow]")
        return {'notes_synced': 0, 'errors': []}

    stats = {
        'notes_synced': 0,
        'notes_skipped': 0,
        'errors': []
    }

    console.print("[blue]Scanning Obsidian vault for notes to sync...[/blue]")

    # Get all paper directories
    paper_dirs = [d for d in zotero_dir.iterdir() if d.is_dir()]

    if not paper_dirs:
        console.print("[yellow]No paper directories found in vault.[/yellow]")
        return stats

    notes_to_sync = []

    # Scan each paper directory for notes
    for paper_dir in paper_dirs:
        item_key = paper_dir.name

        # Read paper.md to get zotero_id
        paper_md = paper_dir / "paper.md"
        if not paper_md.exists():
            continue

        # Extract zotero_id from frontmatter
        zotero_id = _extract_zotero_id(paper_md)
        if not zotero_id:
            console.print(f"[yellow]Could not find zotero_id in {paper_md}[/yellow]")
            continue

        # Find all .md files except paper.md
        note_files = [f for f in paper_dir.glob("*.md") if f.name != "paper.md"]

        for note_file in note_files:
            notes_to_sync.append({
                'file': note_file,
                'item_key': item_key,
                'zotero_id': zotero_id,
                'note_title': note_file.stem  # Use filename (without .md) as note title
            })

    if not notes_to_sync:
        console.print("[yellow]No notes found to sync (only paper.md files exist).[/yellow]")
        return stats

    console.print(f"\n[blue]Found {len(notes_to_sync)} notes to sync...[/blue]")

    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

    # Sync notes
    with Progress() as progress:
        task = progress.add_task("[cyan]Syncing notes to Zotero...", total=len(notes_to_sync))

        for note_info in notes_to_sync:
            try:
                # Read note content
                note_content = note_info['file'].read_text(encoding='utf-8')

                # Check if note already exists
                existing_notes = zotero_db.get_notes(note_info['zotero_id'])
                note_exists = False

                for existing_note in existing_notes:
                    # Check if note with this title exists (title is on first line)
                    content = existing_note.get('content', '')
                    if content.startswith(note_info['note_title'] + '\n'):
                        note_exists = True
                        if not overwrite:
                            stats['notes_skipped'] += 1
                            progress.console.print(
                                f"[yellow]Skipped:[/yellow] {note_info['file'].name} "
                                f"(already exists for item {note_info['item_key']})"
                            )
                            break

                if not note_exists or overwrite:
                    if not dry_run:
                        # Add note to Zotero
                        zotero_db.add_note(
                            note_info['zotero_id'],
                            note_content,
                            note_info['note_title']
                        )

                    stats['notes_synced'] += 1
                    progress.console.print(
                        f"[green]✓[/green] Synced: {note_info['file'].name} "
                        f"→ Zotero item {note_info['item_key']}"
                    )

            except Exception as e:
                error_msg = f"Error syncing {note_info['file'].name}: {str(e)}"
                stats['errors'].append(error_msg)
                progress.console.print(f"[red]{error_msg}[/red]")

            progress.update(task, advance=1)

    return stats


def _extract_zotero_id(paper_md_path: Path) -> Optional[int]:
    """
    Extract zotero_id from paper.md frontmatter.

    Args:
        paper_md_path: Path to paper.md file

    Returns:
        Zotero item ID or None if not found
    """
    try:
        content = paper_md_path.read_text(encoding='utf-8')

        # Extract frontmatter
        match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return None

        frontmatter = match.group(1)

        # Find zotero_id
        id_match = re.search(r'zotero_id:\s*(\d+)', frontmatter)
        if id_match:
            return int(id_match.group(1))

        return None
    except Exception:
        return None
