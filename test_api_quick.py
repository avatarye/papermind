"""Quick test to verify Claude API integration works."""

import os
import sys
from papermind.claude import ClaudeClient, PromptType

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    # Get API key from environment variable
    import os
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        return

    print(f"API Key found: {api_key[:20]}...")
    print("\nInitializing Claude client...")

    try:
        client = ClaudeClient(api_key=api_key)
        print("✓ Client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return

    # Test with a very short sample paper
    sample_paper = """
    Title: Introduction to Machine Learning

    Abstract: This paper provides an overview of machine learning fundamentals.

    1. Introduction
    Machine learning is a subset of artificial intelligence that focuses on
    building systems that can learn from data.

    2. Key Concepts
    Supervised learning involves training models on labeled data.
    Unsupervised learning finds patterns in unlabeled data.

    3. Conclusion
    Machine learning has wide applications across various domains.
    """

    metadata = {
        "title": "Introduction to Machine Learning",
        "authors": ["Test Author"],
        "year": "2024"
    }

    print("\nSending test request to Claude API...")
    print("(Using QUICK_SUMMARY to minimize token usage)")

    try:
        result = client.analyze_paper(
            paper_text=sample_paper,
            metadata=metadata,
            prompt_type=PromptType.QUICK_SUMMARY
        )

        print("\n" + "="*60)
        print("✓ SUCCESS! Claude API is working!")
        print("="*60)
        print(f"\nModel: {result['model']}")
        print(f"Input tokens: {result['input_tokens']}")
        print(f"Output tokens: {result['output_tokens']}")
        print(f"Finish reason: {result['finish_reason']}")

        print("\n" + "-"*60)
        print("Analysis:")
        print("-"*60)
        print(result['analysis'])
        print("-"*60)

        # Show usage stats
        stats = client.get_usage_stats()
        print(f"\nTotal tokens used: {stats['total_tokens']}")

    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
