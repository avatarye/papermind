"""
Example script demonstrating Claude integration for paper analysis.

This script shows how to use the ClaudeClient to analyze academic papers.
"""

from papermind.claude import ClaudeClient, PromptType

def main():
    """Demo the Claude integration."""

    # Example paper data
    sample_paper_text = """
    Abstract: This paper presents a novel approach to machine learning...

    1. Introduction
    Recent advances in deep learning have shown...

    2. Related Work
    Previous studies have explored...

    3. Methodology
    We propose a new architecture that combines...

    4. Experiments
    We evaluated our approach on three benchmark datasets...

    5. Results
    Our method achieves state-of-the-art performance...

    6. Conclusion
    In this work, we have demonstrated...
    """

    sample_metadata = {
        "title": "A Novel Approach to Deep Learning",
        "authors": ["Alice Smith", "Bob Johnson"],
        "year": "2024",
        "publication": "International Conference on Machine Learning",
        "doi": "10.1234/example.5678",
    }

    # Initialize Claude client
    # API key will be read from ANTHROPIC_API_KEY environment variable
    # or you can pass it directly: ClaudeClient(api_key="your-key-here")
    print("Initializing Claude client...")
    client = ClaudeClient()

    # Example 1: Comprehensive analysis
    print("\n" + "="*60)
    print("Example 1: Comprehensive Analysis")
    print("="*60)

    try:
        result = client.analyze_paper(
            paper_text=sample_paper_text,
            metadata=sample_metadata,
            prompt_type=PromptType.COMPREHENSIVE,
        )

        print(f"\nModel used: {result['model']}")
        print(f"Input tokens: {result['input_tokens']}")
        print(f"Output tokens: {result['output_tokens']}")
        print(f"\nAnalysis:\n{result['analysis']}")

    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Quick summary
    print("\n" + "="*60)
    print("Example 2: Quick Summary")
    print("="*60)

    try:
        result = client.analyze_paper(
            paper_text=sample_paper_text,
            metadata=sample_metadata,
            prompt_type=PromptType.QUICK_SUMMARY,
        )

        print(f"\nAnalysis:\n{result['analysis']}")

    except Exception as e:
        print(f"Error: {e}")

    # Example 3: Technical deep dive
    print("\n" + "="*60)
    print("Example 3: Technical Deep Dive")
    print("="*60)

    try:
        result = client.analyze_paper(
            paper_text=sample_paper_text,
            metadata=sample_metadata,
            prompt_type=PromptType.TECHNICAL_DEEP_DIVE,
            custom_instructions="Pay special attention to the experimental setup.",
        )

        print(f"\nAnalysis:\n{result['analysis']}")

    except Exception as e:
        print(f"Error: {e}")

    # Show usage statistics
    print("\n" + "="*60)
    print("Usage Statistics")
    print("="*60)

    stats = client.get_usage_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Total input tokens: {stats['total_input_tokens']}")
    print(f"Total output tokens: {stats['total_output_tokens']}")
    print(f"Total tokens: {stats['total_tokens']}")


if __name__ == "__main__":
    main()
