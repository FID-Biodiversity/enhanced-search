"""Database interfaces to talk to different Document Databases."""

import json

import pysolr

from enhanced_search.errors import UserInputException
from enhanced_search.utils import escape_characters

EXCLUDE_IN_SOLR_QUERY = [
    "qt=",
    "stream.body",
    "/config",
    "shards.qt=",
    "fl=",
    "/update",
    "shards=",
]
SOLR_SPECIAL_CHARACTERS = "&|+\\!(){}[\\]*^~?:$="


class SolrDatabase:
    """A wrapper class that handles the communication with an Apache Solr database.

    Args:
        url: The URL of the Solr instance including the core name, if necessary.

    Examples:
        >>> db = SolrDatabase(url="http://localhost:1234/solr/my-core")
    """

    def __init__(self, url: str, *args, **kwargs):
        self._db = pysolr.Solr(url, *args, **kwargs)

    def read(self, query: str, is_safe: bool = False, **kwargs) -> str:
        """Searches the data in the Solr database.

        Args:
            query: The query string handed to the Solr database.
            is_safe: An indicator, if the given query is sanitized. If False,
                    the query will be escaped before communicated to the database.
                    BEWARE: Only the query is escaped. Additional parameters will
                    NOT be escaped!
        """
        if not is_safe:
            query = self.sanitize_query(query)

        solr_response = self._db.search(query, **kwargs)

        return json.dumps(solr_response.raw_response)

    def sanitize_query(self, text: str) -> str:
        """The query for the given database should be sanitized
        as appropriate.
        """
        if not is_solr_query_safe(text):
            raise UserInputException(
                f"The input '{text}' contained potential "
                "malicious character sequences!"
            )

        return escape_solr_input(text)


def escape_solr_input(query: str, ignore_quotations: bool = False) -> str:
    """Escapes special characters used by Solr.

    Args:
        query: The query to escape.
        ignore_quotations: If True, single and double quotation marks are not
                            escaped.
    """
    solr_escape_characters = list("&|+\\!(){}[\\]*^~?:$=-")
    if not ignore_quotations:
        solr_escape_characters.extend(['"', "'"])

    return escape_characters(text=query, escape_characters=solr_escape_characters)


def is_solr_query_safe(query) -> bool:
    """This simple function shall protect the database from injection attacks.
    For Solr: Relies on the tips given
    in https://github.com/dergachev/solr-security-proxy
    """

    lowered_query = query.lower()
    if any(evil.lower() in lowered_query for evil in EXCLUDE_IN_SOLR_QUERY):
        return False

    # Everything was fine
    return True
