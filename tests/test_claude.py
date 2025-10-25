"""Tests for Claude integration module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from anthropic import APIError, RateLimitError, APIConnectionError

from papermind.claude.client import ClaudeClient
from papermind.claude.prompts import PromptTemplate, PromptType, get_available_prompt_types


class TestClaudeClient:
    """Test cases for ClaudeClient."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = ClaudeClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == "claude-sonnet-4-20250514"
        assert client.max_tokens == 4096
        assert client.temperature == 0.7

    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}):
            client = ClaudeClient()
            assert client.api_key == "env-key"

    def test_init_without_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key must be provided"):
                ClaudeClient()

    def test_custom_parameters(self):
        """Test initialization with custom parameters."""
        client = ClaudeClient(
            api_key="test-key",
            model="claude-opus-4-20250514",
            max_tokens=8192,
            temperature=0.5,
            max_retries=5,
            retry_delay=2.0,
        )
        assert client.model == "claude-opus-4-20250514"
        assert client.max_tokens == 8192
        assert client.temperature == 0.5
        assert client.max_retries == 5
        assert client.retry_delay == 2.0

    @patch("papermind.claude.client.Anthropic")
    def test_analyze_paper_success(self, mock_anthropic):
        """Test successful paper analysis."""
        # Setup mock response
        mock_content = Mock()
        mock_content.text = "This is the analysis result"

        mock_usage = Mock()
        mock_usage.input_tokens = 1000
        mock_usage.output_tokens = 500

        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.usage = mock_usage
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        mock_client_instance = Mock()
        mock_client_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client_instance

        # Test
        client = ClaudeClient(api_key="test-key")
        result = client.analyze_paper(
            paper_text="Sample paper text",
            metadata={"title": "Test Paper", "authors": "Author A"},
        )

        # Assertions
        assert result["analysis"] == "This is the analysis result"
        assert result["model"] == "claude-sonnet-4-20250514"
        assert result["input_tokens"] == 1000
        assert result["output_tokens"] == 500
        assert result["finish_reason"] == "end_turn"
        assert client.total_requests == 1
        assert client.total_input_tokens == 1000
        assert client.total_output_tokens == 500

    @patch("papermind.claude.client.Anthropic")
    def test_analyze_paper_empty_text(self, mock_anthropic):
        """Test analysis with empty paper text."""
        client = ClaudeClient(api_key="test-key")

        with pytest.raises(ValueError, match="Paper text cannot be empty"):
            client.analyze_paper(paper_text="", metadata={})

        with pytest.raises(ValueError, match="Paper text cannot be empty"):
            client.analyze_paper(paper_text="   ", metadata={})

    @patch("papermind.claude.client.Anthropic")
    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_retry_on_rate_limit(self, mock_sleep, mock_anthropic):
        """Test retry logic on rate limit error."""
        mock_content = Mock()
        mock_content.text = "Success after retry"

        mock_usage = Mock()
        mock_usage.input_tokens = 1000
        mock_usage.output_tokens = 500

        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.usage = mock_usage
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        mock_client_instance = Mock()
        # Fail twice, then succeed
        mock_client_instance.messages.create.side_effect = [
            RateLimitError("Rate limited"),
            RateLimitError("Rate limited"),
            mock_response,
        ]
        mock_anthropic.return_value = mock_client_instance

        client = ClaudeClient(api_key="test-key")
        result = client.analyze_paper(
            paper_text="Sample text",
            metadata={},
        )

        assert result["analysis"] == "Success after retry"
        assert mock_client_instance.messages.create.call_count == 3
        assert mock_sleep.call_count == 2  # Slept twice before success

    @patch("papermind.claude.client.Anthropic")
    @patch("time.sleep")
    def test_max_retries_exceeded(self, mock_sleep, mock_anthropic):
        """Test that max retries is respected."""
        mock_client_instance = Mock()
        mock_client_instance.messages.create.side_effect = RateLimitError("Rate limited")
        mock_anthropic.return_value = mock_client_instance

        client = ClaudeClient(api_key="test-key", max_retries=3)

        with pytest.raises(RateLimitError):
            client.analyze_paper(paper_text="Sample text", metadata={})

        # Should try 3 times total
        assert mock_client_instance.messages.create.call_count == 3

    @patch("papermind.claude.client.Anthropic")
    def test_no_retry_on_client_error(self, mock_anthropic):
        """Test that 4xx errors are not retried."""
        mock_error = APIError("Bad request")
        mock_error.status_code = 400

        mock_client_instance = Mock()
        mock_client_instance.messages.create.side_effect = mock_error
        mock_anthropic.return_value = mock_client_instance

        client = ClaudeClient(api_key="test-key")

        with pytest.raises(APIError):
            client.analyze_paper(paper_text="Sample text", metadata={})

        # Should only try once (no retry on 4xx)
        assert mock_client_instance.messages.create.call_count == 1

    def test_estimate_tokens(self):
        """Test token estimation."""
        client = ClaudeClient(api_key="test-key")

        # Rough estimate: 4 chars = 1 token
        assert client.estimate_tokens("test") == 1
        assert client.estimate_tokens("a" * 100) == 25
        assert client.estimate_tokens("") == 0

    @patch("papermind.claude.client.Anthropic")
    def test_usage_stats(self, mock_anthropic):
        """Test usage statistics tracking."""
        mock_content = Mock()
        mock_content.text = "Analysis"

        mock_usage = Mock()
        mock_usage.input_tokens = 1000
        mock_usage.output_tokens = 500

        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.usage = mock_usage
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        mock_client_instance = Mock()
        mock_client_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client_instance

        client = ClaudeClient(api_key="test-key")

        # Make two requests
        client.analyze_paper(paper_text="Test 1", metadata={})
        client.analyze_paper(paper_text="Test 2", metadata={})

        stats = client.get_usage_stats()
        assert stats["total_requests"] == 2
        assert stats["total_input_tokens"] == 2000
        assert stats["total_output_tokens"] == 1000
        assert stats["total_tokens"] == 3000

        # Reset stats
        client.reset_usage_stats()
        stats = client.get_usage_stats()
        assert stats["total_requests"] == 0
        assert stats["total_input_tokens"] == 0
        assert stats["total_output_tokens"] == 0


