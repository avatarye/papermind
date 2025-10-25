"""Prompt templates for Claude API paper analysis."""

from enum import Enum
from typing import Dict, Any, Optional


class PromptType(Enum):
    """Types of analysis prompts available."""

    COMPREHENSIVE = "comprehensive"
    QUICK_SUMMARY = "quick_summary"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    LITERATURE_REVIEW = "literature_review"
    METHODOLOGY = "methodology"
    CITATION_ANALYSIS = "citation_analysis"


class PromptTemplate:
    """
    Template builder for Claude API prompts.

    Generates structured prompts based on prompt type and paper data.
    """

    def __init__(self, prompt_type: PromptType = PromptType.COMPREHENSIVE):
        """
        Initialize prompt template.

        Args:
            prompt_type: Type of analysis to perform
        """
        self.prompt_type = prompt_type

    def build(
        self,
        paper_text: str,
        metadata: Dict[str, Any],
        custom_instructions: Optional[str] = None,
    ) -> str:
        """
        Build the complete prompt for Claude API.

        Args:
            paper_text: Full text of the paper
            metadata: Paper metadata (title, authors, year, etc.)
            custom_instructions: Optional custom instructions

        Returns:
            Formatted prompt string
        """
        # Get base template
        template = self._get_template()

        # Build metadata section
        metadata_section = self._format_metadata(metadata)

        # Build the prompt
        prompt = template.format(
            metadata=metadata_section,
            paper_text=paper_text,
            custom_instructions=custom_instructions or "",
        )

        return prompt

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format paper metadata into a readable string."""
        parts = []

        if "title" in metadata:
            parts.append(f"- Title: {metadata['title']}")
        if "authors" in metadata:
            authors = metadata["authors"]
            if isinstance(authors, list):
                authors = ", ".join(authors)
            parts.append(f"- Authors: {authors}")
        if "year" in metadata:
            parts.append(f"- Year: {metadata['year']}")
        if "publication" in metadata:
            parts.append(f"- Publication: {metadata['publication']}")
        if "doi" in metadata:
            parts.append(f"- DOI: {metadata['doi']}")
        if "url" in metadata:
            parts.append(f"- URL: {metadata['url']}")

        return "\n".join(parts) if parts else "- No metadata available"

    def _get_template(self) -> str:
        """Get the appropriate template based on prompt type."""
        templates = {
            PromptType.COMPREHENSIVE: self._comprehensive_template(),
            PromptType.QUICK_SUMMARY: self._quick_summary_template(),
            PromptType.TECHNICAL_DEEP_DIVE: self._technical_template(),
            PromptType.LITERATURE_REVIEW: self._literature_review_template(),
            PromptType.METHODOLOGY: self._methodology_template(),
            PromptType.CITATION_ANALYSIS: self._citation_analysis_template(),
        }
        return templates[self.prompt_type]

    def _comprehensive_template(self) -> str:
        """Template for comprehensive paper analysis."""
        return """You are an expert research assistant analyzing an academic paper. Provide a thorough, well-structured analysis that would be valuable to researchers and students.

Paper Information:
{metadata}

Full Text:
{paper_text}

Generate a comprehensive analysis with the following sections:

## Executive Summary
Provide a 2-3 paragraph overview that captures the essence of the paper. What is this paper about, and why does it matter?

## Research Context and Motivation
- What problem does this paper address?
- Why is this problem important?
- What gap in existing research does this fill?
- What are the main research questions or objectives?

## Methodology
- What research design and approach was used?
- How was data collected and analyzed?
- What tools, techniques, or frameworks were employed?
- What are the key assumptions or constraints?

## Key Findings and Results
- What are the main results and observations?
- What evidence supports these findings?
- Are there any surprising or unexpected results?
- How robust and reliable are the findings?

## Contributions to the Field
- What are the novel contributions of this work?
- How does it advance the state of the art?
- What is the significance and impact?
- How does it compare to prior work?

## Limitations and Future Work
- What are the acknowledged limitations?
- What questions remain unanswered?
- What future research directions are suggested?
- What are potential weaknesses or concerns?

## Key References and Related Work
- What are the most important papers cited?
- How does this work relate to the broader literature?
- What theoretical or methodological foundations does it build on?

{custom_instructions}

Provide your analysis in clear, well-structured markdown format. Be precise, objective, and thorough."""

    def _quick_summary_template(self) -> str:
        """Template for quick paper summary."""
        return """You are an expert research assistant. Provide a concise summary of this academic paper.

Paper Information:
{metadata}

Full Text:
{paper_text}

Provide a quick summary addressing:

## In One Sentence
Summarize the entire paper in a single sentence.

## Key Points (3-5 bullet points)
- What problem is addressed?
- What approach/method is used?
- What are the main findings?
- Why does it matter?

## Who Should Read This
What audience would benefit most from reading this paper?

{custom_instructions}

Keep your response concise and focused on the most important information."""

    def _technical_template(self) -> str:
        """Template for technical deep dive."""
        return """You are an expert technical reviewer analyzing the methodological and technical aspects of this academic paper.

