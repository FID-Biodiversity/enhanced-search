"""Database interfaces to talk to different Graph and Triple-Store Databases."""

import json
from typing import Optional, Protocol

from SPARQLWrapper import SPARQLWrapper


class KnowledgeDatabase(Protocol):
    """An interface class to interact with any graph database.

    Obeys the Database interface.
    """

    def read(self, query: str, is_safe: bool = False, **kwargs) -> Optional[str]:
        """Queries a database with the given query string and
        parameters and returns the retrieved data as string.

        Args:
            query: A valid query string.
            is_safe: A boolean to confirm that the given query string is sanitized
                     appropriately. Default: False

        Returns:
            A string representation of the database response. This function may
            return None, if no corresponding data could be retrieved.
        """

    def sanitize_query(self, text: str) -> str:
        """The query for the given database should be sanitized
        as appropriate.
        """


class SparqlGraphDatabase:
    """An interface class to interact with any SPARQL database.
    The current implementation makes POST requests per default, to avoid getting
    errors due to too large SPARQL query strings.

    Obeys the KnowledgeDatabase interface.
    """

    def __init__(
        self, url: str, return_format: str = "json", request_type: str = "POST"
    ):
        self.url = url
        self.return_format = return_format
        self.request_type = request_type

        self._db = self._create_sparql_connector()

    def read(self, query: str, is_safe: bool = False) -> str:
        """Queries a database with the given query string and
        parameters and returns the retrieved data as string.
        """
        if not is_safe:
            query = escape_sparql_input(query)

        self._db.setQuery(query)

        return json.dumps(self._db.queryAndConvert())

    def _create_sparql_connector(self) -> SPARQLWrapper:
        sparql = SPARQLWrapper(endpoint=self.url, returnFormat=self.return_format)
        sparql.setMethod(self.request_type)
        return sparql


def escape_sparql_input(text: str) -> str:
    """Escapes dangerous characters in the given text string.
    Escaped characters:
        * Single quotes
        * Double quotes
        * Backslashes
        * Hashtags
    """
    characters_to_escape = [
        "\\",
        "'",
        '"',
        "#",
        "<",
        ">",
    ]  # backslash has to be the first escaped character!

    for char in characters_to_escape:
        text = text.replace(char, f"\\{char}")

    return text