class TestPromptTemplate:
    """Test cases for PromptTemplate."""

    def test_comprehensive_prompt(self):
        """Test comprehensive prompt generation."""
        template = PromptTemplate(PromptType.COMPREHENSIVE)
        prompt = template.build(
            paper_text="This is the paper content",
            metadata={
                "title": "Test Paper",
                "authors": ["Author A", "Author B"],
                "year": "2024",
            },
        )

        assert "Test Paper" in prompt
        assert "Author A, Author B" in prompt
        assert "2024" in prompt
        assert "This is the paper content" in prompt
        assert "Executive Summary" in prompt
        assert "Methodology" in prompt

    def test_quick_summary_prompt(self):
        """Test quick summary prompt."""
        template = PromptTemplate(PromptType.QUICK_SUMMARY)
        prompt = template.build(
            paper_text="Paper content",
            metadata={"title": "Quick Test"},
        )

        assert "Quick Test" in prompt
        assert "Paper content" in prompt
        assert "In One Sentence" in prompt
        assert "Key Points" in prompt

    def test_technical_prompt(self):
        """Test technical deep dive prompt."""
        template = PromptTemplate(PromptType.TECHNICAL_DEEP_DIVE)
        prompt = template.build(
            paper_text="Technical content",
            metadata={"title": "Technical Paper"},
        )

        assert "Technical Paper" in prompt
        assert "Technical Approach" in prompt
        assert "Experimental Design" in prompt
        assert "Mathematical/Theoretical Foundation" in prompt

    def test_custom_instructions(self):
        """Test prompt with custom instructions."""
        template = PromptTemplate(PromptType.COMPREHENSIVE)
        custom = "Focus especially on the results section."

        prompt = template.build(
            paper_text="Content",
            metadata={"title": "Paper"},
            custom_instructions=custom,
        )

        assert custom in prompt

    def test_metadata_formatting(self):
        """Test metadata formatting."""
        template = PromptTemplate(PromptType.COMPREHENSIVE)

        metadata = {
            "title": "Example Paper",
            "authors": ["Alice", "Bob", "Charlie"],
            "year": "2024",
            "publication": "Nature",
            "doi": "10.1234/example",
            "url": "https://example.com",
        }

        prompt = template.build(paper_text="Content", metadata=metadata)

        assert "- Title: Example Paper" in prompt
        assert "- Authors: Alice, Bob, Charlie" in prompt
        assert "- Year: 2024" in prompt
        assert "- Publication: Nature" in prompt
        assert "- DOI: 10.1234/example" in prompt
        assert "- URL: https://example.com" in prompt

    def test_empty_metadata(self):
        """Test handling of empty metadata."""
        template = PromptTemplate(PromptType.COMPREHENSIVE)
        prompt = template.build(paper_text="Content", metadata={})

        assert "No metadata available" in prompt

    def test_all_prompt_types(self):
        """Test that all prompt types can be generated."""
        paper_text = "Sample paper content"
        metadata = {"title": "Test"}

        for prompt_type in PromptType:
            template = PromptTemplate(prompt_type)
            prompt = template.build(paper_text=paper_text, metadata=metadata)

            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert paper_text in prompt


def test_get_available_prompt_types():
    """Test getting available prompt types."""
    prompt_types = get_available_prompt_types()

    assert isinstance(prompt_types, dict)
    assert "comprehensive" in prompt_types
    assert "quick_summary" in prompt_types
    assert "technical_deep_dive" in prompt_types
    assert len(prompt_types) == 6

    # Check descriptions exist
    for description in prompt_types.values():
        assert isinstance(description, str)
        assert len(description) > 0