Paper Information:
{metadata}

Full Text:
{paper_text}

Provide a detailed technical analysis covering:

## Technical Approach
- What specific methods, algorithms, or techniques are used?
- How are they implemented?
- What are the technical innovations?

## Experimental Design
- What is the experimental setup?
- What datasets, benchmarks, or testbeds are used?
- How are experiments controlled and validated?

## Mathematical/Theoretical Foundation
- What mathematical models or theoretical frameworks are employed?
- Are there key equations or formalisms?
- How rigorous is the theoretical treatment?

## Implementation Details
- What tools, libraries, or platforms are used?
- Are there important implementation choices?
- Is the work reproducible?

## Results and Evaluation
- How are results measured and evaluated?
- What metrics are used?
- How do results compare to baselines?
- Are statistical tests applied?

## Technical Limitations
- What are the technical constraints?
- Where might the approach struggle?
- What assumptions may not hold in practice?

{custom_instructions}

Focus on technical depth and precision. Include specific details, equations, and technical terminology."""

    def _literature_review_template(self) -> str:
        """Template for literature review focus."""
        return """You are an expert researcher analyzing how this paper fits into the broader academic literature.

Paper Information:
{metadata}

Full Text:
{paper_text}

Analyze the paper's relationship to existing literature:

## Research Lineage
- What prior work does this build directly upon?
- What is the historical development of this research area?
- How has thinking evolved on this topic?

## Key Citations and Influences
- What are the most important papers cited?
- Who are the key researchers and schools of thought?
- What theoretical frameworks or paradigms are referenced?

## Positioning in the Field
- How does this work position itself relative to others?
- What debates or controversies does it engage with?
- Does it challenge or support existing views?

## Gaps Addressed
- What gap in the literature does this fill?
- Why was this gap important?
- How successful is it at filling this gap?

## Related Work Comparison
- How does this compare to similar approaches?
- What are the key differences and similarities?
- What are the relative strengths and weaknesses?

## Influence and Reception
- What impact might this work have on future research?
- What new questions or directions does it open?
- Who would build on this work?

{custom_instructions}

Emphasize connections, influences, and the scholarly conversation this paper participates in."""

    def _methodology_template(self) -> str:
        """Template for methodology-focused analysis."""
        return """You are an expert methodologist analyzing the research methods used in this academic paper.

Paper Information:
{metadata}

Full Text:
{paper_text}

Provide a detailed methodological analysis:

## Research Design
- What type of research design is employed (experimental, observational, theoretical, etc.)?
- What is the overall research strategy?
- Is the design appropriate for the research questions?

## Data Collection
- What data is collected and how?
- What is the sampling strategy?
- What are potential sources of bias?

## Analysis Methods
- What analytical techniques are used?
- Are they appropriate for the data and questions?
- How rigorous is the analysis?

## Validity and Reliability
- How is internal validity addressed?
- How is external validity (generalizability) addressed?
- What reliability checks are performed?
- What are potential threats to validity?

## Ethical Considerations
- Are there ethical considerations?
- How are they addressed?
- Are there potential ethical concerns?

## Methodological Strengths
- What are the methodological innovations or strengths?
- What is done particularly well?

## Methodological Limitations
- What are the methodological weaknesses?
- What could have been done differently?
- How do limitations affect the conclusions?

{custom_instructions}

Focus on the soundness, rigor, and appropriateness of the research methods."""

    def _citation_analysis_template(self) -> str:
        """Template for citation and reference analysis."""
        return """You are an expert bibliographer analyzing the citations and references in this academic paper.

Paper Information:
{metadata}

Full Text:
{paper_text}

Analyze the paper's citations and references:

## Key References
List and categorize the most important references cited:
- Foundational works that establish the research area
- Methodological sources (methods, tools, frameworks)
- Empirical studies providing evidence or comparison
- Theoretical frameworks and models
- Recent/contemporary work in the field

## Citation Pattern Analysis
- How extensive is the literature review?
- What time period do citations cover?
- Are citations concentrated in certain areas?
- Are there notable omissions?

## Influential Authors and Works
- Who are the most cited authors?
- What seminal papers appear repeatedly?
- What schools of thought or research groups are referenced?

## Interdisciplinary Connections
- Does the paper draw on multiple disciplines?
- How are different fields integrated?
- What cross-disciplinary influences are present?

## Citation Context
For the most important references, explain:
- Why are they cited?
- How do they support the current work?
- What specific ideas or findings are drawn from them?

{custom_instructions}

Focus on understanding the scholarly foundations and intellectual influences on this work."""


def get_available_prompt_types() -> Dict[str, str]:
    """
    Get a dictionary of available prompt types and their descriptions.

    Returns:
        Dict mapping prompt type names to descriptions
    """
    return {
        "comprehensive": "Complete analysis with all sections (default)",
        "quick_summary": "Brief summary with key points",
        "technical_deep_dive": "Detailed technical and methodological analysis",
        "literature_review": "Focus on citations and relationship to existing work",
        "methodology": "In-depth analysis of research methods",
        "citation_analysis": "Analysis of references and scholarly influences",
    }
