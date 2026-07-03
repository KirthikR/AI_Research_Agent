"""
Abstract base tool for all information-gathering tools.

Every search/scrape tool inherits from BaseTool to provide
a uniform interface for the agent controller.
"""

from abc import ABC, abstractmethod

from agent.models import SearchResult


class BaseTool(ABC):
    """Abstract base class for all research tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the tool."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this tool does — used by the LLM for source selection."""
        ...

    @abstractmethod
    def execute(self, query: str) -> list[SearchResult]:
        """
        Execute a search/scrape for the given query.

        Args:
            query: The search query string.

        Returns:
            A list of SearchResult objects with gathered information.
        """
        ...

    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
