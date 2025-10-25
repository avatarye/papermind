"""Claude AI integration module for paper analysis."""

from .client import ClaudeClient
from .prompts import PromptTemplate, PromptType

__all__ = ["ClaudeClient", "PromptTemplate", "PromptType"]
