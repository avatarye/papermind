# Papermind Usage Guide

Papermind is an AI-powered CLI tool for analyzing academic papers with Claude and Zotero.

## Installation

### Install with pipx (Recommended)

pipx is the recommended way to install Python CLI tools. It installs the tool in an isolated environment.

```bash
# Install pipx if you don't have it
python -m pip install --user pipx
python -m pipx ensurepath

# Install Papermind
pipx install .
```

### Install with pip

```bash
# Install from source
pip install .

# Or install in development mode
pip install -e .
```

### Verify Installation

```bash
papermind --version
papermind --help
```

## Configuration

Before using Papermind, you need to configure your Zotero path and Claude API key.

### Initial Configuration

Run the interactive configuration wizard:

```bash
papermind configure
```

This will prompt you to enter:
1. **Zotero data directory path** - The location where Zotero stores its database
   - Windows: Usually `C:\Users\YourName\Zotero`
   - Mac: Usually `~/Zotero`
   - Linux: Usually `~/Zotero` or `~/.zotero`

2. **Claude API key** - Your Anthropic API key (starts with `sk-ant-`)
   - Get one at https://console.anthropic.com/

### Quick Configuration

You can also configure directly with options:

```bash
papermind configure --zotero-path /path/to/zotero
papermind configure --api-key sk-ant-...
```

### View Current Configuration

```bash
papermind configure --show
```

### Reset Configuration

```bash
papermind configure --reset
```

### Configure Obsidian Vault (Optional)

If you want to use Obsidian sync features, configure your vault path:

```bash
papermind configure --obsidian-vault /path/to/vault
```

Or use interactive mode and it will prompt you to configure it.

## Configuration Storage

Configuration is stored in:
- **Windows**: `%USERPROFILE%\.papermind\config.json`
- **Mac/Linux**: `~/.papermind/config.json`

The Claude API key can also be set via the `ANTHROPIC_API_KEY` environment variable.

## Commands

### Interactive Selection (Recommended)

The easiest way to use Papermind is with interactive mode:

```bash
papermind select
```

This command guides you through a step-by-step process:

1. **Select a Collection** - Choose from your Zotero collections or "All Papers"
2. **Select a Paper** - Browse papers in the collection with titles, authors, and years
3. **Select Analysis Type** - Choose from 6 different analysis types
4. **Run Analysis** - Automatically analyzes and saves to Zotero

**Example Session:**

```
$ papermind select

Welcome to Papermind Interactive Mode!

Let's analyze a paper from your Zotero library.

Collections

      Number  Item
      1       All Papers
      2       Machine Learning
      3       Neural Networks
      4       To Read

Select collections [1]: 2

Loading papers from 'Machine Learning'...

Papers

      Number  Item
      1       Attention Is All You Need - Vaswani et al. (2017)
      2       BERT: Pre-training of Deep Bidirectional Transformers - Devlin et al. (2018)
      3       GPT-4 Technical Report - OpenAI (2023)

Select papers [1]: 1

Analysis Type

      Number  Item
      1       Quick Summary                   - Brief overview and key takeaways
      2       Comprehensive Analysis          - Full detailed analysis
      3       Technical Deep Dive             - In-depth technical details
      4       Literature Review               - Context within existing research
      5       Methodology Analysis            - Research methods and design
      6       Citation Analysis               - Citations and related work

Select analysis type [1]: 2

[Analysis runs...]
```

**Options:**

```bash
# Don't save to Zotero
papermind select --no-save-to-zotero

# Save to a file
papermind select --output analysis.txt
```

### List Papers

List papers in your Zotero library:

```bash
# List recent papers
papermind list

# Filter by collection
papermind list --collection "Machine Learning"

# Filter by tags
papermind list --tag important --tag unread

# Limit results
papermind list --limit 50
```

### Show Paper Details

Display detailed information about a specific paper:

```bash
papermind show 12345
```

The item ID can be found using the `list` command.

### Analyze Paper

Analyze a paper with Claude AI:

```bash
# Comprehensive analysis (default)
papermind analyze 12345

# Quick summary
papermind analyze 12345 --type quick_summary

# Technical deep dive
papermind analyze 12345 --type technical_deep_dive

# Other analysis types
papermind analyze 12345 --type literature_review
papermind analyze 12345 --type methodology
papermind analyze 12345 --type citation_analysis
```

#### Save Analysis

