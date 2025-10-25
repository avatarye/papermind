"""Zotero SQLite database interface with read and write capabilities."""

import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class ZoteroDatabase:
    """
    Interface for reading from and writing to Zotero SQLite database.

    Supports:
    - Reading item metadata
    - Querying by collection, tags, authors
    - Finding attached PDFs
    - Writing notes back to Zotero items
    """

    def __init__(self, zotero_path: Optional[str] = None):
        """
        Initialize Zotero database connection.

        Args:
            zotero_path: Path to Zotero data directory.
                        If None, tries common default locations.
        """
        self.zotero_path = self._find_zotero_path(zotero_path)
        self.db_path = Path(self.zotero_path) / "zotero.sqlite"

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Zotero database not found at {self.db_path}. "
                "Please specify the correct Zotero data directory."
            )

        self.storage_path = Path(self.zotero_path) / "storage"

    def _find_zotero_path(self, provided_path: Optional[str] = None) -> str:
        """Find Zotero data directory."""
        if provided_path:
            return provided_path

        # Try common default locations
        home = Path.home()

        if os.name == 'nt':  # Windows
            possible_paths = [
                home / "Zotero",
                Path(os.getenv('APPDATA', '')) / "Zotero" / "Zotero" / "Profiles",
            ]
        else:  # Linux/Mac
            possible_paths = [
                home / "Zotero",
                home / ".zotero",
                home / "snap" / "zotero-snap" / "common" / "Zotero",
            ]

        for path in possible_paths:
            if path.exists() and (path / "zotero.sqlite").exists():
                return str(path)

        # If not found, try the first default
        return str(possible_paths[0])

    def _get_connection(self) -> sqlite3.Connection:
        """Get a read-only database connection."""
        # Use URI mode for read-only access (safer when Zotero might be running)
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_write_connection(self) -> sqlite3.Connection:
        """Get a writable database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def list_items(
        self,
        collection: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List items in Zotero library.

        Args:
            collection: Filter by collection name
            tags: Filter by tag names (all must match)
            limit: Maximum number of items to return

        Returns:
            List of item dictionaries with metadata
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT DISTINCT
                i.itemID,
                i.key,
                iv.value AS title,
                i.dateAdded,
                i.dateModified
            FROM items i
            JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
            LEFT JOIN itemData id ON i.itemID = id.itemID
            LEFT JOIN fields f ON id.fieldID = f.fieldID
            LEFT JOIN itemDataValues iv ON id.valueID = iv.valueID
            WHERE i.itemID NOT IN (SELECT itemID FROM deletedItems)
                AND f.fieldName = 'title'
                AND it.typeName NOT IN ('attachment', 'note')
                AND i.itemID NOT IN (
                    SELECT itemID FROM itemAttachments
                    UNION
                    SELECT itemID FROM itemNotes WHERE parentItemID IS NOT NULL
                )
        """

        params = []

        # Filter by collection
        if collection:
            query += """
                AND i.itemID IN (
                    SELECT itemID FROM collectionItems ci
                    JOIN collections c ON ci.collectionID = c.collectionID
                    WHERE c.collectionName = ?
                )
            """
            params.append(collection)

        # Filter by tags
        if tags:
            for tag in tags:
                query += """
                    AND i.itemID IN (
                        SELECT itemID FROM itemTags it
                        JOIN tags t ON it.tagID = t.tagID
                        WHERE t.name = ?
                    )
                """
                params.append(tag)

        query += " ORDER BY i.dateModified DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        items = []
        for row in rows:
            item_data = dict(row)
            # Get additional metadata
            item_data.update(self._get_item_metadata(cursor, row['itemID']))
            items.append(item_data)

        conn.close()
        return items

    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific item.

        Args:
            item_id: Zotero item ID

        Returns:
            Dictionary with item metadata, or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT itemID, key, dateAdded, dateModified
            FROM items
            WHERE itemID = ? AND itemID NOT IN (SELECT itemID FROM deletedItems)
        """, (item_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        item = dict(row)
        item.update(self._get_item_metadata(cursor, item_id))

        # Get PDF path
        pdf_path = self._get_pdf_path(cursor, item_id)
        if pdf_path:
            item['pdf_path'] = pdf_path

        conn.close()
        return item

    def _get_item_metadata(self, cursor, item_id: int) -> Dict[str, Any]:
        """Get all metadata fields for an item."""
        cursor.execute("""
            SELECT f.fieldName, iv.value
            FROM itemData id
            JOIN fields f ON id.fieldID = f.fieldID
            JOIN itemDataValues iv ON id.valueID = iv.valueID
            WHERE id.itemID = ?
        """, (item_id,))

        metadata = {}
        for row in cursor.fetchall():
            metadata[row['fieldName']] = row['value']

        # Get authors/creators
        cursor.execute("""
            SELECT ct.creatorType, c.firstName, c.lastName
            FROM itemCreators ic
            JOIN creators c ON ic.creatorID = c.creatorID
            JOIN creatorTypes ct ON ic.creatorTypeID = ct.creatorTypeID
            WHERE ic.itemID = ?
            ORDER BY ic.orderIndex
        """, (item_id,))

        authors = []
        for row in cursor.fetchall():
            name = f"{row['firstName']} {row['lastName']}".strip()
            if name:
                authors.append(name)

        if authors:
            metadata['authors'] = ', '.join(authors)

        # Get tags
        cursor.execute("""
            SELECT t.name
            FROM itemTags it
            JOIN tags t ON it.tagID = t.tagID
            WHERE it.itemID = ?
        """, (item_id,))

        tags = [row['name'] for row in cursor.fetchall()]
        if tags:
            metadata['tags'] = tags

        return metadata

    def _get_pdf_path(self, cursor, item_id: int) -> Optional[str]:
        """Get path to attached PDF file."""
        cursor.execute("""
            SELECT ia.path, i.key
            FROM itemAttachments ia
            JOIN items i ON ia.itemID = i.itemID
            WHERE ia.parentItemID = ?
                AND ia.contentType = 'application/pdf'
            LIMIT 1
        """, (item_id,))

        row = cursor.fetchone()
        if not row:
            return None

        # PDF can be stored with relative path or in storage directory
        if row['path']:
            # Has explicit path
            pdf_path = Path(row['path'])
            if pdf_path.exists():
                return str(pdf_path)

        # Try storage directory
        storage_dir = self.storage_path / row['key']
        if storage_dir.exists():
            # Find PDF in storage directory
            pdf_files = list(storage_dir.glob("*.pdf"))
            if pdf_files:
                return str(pdf_files[0])

        return None

    def add_note(
        self,
        parent_item_id: int,
        note_content: str,
        note_title: Optional[str] = None
    ) -> int:
        """
        Add a note to a Zotero item.

        Args:
            parent_item_id: ID of the parent item to attach note to
            note_content: Content of the note (plain text)
            note_title: Optional title for the note (will be first line)

        Returns:
            The itemID of the created note

        Raises:
            sqlite3.Error: If database write fails
            ValueError: If parent item doesn't exist
        """
        # Verify parent item exists
        conn = self._get_write_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT itemID, libraryID FROM items
            WHERE itemID = ? AND itemID NOT IN (SELECT itemID FROM deletedItems)
        """, (parent_item_id,))

        parent_row = cursor.fetchone()
        if not parent_row:
            conn.close()
            raise ValueError(f"Parent item {parent_item_id} not found")

        library_id = parent_row['libraryID']

        try:
            # Get the note item type ID
            cursor.execute("SELECT itemTypeID FROM itemTypes WHERE typeName = 'note'")
            note_type_id = cursor.fetchone()['itemTypeID']

            # Generate a unique key for the note
            import hashlib
            import time
            key = hashlib.md5(f"{parent_item_id}{time.time()}".encode()).hexdigest()[:8].upper()

            # Insert the note item
            cursor.execute("""
                INSERT INTO items (itemTypeID, libraryID, dateAdded, dateModified, key)
                VALUES (?, ?, ?, ?, ?)
            """, (
                note_type_id,
                library_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                key
            ))

            note_item_id = cursor.lastrowid

            # Format note as pure text with title on first line
            title = note_title or 'AI Analysis'
            text_content = f"{title}\n\n{note_content}"

            # Insert the note content
            cursor.execute("""
                INSERT INTO itemNotes (itemID, parentItemID, note)
                VALUES (?, ?, ?)
            """, (note_item_id, parent_item_id, text_content))

            conn.commit()
            conn.close()

            return note_item_id

        except Exception as e:
            conn.rollback()
            conn.close()
            raise sqlite3.Error(f"Failed to add note: {e}")

    def get_notes(self, parent_item_id: int) -> List[Dict[str, Any]]:
        """
        Get all notes attached to an item.

        Args:
            parent_item_id: ID of the parent item

        Returns:
            List of notes with their content
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.itemID,
                i.key,
                i.dateAdded,
                i.dateModified,
                n.note
            FROM itemNotes n
            JOIN items i ON n.itemID = i.itemID
            WHERE n.parentItemID = ?
                AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
            ORDER BY i.dateModified DESC
        """, (parent_item_id,))

        notes = []
        for row in cursor.fetchall():
            notes.append({
                'itemID': row['itemID'],
                'key': row['key'],
                'dateAdded': row['dateAdded'],
                'dateModified': row['dateModified'],
                'content': row['note'],
            })

        conn.close()
        return notes

    def search_items(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for items by text query.

        Args:
            query: Search query (searches title, abstract, and creators)
            limit: Maximum number of results

        Returns:
            List of matching items
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{query}%"

        cursor.execute("""
            SELECT DISTINCT i.itemID
            FROM items i
            LEFT JOIN itemData id ON i.itemID = id.itemID
            LEFT JOIN itemDataValues iv ON id.valueID = iv.valueID
            LEFT JOIN itemCreators ic ON i.itemID = ic.itemID
            LEFT JOIN creators c ON ic.creatorID = c.creatorID
            WHERE i.itemID NOT IN (SELECT itemID FROM deletedItems)
                AND (
                    iv.value LIKE ?
                    OR c.firstName LIKE ?
                    OR c.lastName LIKE ?
                )
            LIMIT ?
        """, (search_pattern, search_pattern, search_pattern, limit))

        item_ids = [row['itemID'] for row in cursor.fetchall()]
        conn.close()

        return [self.get_item(item_id) for item_id in item_ids if self.get_item(item_id)]
