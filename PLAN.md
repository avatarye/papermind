# Papermind - Project Plan

## Overview
Papermind is an AI-powered CLI tool that integrates Claude with Zotero to help researchers analyze, summarize, and generate reports from their academic paper collections.

## Goals
- Provide seamless access to local Zotero library via CLI
- Leverage Claude AI to generate intelligent summaries and insights
- Support batch processing of multiple papers
- Generate structured reports in multiple formats
- Enable interactive exploration of papers

## Architecture

### Components

```
papermind/
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # User documentation
├── PLAN.md                 # This file
├── papermind/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point and commands
│   ├── zotero/
│   │   ├── __init__.py
│   │   ├── database.py     # SQLite database queries
│   │   └── models.py       # Data models for Zotero items
│   ├── pdf/
│   │   ├── __init__.py
│   │   └── parser.py       # PDF text extraction
│   ├── claude/
│   │   ├── __init__.py
│   │   ├── client.py       # Claude API integration
│   │   └── prompts.py      # Prompt templates
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── generator.py    # Report generation
│   │   └── templates/      # Report templates
│   ├── config.py           # Configuration management
│   └── utils.py            # Utility functions
└── tests/
    ├── __init__.py
    ├── test_zotero.py
    ├── test_pdf.py
    └── test_cli.py
```

## Technical Stack

### Core Dependencies
- **CLI Framework**: `click` or `typer` - for building the command-line interface
- **AI Integration**: `anthropic` - official Claude API SDK
- **PDF Processing**: `pypdf` or `pdfplumber` - for extracting text from PDFs
- **Database**: `sqlite3` (built-in) - for querying Zotero database
- **Configuration**: `pyyaml` - for config file management
- **UI/UX**: `rich` - for beautiful terminal output with progress bars, tables, etc.

### Development Dependencies
- **Testing**: `pytest`
- **Linting**: `ruff` or `flake8`
- **Type Checking**: `mypy`
- **Formatting**: `black`

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [x] Project setup and repository initialization
- [ ] Basic CLI structure with Click/Typer
- [ ] Configuration management (Zotero path, API keys)
- [ ] Setup command: `papermind setup`
- [ ] Basic project documentation

**Deliverables**:
- Working CLI skeleton
- Configuration file structure
- README with installation instructions

### Phase 2: Zotero Integration (Week 2)
- [ ] Zotero SQLite database reader
- [ ] Query interface for items, collections, tags
- [ ] Data models for papers, authors, metadata
- [ ] List command: `papermind list`
- [ ] Search/filter functionality

**Deliverables**:
- Zotero database module
- Commands to browse Zotero library
- Unit tests for database queries

### Phase 3: PDF Processing (Week 3)
- [ ] PDF text extraction module
- [ ] Handle different PDF formats and layouts
- [ ] Extract tables and figures (basic)
- [ ] Text preprocessing and cleaning
- [ ] Caching mechanism for extracted text

**Deliverables**:
- PDF parser module
- Text extraction with quality validation
- Tests for various PDF formats

### Phase 4: Claude Integration (Week 4)
- [ ] Claude API client wrapper
- [ ] Prompt engineering for paper analysis
- [ ] Context window management (200k tokens)
- [ ] Structured output parsing
- [ ] Error handling and retries

**Deliverables**:
- Claude integration module
- Prompt templates library
- API usage tracking

### Phase 5: Report Generation (Week 5)
- [ ] Report generator with templates
- [ ] Multiple output formats (Markdown, JSON, HTML)
- [ ] Report command: `papermind report <item-id>`
- [ ] Customizable report sections
- [ ] Save and organize reports

**Deliverables**:
- Report generation module
- Default report templates
- Output format converters

### Phase 6: Batch Processing (Week 6)
- [ ] Batch processing for multiple papers
- [ ] Progress tracking with rich progress bars
- [ ] Parallel processing (optional)
- [ ] Batch command: `papermind batch`
- [ ] Resume failed batches

**Deliverables**:
- Batch processing functionality
- Progress reporting
- Error recovery mechanisms

### Phase 7: Advanced Features (Week 7-8)
- [ ] Interactive mode: `papermind interactive <item-id>`
- [ ] Comparative analysis across papers
- [ ] Citation network analysis
- [ ] Export to various formats
- [ ] Integration with note-taking apps (optional)

