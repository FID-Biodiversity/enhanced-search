"""Base interface classes to interact with different databases."""

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class Database(Protocol):
    """An interface class to interact with any database."""

    def read(self, query: str, is_safe: bool = False, **kwargs) -> Optional[str]:
        """Queries a database with the given query string and
        parameters and returns the retrieved data as string.

        This function may return None, if no corresponding data
        could be retrieved.
        """

    def sanitize_query(self, text: str) -> str:
        """The query for the given database should be sanitized
        as appropriate.
        """