```bash
# Save to Zotero as a note (default)
papermind analyze 12345

# Don't save to Zotero
papermind analyze 12345 --no-save-to-zotero

# Save to a file
papermind analyze 12345 --output analysis.txt
```

### Batch Processing

Process multiple papers at once:

```bash
# Process all papers in a collection
papermind batch --collection "To Read" --type quick_summary

# Process papers with specific tags
papermind batch --tag important --limit 10

# Process all papers (limited to first 20)
papermind batch --limit 20
```

## Analysis Types

Papermind supports several types of analysis:

- **comprehensive** - Full detailed analysis covering all aspects (default for `analyze`)
- **quick_summary** - Brief overview and key takeaways (default for `batch`)
- **technical_deep_dive** - In-depth technical details and implementation
- **literature_review** - Context within existing research
- **methodology** - Focus on research methods and experimental design
- **citation_analysis** - Analysis of citations and related work

## Obsidian Sync

Papermind includes powerful bidirectional sync between Zotero and Obsidian, allowing you to manage your research library in Obsidian with dynamic Dataview queries.

### Prerequisites

1. **Obsidian vault** - Create or use an existing Obsidian vault
2. **Dataview plugin** - Install the Dataview community plugin in Obsidian
   - Settings → Community plugins → Browse → Search "Dataview" → Install → Enable

### Sync Zotero to Obsidian

Sync your entire Zotero library to Obsidian:

```bash
# Sync all papers and collections
papermind sync

# Preview what will be synced (dry run)
papermind sync --dry-run

# Sync to a specific vault
papermind sync --vault-path /path/to/vault
```

#### What Gets Synced

The sync creates the following structure in your Obsidian vault:

```
Obsidian Vault/
└── Zotero/
    ├── repo/                    # All papers
    │   ├── PAPERKEY1/
    │   │   ├── paper.md        # Metadata with frontmatter
    │   │   ├── Paper.pdf       # PDF attachment
    │   │   ├── file.html       # Other attachments
    │   │   └── Note.md         # Zotero notes
    │   └── PAPERKEY2/
    │       └── ...
    └── collections/             # Collection views
        ├── Machine Learning.md
        └── Neural Networks.md
```

#### Paper Metadata

Each `paper.md` file contains:

```yaml
---
title: "Paper Title"
authors:
  - "Author 1"
  - "Author 2"
collections:
  - "Machine Learning"
  - "AI"
year: 2024
doi: "10.1234/..."
url: "https://..."
tags:
  - "tag1"
  - "tag2"
zotero_id: 12345
zotero_key: "ABC123"
---

## Abstract

[Paper abstract here]

## Attachments

- [[Paper.pdf]]
- [[file.html]]

## Notes

*Add your notes here. Use Claude CLI to generate reports.*
```

#### Collection Views

Each collection file uses Dataview queries to dynamically list papers:

```markdown
# Machine Learning

​```dataview
TABLE
  file.link as Paper,
  title as Title
FROM "Zotero/repo"
WHERE contains(collections, "Machine Learning")
SORT title ASC
​```

*20 papers in this collection*
```

### Sync Notes from Obsidian to Zotero

After creating analysis reports or notes in Obsidian, sync them back to Zotero:

```bash
# Sync all new notes to Zotero
papermind sync-notes

# Preview what will be synced
papermind sync-notes --dry-run

# Overwrite existing notes in Zotero
papermind sync-notes --overwrite
```

#### How It Works

1. Creates reports in Obsidian (e.g., using Claude CLI)
2. Saves them as `.md` files in paper directories
3. Runs `papermind sync-notes` to sync back to Zotero
4. Notes appear in Zotero items

**Note Handling:**
- Only `.md` files (excluding `paper.md`) are synced as notes
- Notes are identified by filename
- Duplicate detection prevents re-syncing unchanged notes
- Use `--overwrite` to update existing notes

### Obsidian + Claude CLI Workflow

Recommended workflow for using Claude CLI with Papermind:

```bash
# 1. Sync Zotero library to Obsidian
papermind sync

# 2. Navigate to a paper directory in your vault
cd ~/ObsidianVault/Zotero/repo/ABC123/

# 3. Use Claude CLI to generate analysis
claude "analyze this paper and create a comprehensive summary" > analysis.md

# 4. Sync the analysis back to Zotero
papermind sync-notes

# 5. Open Zotero to see the analysis as a note!
```

### Use Cases