**Deliverables**:
- Interactive chat mode
- Advanced analysis features
- Extended documentation

### Phase 8: Polish & Release (Week 9)
- [ ] Comprehensive testing
- [ ] Documentation finalization
- [ ] Usage examples and tutorials
- [ ] Performance optimization
- [ ] Package for PyPI
- [ ] Release v1.0.0

**Deliverables**:
- Production-ready package
- Complete documentation
- PyPI package

## CLI Commands Design

### Setup
```bash
# Initial setup wizard
papermind setup

# Configure Zotero path
papermind config set zotero-path ~/Zotero

# Configure Claude API key
papermind config set api-key sk-ant-...

# View current configuration
papermind config show
```

### Browse & Search
```bash
# List all papers
papermind list

# List with filters
papermind list --collection "Machine Learning"
papermind list --tag "important" --tag "unread"
papermind list --author "Smith"
papermind list --year 2024

# Search papers
papermind search "neural networks"

# Show paper details
papermind show <item-id>
```

### Report Generation
```bash
# Generate report for a single paper
papermind report <item-id>

# Specify output file and format
papermind report <item-id> --output report.md
papermind report <item-id> --output report.json --format json

# Custom report sections
papermind report <item-id> --sections summary,methodology,findings

# Batch processing
papermind batch --collection "To Read"
papermind batch --tag "review" --output-dir ./reports
papermind batch --all --max 10
```

### Interactive Mode
```bash
# Chat with Claude about a paper
papermind interactive <item-id>

# Example interactive session:
# > What are the main contributions?
# > Explain the methodology in simple terms
# > Compare this with paper XYZ
# > exit
```

### Utilities
```bash
# Version and info
papermind --version
papermind info

# Clear cache
papermind cache clear

# Export data
papermind export --format csv --output papers.csv
```

## Report Structure

### Default Report Sections
1. **Metadata**
   - Title, Authors, Year, Journal/Conference
   - DOI, URL, Tags
   - Zotero item ID

2. **Executive Summary**
   - 2-3 paragraph overview
   - Key takeaways

3. **Research Context**
   - Problem statement
   - Research questions/objectives
   - Background and motivation

4. **Methodology**
   - Research design
   - Data collection
   - Analysis methods

5. **Key Findings**
   - Main results
   - Important observations
   - Tables and figures (referenced)

6. **Contributions**
   - Novel contributions
   - Significance to the field

7. **Limitations**
   - Study limitations
   - Future work suggestions

8. **Citations & References**
   - Key papers cited
   - Relevant related work

9. **Personal Notes** (optional)
   - Custom annotations
   - Reading notes from Zotero

## Configuration

### Config File Location
- Linux/Mac: `~/.config/papermind/config.yaml`
- Windows: `%APPDATA%\papermind\config.yaml`

### Config File Structure
```yaml
zotero:
  data_directory: /home/user/Zotero
  database: zotero.sqlite
  storage: storage

claude:
  api_key: sk-ant-...
  model: claude-sonnet-4-20250514
  max_tokens: 4096
  temperature: 0.7

reports:
  output_directory: ~/papermind-reports
  default_format: markdown
  sections:
    - metadata
    - summary
    - methodology
    - findings
    - contributions

cache:
  enabled: true
  directory: ~/.cache/papermind
  ttl: 86400  # 24 hours

ui:
  theme: auto
  show_progress: true
  verbose: false
```

## Data Flow

1. **User invokes command**: `papermind report 12345`
2. **CLI parses command**: Extract item ID and options
3. **Query Zotero DB**: Get paper metadata and file path
4. **Extract PDF text**: Parse PDF and extract text content
5. **Prepare Claude prompt**: Build structured prompt with paper content
6. **Call Claude API**: Send request and get structured response
7. **Generate report**: Format response into desired output format
8. **Save report**: Write to file system
9. **Display result**: Show summary and file path to user

## Prompt Engineering Strategy

### Base Prompt Template
```
You are an expert research assistant analyzing an academic paper.

Paper Information:
- Title: {title}
- Authors: {authors}
- Year: {year}
- Publication: {publication}

Full Text:
{paper_text}

Generate a comprehensive analysis with the following sections:
1. Executive Summary (2-3 paragraphs)
2. Research Context and Motivation
3. Methodology
4. Key Findings and Results
5. Contributions to the Field
6. Limitations and Future Work
7. Key References

Provide your analysis in structured markdown format.
```

