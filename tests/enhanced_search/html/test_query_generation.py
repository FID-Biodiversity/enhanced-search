from enhanced_search.annotation import Query
from enhanced_search.html.query_generation import convert_request_data_to_query


class TestQueryGeneration:
    def test_request_to_query(self):
        request_data = {"query": "This is a test!"}
        query = convert_request_data_to_query(request_data)
        assert query == Query(original_string="This is a test!")
