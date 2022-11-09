import json
from typing import List

import pytest

from enhanced_search.annotation import Uri, LiteralString, Statement
from enhanced_search.annotation.query.engines import SparqlQueryGenerator


class TestSparqlQueryGenerator:
    """Tests the SPARQL query generation from a given context.
    A test to pass expects data for an assertion. This is due to the fact,
    that it is very cumbersome to maintain SPARQL query strings to check against.
    Furthermore, since the data that is returned is retrieved from an in-memory
    graph db, the SPARQL query is additionally checked for validity.
    """

    @pytest.mark.parametrize(
        ["statements", "expected_data"],
        [
            (  # Scenario - Check that more than the filtered triples exist
                [
                    Statement(subject=Uri("https://www.biofid.de/ontology/pflanzen")),
                ],
                [
                    "https://www.biofid.de/ontology/fagus_sylvatica",
                    "https://www.biofid.de/ontology/plant_with_green_flowers",
                    "https://www.biofid.de/ontology/plant_with_no_flowers",
                    "https://www.biofid.de/ontology/plant_with_red_flower_1",
                    "https://www.biofid.de/ontology/plant_with_red_flower_2",
                    "https://www.biofid.de/ontology/plant_with_red_flower_3",
                    "https://www.biofid.de/ontology/plant_with_red_flower_and_3_petals",
                ],
            ),
            (  # Scenario - Filter results for two URI attributes
                [
                    Statement(
                        subject=Uri("https://www.biofid.de/ontology/pflanzen"),
                        predicate=[Uri("https://pato.org/flower_part", 2)],
                        object=[Uri("https://pato.org/red_color", 3)],
                    )
                ],
                [
                    "https://www.biofid.de/ontology/plant_with_red_flower_1",
                    "https://www.biofid.de/ontology/plant_with_red_flower_2",
                    "https://www.biofid.de/ontology/plant_with_red_flower_3",
                    "https://www.biofid.de/ontology"
                    "/plant_with_red_flower_and_3_petals",
                ],
            ),
            (  # Scenario - Filter results for URI with string association
                [
                    Statement(
                        subject=Uri("https://www.biofid.de/ontology/pflanzen"),
                        predicate=[Uri("https://pato.org/petal_part", 2)],
                        object=LiteralString(begin=15, end=16, text="3"),
                    )
                ],
                ["https://www.biofid.de/ontology/plant_with_red_flower_and_3_petals"],
            ),
        ],
    )
    def test_generate_sparql_from_annotation_context(
        self,
        statements: List[Statement],
        expected_data: dict,
        sparql_generator,
        sparql_db,
    ):
        """Feature: Correct and valid SPARQL is generated."""
        variable_name = "taxon"
        sparql_query_string = sparql_generator.generate(
            variable_name=f"?{variable_name}", statements=statements
        )

        db_response_string = sparql_db.read(sparql_query_string)

        assert (
            extract_data_from_graph_response(variable_name, db_response_string)
            == expected_data
        )

    @pytest.fixture(scope="session")
    def sparql_generator(self):
        return SparqlQueryGenerator()

    @pytest.fixture(scope="session")
    def sparql_db(self, loaded_sparql_database):
        return loaded_sparql_database


def extract_data_from_graph_response(variable_name: str, response_data_string: str):
    data = json.loads(response_data_string)
    bindings = data["results"]["bindings"]
    return [v[variable_name]["value"] for v in bindings if variable_name in v]
