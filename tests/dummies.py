"""A set of dummy databases for testing purposes."""

import pathlib
from typing import Optional, Union

from rdflib import Graph


class DummySparqlKnowledgeDatabase:
    """A dummy SPARQL database class that obeys the KnowledgeDatabase interface."""

    def __init__(self, rdf_source_path: Optional[Union[pathlib.Path, str]] = None):
        self.db = Graph()

        if rdf_source_path is not None:
            self.db.parse(rdf_source_path)

    def read(self, query: str) -> str:
        """Queries a database with the given query string and
        parameters and returns the retrieved data as string.
        """
        result = self.db.query(query)

        serialized_data = result.serialize(format="json")

        if serialized_data is not None:
            return serialized_data.decode("utf-8")

        raise TypeError('No data found for the given query!')

    def parse(self, rdf_source_path: Union[pathlib.Path, str]) -> None:
        """Load the RDF data from a given path."""
        self.db.parse(rdf_source_path)

    def sanitize_query(self, text: str) -> str:
        """This method does nothing, only returns the given text."""
        return text


class DummyKeyValueDatabase:
    """Returns a value for a given key.
    Since very short sequences or numerical values led in the past to mayor
    performance penalties, a read with a short or numerical-only key (e.g. 1894) will
    raise a KeyError.
    """

    def __init__(self):
        self.data = {}

    def read(self, query: str) -> str:
        """Get data for a query string."""
        self._raise_if_not_valid(query)
        return self.data.get(query)

    def sanitize_query(self, text: str) -> str:
        """This method does nothing, only returns the given text."""
        return text

    def _raise_if_not_valid(self, query: str) -> None:
        if query.isnumeric() or len(query) <= 2:
            raise KeyError(
                f"Reading short or numerical-only values is forbidden "
                f"for performance reasons! Provided was string: '{query}'"
            )
