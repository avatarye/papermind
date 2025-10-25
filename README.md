# Papermind

AI-powered CLI tool for analyzing academic papers with Claude and Zotero.

## Overview

Papermind integrates Anthropic's Claude AI with your Zotero library to provide intelligent analysis, summaries, and insights from your research papers. It can:

- Read papers directly from your Zotero library
- Extract text from PDFs automatically
- Analyze papers using Claude AI with multiple analysis types
- **Write analysis results back to Zotero as notes**
- Support batch processing of multiple papers
- Generate reports in multiple formats

## Features

✅ **Claude Integration**: Leverage Claude's 200k context window for deep paper analysis
✅ **Zotero Integration**: Direct read/write access to your Zotero database
✅ **Note Writing**: Save AI analysis directly as notes in Zotero entries
✅ **Multiple Analysis Types**: Comprehensive, quick summary, technical deep dive, literature review, methodology, citation analysis
✅ **PDF Extraction**: Automatic text extraction from PDF files
✅ **CLI Interface**: Easy-to-use command-line interface with rich output
✅ **Pipx Compatible**: Can be installed globally as a CLI tool

## Installation

### Using pipx (Recommended for global CLI tool)

```bash
pipx install papermind
```

### Using pip

```bash
pip install papermind
```

### From source (Development)

```bash
git clone https://github.com/yourusername/papermind.git
cd papermind
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install anthropic click pyyaml rich pypdf
```

## Quick Start

### 1. Install Papermind

```bash
# Recommended: Install with pipx
pipx install .

# Or with pip
pip install .
```

### 2. Configure

Run the configuration wizard to set up your Zotero path and Claude API key:

```bash
papermind configure
```

This will prompt you for:
- Zotero data directory path
- Claude API key (or use `ANTHROPIC_API_KEY` environment variable)

Configuration is saved to `~/.papermind/config.json` for future use.

### 3. List Papers

```bash
papermind list --limit 10
```

### 4. Analyze a Paper

**Easy Way (Interactive Selection):**

```bash
papermind select
```

This will guide you through:
1. Selecting a collection
2. Selecting a paper
3. Selecting analysis type
4. Running the analysis

**Direct Way (If you know the item ID):**

```bash
# Get paper ID from the list command, then analyze it
papermind analyze 12345
```

Both methods will:
- Extract text from the PDF
- Send it to Claude for analysis
- Display the analysis
- **Save the analysis as a note in the Zotero entry**

## Commands

See the full documentation in [USAGE.md](USAGE.md) for detailed command reference.

### Quick Reference

```bash
# Configure
papermind configure                    # Interactive setup
papermind configure --show             # Show current config
papermind configure --reset            # Reset configuration

# Interactive mode (easiest!)
papermind select                       # Guided selection of collection -> paper -> analysis type

# List papers
papermind list
papermind list --collection "Machine Learning"
papermind list --tag important

# Show paper details
papermind show 12345

# Analyze papers (direct)
papermind analyze 12345
papermind analyze 12345 --type quick_summary
papermind analyze 12345 --type technical_deep_dive --output report.md

# Batch processing
papermind batch --collection "To Read" --type quick_summary
```

## Requirements

- Python ≥3.10
- Claude API key (get one at https://console.anthropic.com)
- Zotero with papers and PDFs

## Documentation

- [Full Usage Guide](USAGE.md) - Detailed command reference
- [Claude Integration](papermind/claude/README.md) - How the AI backend works
- [Development Guide](PLAN.md) - Architecture and development roadmap

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.

## Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/)
- Integrates with [Zotero](https://www.zotero.org/)
- Uses [Click](https://click.palletsprojects.com/) for CLI
- Uses [Rich](https://rich.readthedocs.io/) for beautiful terminal output