### Specialized Prompts
- **Quick Summary**: Shorter, focused on key points
- **Technical Deep Dive**: Detailed methodology analysis
- **Literature Review**: Focus on context and related work
- **Citation Analysis**: Extract and analyze references
- **Comparative Analysis**: Compare multiple papers

## Error Handling

### Common Scenarios
- Zotero database not found
- PDF file missing or corrupted
- Claude API rate limits
- Network errors
- Invalid item IDs
- Insufficient API credits

### Strategies
- Graceful degradation
- Helpful error messages
- Retry logic with exponential backoff
- Cache results to minimize API calls
- Validate inputs before processing

## Security & Privacy

### API Key Management
- Store API keys securely in config file
- Never log or display API keys
- Support environment variables
- Clear warnings about data sent to Claude API

### Data Handling
- Papers are sent to Claude API (user should be aware)
- Option to process sensitive papers locally (future)
- No data stored on external servers (except Claude API processing)
- Cache can be disabled for sensitive content

## Testing Strategy

### Unit Tests
- Zotero database queries
- PDF text extraction
- Report generation
- CLI command parsing

### Integration Tests
- End-to-end workflows
- API integration (with mocking)
- File I/O operations

### Manual Testing
- Various PDF formats
- Different Zotero database versions
- Edge cases (empty library, missing files)

## Documentation

### README.md
- Quick start guide
- Installation instructions
- Basic usage examples
- Configuration overview

### User Guide
- Detailed command reference
- Advanced usage patterns
- Troubleshooting
- FAQ

### Developer Guide
- Architecture overview
- Contribution guidelines
- Code style and standards
- How to extend functionality

## Performance Considerations

### Optimization Targets
- PDF parsing speed
- API call efficiency (batching)
- Database query optimization
- Caching strategy

### Metrics
- Time to generate single report: < 30 seconds
- Batch processing: ~10 papers per minute (API dependent)
- Memory usage: < 500MB for typical operations
- Startup time: < 2 seconds

## Future Enhancements (v2.0+)

### Potential Features
- [ ] Web interface (FastAPI/Flask)
- [ ] Integration with other reference managers (Mendeley, EndNote)
- [ ] Advanced citation network visualization
- [ ] Automatic literature review generation
- [ ] Integration with writing tools (Obsidian, Notion)
- [ ] Collaborative features (shared reports)
- [ ] Custom AI models/fine-tuning
- [ ] Voice interface for interactive mode
- [ ] Mobile app companion
- [ ] Cloud sync for reports

### Community Feedback
- Gather user feedback after v1.0 release
- Prioritize features based on demand
- Consider plugin architecture for extensibility

## Release Strategy

### Version 0.1.0 (Alpha)
- Basic CLI structure
- Zotero database reading
- Simple report generation

### Version 0.5.0 (Beta)
- Full feature set
- Batch processing
- Multiple output formats

### Version 1.0.0 (Stable)
- Production-ready
- Complete documentation
- Published on PyPI
- Comprehensive testing

### Maintenance
- Regular updates for Claude API changes
- Bug fixes and performance improvements
- Community contributions welcome

## Success Metrics

### Adoption
- GitHub stars: 100+ in first 3 months
- PyPI downloads: 500+ per month
- Active users: 50+ researchers

### Quality
- Test coverage: >80%
- Zero critical bugs in stable release
- Positive community feedback
- Active maintenance and updates

## Resources

### Documentation
- Claude API docs: https://docs.anthropic.com
- Zotero database schema: https://www.zotero.org/support/dev/client_coding/direct_sqlite_database_access
- Click documentation: https://click.palletsprojects.com

### Community
- GitHub Discussions for Q&A
- Issue tracking for bugs and features
- Contributing guidelines for PRs

## Timeline Summary

- **Week 1-2**: Foundation & Zotero integration
- **Week 3-4**: PDF processing & Claude integration
- **Week 5-6**: Report generation & batch processing
- **Week 7-8**: Advanced features
- **Week 9**: Polish, testing, and v1.0.0 release

**Target Launch**: 9 weeks from project start

---

*Last Updated*: 2025-10-23  
*Status*: Planning Phase  
*Next Steps*: Begin Phase 1 implementation
