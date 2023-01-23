import pytest

from enhanced_search.annotation import (
    Annotation,
    Feature,
    LiteralString,
    Query,
    RelationshipType,
    Statement,
    Uri,
)
from enhanced_search.generators import SolrQueryGenerator

# flake8: noqa


class TestSolrQueryGenerator:
    @pytest.mark.parametrize(
        ["query", "expected_solr_query"],
        [
            (  # Scenario - Only single literals
                Query(
                    original_string="Here is no annotation",
                    literals=[
                        LiteralString(begin=0, end=4, text="Here"),
                        LiteralString(begin=5, end=7, text="is"),
                        LiteralString(begin=8, end=10, text="no"),
                        LiteralString(begin=11, end=21, text="annotation"),
                    ],
                ),
                "q:(Here AND is AND no AND annotation)",
            ),
            (  # Scenario - Quoted literal
                Query(
                    original_string="'Here is no annotation'",
                    literals=[
                        LiteralString(
                            begin=0,
                            end=21,
                            text="Here is no annotation",
                            is_quoted=True,
                        ),
                    ],
                ),
                'q:"Here is no annotation"',
            ),
            (  # Scenario - Only a single safe annotation
                Query(
                    original_string="Fagus sylvatica",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus sylvatica",
                            uris={
                                Uri(
                                    url="https://www.biofid.de/ontology/fagus_sylvatica",
                                    is_safe=True,
                                )
                            },
                        )
                    ],
                ),
                'q:"https://www.biofid.de/ontology/fagus_sylvatica"',
            ),
            (  # Scenario - An Annotation with a literal
                Query(
                    original_string="Fagus sylvatica Test",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus sylvatica",
                            uris={
                                Uri(
                                    url="https://www.biofid.de/ontology/fagus_sylvatica",
                                    is_safe=True,
                                )
                            },
                        )
                    ],
                    literals=[LiteralString(begin=16, end=20, text="Test")],
                ),
                'q:"https://www.biofid.de/ontology/fagus_sylvatica" AND q:Test',
            ),
            (  # Scenario - An Annotation with a quoted literal
                Query(
                    original_string="Fagus sylvatica 'Foo Bar'",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus sylvatica",
                            uris={
                                Uri(
                                    url="https://www.biofid.de/ontology/fagus_sylvatica",
                                    is_safe=True,
                                )
                            },
                        )
                    ],
                    literals=[
                        LiteralString(begin=16, end=25, text="Foo Bar", is_quoted=True)
                    ],
                ),
                'q:"https://www.biofid.de/ontology/fagus_sylvatica" AND ' 'q:"Foo Bar"',
            ),
            (  # Scenario - AND-Relationship
                Query(
                    original_string="Fagus sylvatica und Foo",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus sylvatica",
                            is_quoted=True,
                            uris={
                                Uri(
                                    url="https://www.biofid.de/ontology/fagus_sylvatica",
                                    is_safe=True,
                                ),
                                Uri(
                                    url="https://www.biofid.de/ontology/another_fagus",
                                    is_safe=True,
                                ),
                            },
                        )
                    ],
                    literals=[LiteralString(begin=21, end=24, text="Foo")],
                    statements=[
                        Statement(
                            subject={
                                Uri(
                                    "https://www.biofid.de/ontology/fagus_sylvatica",
                                    is_safe=True,
                                ),
                                Uri(
                                    "https://www.biofid.de/ontology/another_fagus",
                                    is_safe=True,
                                ),
                            },
                            object=LiteralString(begin=21, end=24, text="Foo"),
                            relationship=RelationshipType.AND,
                        )
                    ],
                ),
                'q:("https://www.biofid.de/ontology/another_fagus" OR '
                '"https://www.biofid.de/ontology/fagus_sylvatica") AND q:Foo',
            ),
            (  # Scenario - Two NEs in an AND-Conjunction
                Query(
                    original_string="Fagus sylvatica und Quercus",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus sylvatica",
                            is_quoted=False,
                            uris={
                                Uri(
                                    url="https://www.biofid.de/ontology"
                                    "/another_fagus",
                                    is_safe=True,
                                ),
                                Uri(
                                    url="https://www.biofid.de/ontology"
                                    "/another_fagus",
                                    is_safe=True,
                                ),
                            },
                            features=[
                                Feature(
                                    value={
                                        Uri(
                                            url="https://www.biofid.de/ontology"
                                            "/another_fagus",
                                            is_safe=True,
                                        ),
                                        Uri(
                                            url="https://www.biofid.de/ontology"
                                            "/another_fagus",
                                            is_safe=True,
                                        ),
                                    }
                                ),
                                Feature(
                                    value={
                                        Uri(
                                            url="https://www.biofid.de/ontology/quercus",
                                            is_safe=True,
                                        )
                                    }
                                ),
                            ],
                        )
                    ],
                    statements=[
                        Statement(
                            subject={
                                Uri(
                                    "https://www.biofid.de/ontology/fagus_sylvatica",
                                    is_safe=True,
                                ),
                                Uri(
                                    "https://www.biofid.de/ontology/another_fagus",
                                    is_safe=True,
                                ),
                            },
                            object={
                                Uri(
                                    "https://www.biofid.de/ontology/quercus",
                                    is_safe=True,
                                )
                            },
                            relationship=RelationshipType.AND,
                        )
                    ],
                ),
                'q:("https://www.biofid.de/ontology/another_fagus" OR '
                '"https://www.biofid.de/ontology/fagus_sylvatica") AND '
                'q:"https://www.biofid.de/ontology/quercus"',
            ),
            (  # Scenario - OR-Relationship
                Query(
                    original_string="Fagus sylvatica oder Foo",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus sylvatica",
                            is_quoted=True,
                            uris={
                                Uri(
                                    url="https://www.biofid.de/ontology/fagus_sylvatica",
                                    is_safe=True,
                                ),
                                Uri(
                                    url="https://www.biofid.de/ontology/another_fagus",
                                    is_safe=True,
                                ),
                            },
                        )
                    ],
                    literals=[LiteralString(begin=21, end=24, text="Foo")],
                    statements=[
                        Statement(
                            subject={
                                Uri(
                                    "https://www.biofid.de/ontology/fagus_sylvatica",
                                    is_safe=True,
                                ),
                                Uri(
                                    "https://www.biofid.de/ontology/another_fagus",
                                    is_safe=True,
                                ),
                            },
                            object=LiteralString(begin=21, end=24, text="Foo"),
                            relationship=RelationshipType.OR,
                        )
                    ],
                ),
                'q:("https://www.biofid.de/ontology/another_fagus" OR '
                '"https://www.biofid.de/ontology/fagus_sylvatica") OR q:Foo',
            ),
            (  # Scenario - Literal OR-conjunction
                Query(
                    original_string="Foo or Bar",
                    literals=[
                        LiteralString(begin=0, end=3, text="Foo"),
                        LiteralString(begin=7, end=10, text="Bar"),
                    ],
                    statements=[
                        Statement(
                            subject=LiteralString(begin=0, end=3, text="Foo"),
                            object=LiteralString(begin=7, end=10, text="Bar"),
                            relationship=RelationshipType.OR,
                        )
                    ],
                ),
                "q:Foo OR q:Bar",
            ),
            (  # Scenario - Unsafe input data
                Query(
                    original_string="Fagus sylvatica 'Foo Bar'",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus sylvatica",
                            uris={
                                Uri(
                                    url="https://www.biofid.de/ontology/fagus_sylvatica",
                                )
                            },
                        )
                    ],
                    literals=[
                        LiteralString(begin=16, end=25, text="Foo Bar", is_quoted=True)
                    ],
                ),
                'q:"https\\://www.biofid.de/ontology/fagus_sylvatica" AND '
                'q:"Foo Bar"',
            ),
        ],
    )
    def test_to_solr_query(
        self,
        query: Query,
        expected_solr_query: str,
        solr_query_generator: SolrQueryGenerator,
    ):
        """Feature: The correct Solr query is generated from the given Annotations."""
        generated_query = solr_query_generator.to_solr_query(query)
        assert generated_query.string == expected_solr_query

    @pytest.mark.parametrize(
        ["query", "expected_solr_query"],
        [
            (
                Query(
                    original_string="Fagus sylvatica Test",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus sylvatica",
                            uris={
                                Uri(
                                    url="https://www.biofid.de/ontology/fagus_sylvatica",
                                    is_safe=True,
                                )
                            },
                        )
                    ],
                    literals=[LiteralString(begin=16, end=20, text="Test")],
                ),
                'q:"https://www.biofid.de/ontology/fagus_sylvatica" OR q:Test',
            )
        ],
    )
    def test_modify_default_conjunction_type(
        self, query, expected_solr_query, solr_query_generator
    ):
        """Feature: Default conjunction type can be changed."""
        solr_query_generator.default_conjunction_type = RelationshipType.OR
        generated_query = solr_query_generator.to_solr_query(query)
        assert generated_query.string == expected_solr_query

    @pytest.fixture
    def solr_query_generator(self):
        return SolrQueryGenerator()
