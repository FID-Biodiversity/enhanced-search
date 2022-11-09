from typing import Protocol, runtime_checkable


@runtime_checkable
class Database(Protocol):
    """An interface class to interact with any database."""

    def read(self, query: str, *args, **kwargs) -> str:
        """Queries a database with the given query string and
        parameters and returns the retrieved data as string.
        """
        ...

    def sanitize_query(self, text: str) -> str:
        """The query for the given database should be sanitized
         as appropriate.
         """
        ...
