"""PDF text extraction utilities."""

from pathlib import Path
from typing import Optional
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as a string, or None if extraction fails

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF reading fails
    """
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        reader = PdfReader(str(pdf_file))

        # Extract text from all pages
        text_parts = []
        for page_num, page in enumerate(reader.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                # Log error but continue with other pages
                print(f"Warning: Failed to extract text from page {page_num}: {e}")
                continue

        if not text_parts:
            return None

        # Join all pages
        full_text = "\n\n".join(text_parts)

        # Basic cleanup
        full_text = _clean_text(full_text)

        return full_text

    except Exception as e:
        raise Exception(f"Failed to read PDF: {e}")


def _clean_text(text: str) -> str:
    """
    Clean extracted PDF text.

    Args:
        text: Raw extracted text

    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Strip whitespace
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Remove excessive spaces
        line = ' '.join(line.split())

        cleaned_lines.append(line)

    # Join lines with single newline
    cleaned_text = '\n'.join(cleaned_lines)

    # Remove multiple consecutive newlines
    while '\n\n\n' in cleaned_text:
        cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')

    return cleaned_text


def get_pdf_metadata(pdf_path: str) -> dict:
    """
    Extract metadata from PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary with PDF metadata
    """
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        reader = PdfReader(str(pdf_file))

        metadata = {
            'num_pages': len(reader.pages),
            'file_size': pdf_file.stat().st_size,
            'file_name': pdf_file.name,
        }

        # Extract PDF metadata if available
        if reader.metadata:
            if reader.metadata.title:
                metadata['title'] = reader.metadata.title
            if reader.metadata.author:
                metadata['author'] = reader.metadata.author
            if reader.metadata.subject:
                metadata['subject'] = reader.metadata.subject
            if reader.metadata.creator:
                metadata['creator'] = reader.metadata.creator
            if reader.metadata.producer:
                metadata['producer'] = reader.metadata.producer

        return metadata

    except Exception as e:
        raise Exception(f"Failed to read PDF metadata: {e}")


def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Estimate reading time for text.

    Args:
        text: Text to estimate
        words_per_minute: Average reading speed (default: 200)

    Returns:
        Estimated reading time in minutes
    """
    word_count = len(text.split())
    return max(1, word_count // words_per_minute)
