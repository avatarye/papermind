# Claude Integration Module

This module provides integration with Anthropic's Claude API for analyzing academic papers.

## Components

### `client.py` - ClaudeClient

The main API client for interacting with Claude.

**Features:**
- API authentication and request handling
- Context window management (up to 200k tokens)
- Automatic retry logic with exponential backoff
- Token usage tracking
- Support for multiple Claude models

**Example:**
```python
from papermind.claude import ClaudeClient, PromptType

# Initialize client (uses ANTHROPIC_API_KEY env var)
client = ClaudeClient()

# Or provide API key directly
client = ClaudeClient(api_key="sk-ant-...")

# Analyze a paper
result = client.analyze_paper(
    paper_text="Full text of the paper...",
    metadata={
        "title": "Paper Title",
        "authors": ["Author A", "Author B"],
        "year": "2024",
    },
    prompt_type=PromptType.COMPREHENSIVE
)

print(result["analysis"])
```

### `prompts.py` - Prompt Templates

Pre-configured prompt templates for different types of analysis.

**Available Prompt Types:**

1. **COMPREHENSIVE** (default)
   - Complete analysis with all sections
   - Executive summary, methodology, findings, contributions, limitations
   - Best for thorough understanding of a paper

2. **QUICK_SUMMARY**
   - Brief summary with key points
   - One-sentence summary + bullet points
   - Best for quick overviews

3. **TECHNICAL_DEEP_DIVE**
   - Detailed technical and methodological analysis
   - Focus on implementation, algorithms, experiments
   - Best for understanding technical details

4. **LITERATURE_REVIEW**
   - Focus on citations and relationship to existing work
   - Research lineage, key influences, positioning
   - Best for understanding scholarly context

5. **METHODOLOGY**
   - In-depth analysis of research methods
   - Research design, data collection, validity
   - Best for methodological review

6. **CITATION_ANALYSIS**
   - Analysis of references and scholarly influences
   - Key references, citation patterns, influential authors
   - Best for bibliographic analysis

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Claude API key (required)

### Client Parameters

```python
ClaudeClient(
    api_key="sk-ant-...",           # API key (or use env var)
    model="claude-sonnet-4-20250514",  # Model to use
    max_tokens=4096,                # Max tokens in response
    temperature=0.7,                # Sampling temperature (0.0-1.0)
    max_retries=3,                  # Max retry attempts
    retry_delay=1.0                 # Initial retry delay (seconds)
)
```

### Recommended Models

- **claude-sonnet-4-20250514**: Best balance of speed and quality (default)
- **claude-opus-4-20250514**: Highest quality, slower and more expensive
- **claude-haiku-4-20250514**: Fastest and cheapest, good for summaries

## Error Handling

The client automatically handles:

- **Rate Limits**: Retries with exponential backoff
- **Network Errors**: Retries transient connection issues
- **Server Errors (5xx)**: Retries on server-side failures
- **Client Errors (4xx)**: Fails immediately (no retry)

```python
from anthropic import APIError, RateLimitError

try:
    result = client.analyze_paper(...)
except RateLimitError:
    print("Rate limit exceeded, try again later")
except APIError as e:
    print(f"API error: {e}")
```

## Usage Tracking

Track token usage across multiple requests:

```python
# Make several requests
client.analyze_paper(...)
client.analyze_paper(...)

# Get usage statistics
stats = client.get_usage_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Total tokens: {stats['total_tokens']}")

# Reset statistics
client.reset_usage_stats()
```

## Custom Instructions

Add custom instructions to any prompt:

```python
result = client.analyze_paper(
    paper_text=text,
    metadata=metadata,
    prompt_type=PromptType.COMPREHENSIVE,
    custom_instructions="Focus especially on statistical methods used."
)
```

## Token Estimation

Estimate tokens before making API calls:

```python
text = "Your paper content..."
estimated_tokens = client.estimate_tokens(text)
print(f"Estimated tokens: {estimated_tokens}")
```

Note: This is a rough estimate (4 characters ≈ 1 token). For precise counting, use the official tokenizer.

## Best Practices

1. **Use appropriate prompt types**: Don't use COMPREHENSIVE when QUICK_SUMMARY would suffice
2. **Monitor token usage**: Track usage to manage API costs
3. **Cache results**: Store analysis results to avoid repeated API calls for the same paper
4. **Handle errors gracefully**: Implement proper error handling for production use
5. **Set reasonable timeouts**: Some papers may take longer to analyze

## Testing

Run the tests:

```bash
pytest tests/test_claude.py -v
```

## Example

See `examples/claude_demo.py` for a complete working example.

## API Reference

### ClaudeClient

#### Methods

**`analyze_paper(paper_text, metadata, prompt_type, custom_instructions)`**
- Analyze a paper using Claude AI
- Returns: Dict with analysis, model, token counts, finish_reason

**`estimate_tokens(text)`**
- Estimate token count for text
- Returns: int (estimated tokens)

**`get_usage_stats()`**
- Get cumulative usage statistics
- Returns: Dict with request count and token counts

**`reset_usage_stats()`**
- Reset usage statistics to zero

### PromptTemplate

#### Methods

**`build(paper_text, metadata, custom_instructions)`**
- Build a formatted prompt
- Returns: str (complete prompt)

### Functions

**`get_available_prompt_types()`**
- Get all available prompt types with descriptions
- Returns: Dict[str, str]

## Future Enhancements

- [ ] Support for streaming responses
- [ ] Batch processing multiple papers
- [ ] Prompt caching for repeated metadata
- [ ] Support for vision (analyzing figures/tables)
- [ ] Custom prompt templates from config
- [ ] Async support for concurrent requests