**Research Organization:**
- Browse papers in Obsidian with Dataview queries
- Click paper links to view metadata and attachments
- Use collections to organize by topic

**Literature Review:**
- Use Dataview to filter papers by year, author, or tags
- Create custom queries for your research questions
- Link between papers using wiki-links

**Note-Taking:**
- Add notes directly in `paper.md` files
- Create separate `.md` files for detailed analysis
- Sync notes back to Zotero for backup

**AI-Assisted Analysis:**
- Use Claude CLI to generate reports
- Save reports as markdown files
- Sync to Zotero as permanent notes

## Examples

### Getting Started Workflow

**Easy Mode (Recommended):**

```bash
# 1. Install
pipx install .

# 2. Configure
papermind configure

# 3. Use interactive mode
papermind select

# 4. Check the note in Zotero!
```

**Advanced Mode:**

```bash
# 1. Install
pipx install .

# 2. Configure
papermind configure

# 3. List your papers
papermind list

# 4. Analyze a paper by ID
papermind analyze 12345 --type quick_summary

# 5. Check the note in Zotero
```

### Research Workflow

**Interactive Approach:**

```bash
# Use interactive mode for easy selection
papermind select

# Select "To Read" collection
# Pick a paper
# Choose "Quick Summary" for initial review
# Repeat as needed
```

**Command-Line Approach:**

```bash
# List papers in your "To Read" collection
papermind list --collection "To Read" --limit 10

# Get a quick summary of interesting papers
papermind analyze 98765 --type quick_summary

# Do a deep dive on the most relevant one
papermind analyze 98765 --type technical_deep_dive --output deep_analysis.txt

# Process remaining papers in batch
papermind batch --collection "To Read" --type quick_summary --limit 5
```

### Literature Review Workflow

**Interactive Approach:**

```bash
# Use interactive mode and select your topic collection
papermind select
# Select collection (e.g., "Neural Networks")
# Select first paper
# Choose "Literature Review" analysis type
# Repeat for other papers
```

**Command-Line Approach:**

```bash
# Find papers on a specific topic (use Zotero's interface or tags)
papermind list --tag "neural-networks"

# Analyze each for literature context
papermind analyze 11111 --type literature_review
papermind analyze 22222 --type literature_review
papermind analyze 33333 --type literature_review

# All analyses are saved as notes in Zotero for easy reference
```

## Troubleshooting

### "Papermind is not configured yet"

Run `papermind configure` to set up your Zotero path and API key.

### "Zotero database not found"

Make sure the Zotero path points to your Zotero data directory (the folder containing `zotero.sqlite`).

### "No PDF attached to this item"

The paper must have an attached PDF file. Add PDFs to your Zotero items first.

### API Key Issues

- Check that your API key is valid and starts with `sk-ant-`
- You can set it via environment variable: `export ANTHROPIC_API_KEY=sk-ant-...`
- Or configure it: `papermind configure --api-key sk-ant-...`

### Obsidian Sync Issues

**"No Zotero/repo directory found in vault"**

Run `papermind sync` first to create the directory structure.

**Dataview queries not showing papers**

1. Make sure the Dataview plugin is installed and enabled
2. Switch to Reading Mode (Cmd+E) to see rendered tables
3. Check that papers have the collection in their frontmatter

**Notes not visible in Obsidian**

- Only `.md` files are visible in Obsidian
- Check that notes were synced with `papermind sync`
- Zotero notes are stripped of HTML and saved as `.md` files

**Sync conflicts with Dropbox/iCloud**

The sync is designed to work with cloud storage like Dropbox. Each sync recreates the structure, so conflicts should be minimal.

## Tips

1. **Use Interactive Mode**: The `papermind select` command is the easiest way to get started
2. **Start Small**: Use `--type quick_summary` first to save tokens
3. **Batch Processing**: Process multiple papers with `batch` command
4. **Save Analyses**: All analyses are saved as notes in Zotero by default
5. **Export**: Use `--output` to save analyses to files
6. **Organization**: Use Zotero collections and tags to organize papers before analysis
7. **Cancel Selection**: Type 'q', 'quit', 'exit', or 'cancel' to exit interactive mode

## Getting Help

```bash
# General help
papermind --help

# Command-specific help
papermind configure --help
papermind select --help
papermind list --help
papermind show --help
papermind analyze --help
papermind batch --help
papermind sync --help
papermind sync-notes --help
```
