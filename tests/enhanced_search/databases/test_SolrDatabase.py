import json

import pytest
import responses

from enhanced_search.databases.documents import SolrDatabase
from enhanced_search.errors import UserInputException


class TestSolrDatabase:
    @responses.activate
    def test_read(self, solr_db, solr_response_toml_file_path):
        """Feature: Solr database is called appropriately."""
        responses.patch("http://localhost:8983")
        responses._add_from_file(file_path=solr_response_toml_file_path)

        response_string = solr_db.read("*:*", is_safe=True, fl="id")

        document_data = get_document_data_from_response_string(response_string)
        assert document_data["numFound"] == 827488

    @pytest.mark.parametrize(
        ["query", "expected_sanitized_query"],
        [
            ("Foo bar", "Foo bar"),
            ("id:'foo bar'", "id\\:\\'foo bar\\'"),
            ('id:"foo bar"', 'id\\:\\"foo bar\\"'),
        ],
    )
    def test_sanitization(self, query: str, expected_sanitized_query: str, solr_db):
        """Feature: Sanitization is working correctly."""
        sanitized_query = solr_db.sanitize_query(query)
        assert sanitized_query == expected_sanitized_query

    def test_malicious_input_raises_error(self, solr_db):
        """Feature: Malicious substrings raise an Exception."""
        malicious_query = "This is STREAM.Body = evil"
        with pytest.raises(UserInputException):
            solr_db.read(malicious_query)

    @pytest.fixture
    def solr_db(self):
        return SolrDatabase(url="http://localhost:8983/solr/digitaleSammlungen")

    @pytest.fixture(scope="session")
    def solr_response_toml_file_path(self, resource_directory):
        return resource_directory / "http/solr.toml"


def get_document_data_from_response_string(response_string: str) -> dict:
    """Converts a Solr response string into a dict and returns
    only the response data.
    """
    solr_data = json.loads(response_string)
    return solr_data["response"]
