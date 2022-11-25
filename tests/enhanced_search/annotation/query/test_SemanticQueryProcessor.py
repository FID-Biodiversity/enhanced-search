from typing import List

import pytest

from enhanced_search.annotation import (
    Annotation,
    Feature,
    LiteralString,
    NamedEntityType,
    Query,
    RelationshipType,
    Statement,
    Uri,
)
from enhanced_search.annotation.query.processors import SemanticQueryProcessor

# Alias for clarity
from enhanced_search.annotation.text import TextAnnotator

ExpectedQuery = Query


class TestSemanticQueryProcessor:
    @pytest.mark.parametrize(
        ["query", "expected_query"],
        [
            (  # Scenario - No annotations
                Query("Something not in the database"),
                ExpectedQuery("Something not in the database"),
            ),
            (  # Scenario - A species is searched: No enrichment necessary
                Query(
                    "Fagus sylvatica",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={
                                Uri("https://www.biofid.de/ontology/fagus_sylvatica")
                            },
                        )
                    ],
                ),
                ExpectedQuery(
                    "Fagus sylvatica",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={
                                Uri("https://www.biofid.de/ontology/fagus_sylvatica")
                            },
                        )
                    ],
                ),
            ),
            (  # Scenario - A taxon with a location: No enrichment necessary
                Query(
                    "Fagus in Deutschland",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=5,
                            text="Fagus",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={Uri("https://www.biofid.de/ontology/fagus")},
                        ),
                        Annotation(
                            begin=9,
                            end=20,
                            text="Deutschland",
                            named_entity_type=NamedEntityType.LOCATION,
                            uris={Uri("https://sws.geonames.org/deutschland")},
                        ),
                    ],
                    literals=[LiteralString(begin=6, end=8, text="in", is_safe=False)],
                ),
                ExpectedQuery(
                    "Fagus in Deutschland",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=5,
                            text="Fagus",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={Uri("https://www.biofid.de/ontology/fagus")},
                        ),
                        Annotation(
                            begin=9,
                            end=20,
                            text="Deutschland",
                            named_entity_type=NamedEntityType.LOCATION,
                            uris={Uri("https://sws.geonames.org/deutschland")},
                        ),
                    ],
                    literals=[LiteralString(begin=6, end=8, text="in", is_safe=False)],
                ),
            ),
            (  # Scenario - A taxon with a filtering property (both are URIs)
                Query(
                    "Pflanzen mit roten Blüten",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=8,
                            text="Pflanzen",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={Uri("https://www.biofid.de/ontology/pflanzen")},
                        ),
                        Annotation(
                            begin=13,
                            end=18,
                            text="roten",
                            named_entity_type=NamedEntityType.MISCELLANEOUS,
                            uris={
                                Uri(
                                    url="https://pato.org/red_color",
                                    position_in_triple=3,
                                )
                            },
                        ),
                        Annotation(
                            begin=19,
                            end=25,
                            text="Blüten",
                            named_entity_type=NamedEntityType.MISCELLANEOUS,
                            uris={
                                Uri(
                                    url="https://pato.org/flower_part",
                                    position_in_triple=2,
                                )
                            },
                        ),
                    ],
                    literals=[
                        LiteralString(begin=9, end=12, text="mit", is_safe=False)
                    ],
                    statements=[
                        Statement(
                            subject={Uri("https://www.biofid.de/ontology/pflanzen")},
                            predicate={
                                Uri(
                                    url="https://pato.org/flower_part",
                                    position_in_triple=2,
                                )
                            },
                            object={Uri(url="https://pato.org/red_color")},
                        )
                    ],
                ),
                ExpectedQuery(
                    "Pflanzen mit roten Blüten",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=8,
                            text="Pflanzen",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={
                                Uri(
                                    "https://www.biofid.de/ontology"
                                    "/plant_with_red_flower_1",
                                    is_safe=True,
                                ),
                                Uri(
                                    "https://www.biofid.de/ontology"
                                    "/plant_with_red_flower_2",
                                    is_safe=True,
                                ),
                                Uri(
                                    "https://www.biofid.de/ontology"
                                    "/plant_with_red_flower_3",
                                    is_safe=True,
                                ),
                                Uri(
                                    "https://www.biofid.de/ontology"
                                    "/plant_with_red_flower_and_3_petals",
                                    is_safe=True,
                                ),
                            },
                            features=[
                                Feature(
                                    property=None,
                                    value={
                                        Uri("https://www.biofid.de/ontology/pflanzen")
                                    },
                                ),
                                Feature(
                                    property={Uri("https://pato.org/flower_part", 2)},
                                    value={Uri("https://pato.org/red_color", 3)},
                                ),
                            ],
                        ),
                    ],
                    literals=[
                        LiteralString(begin=9, end=12, text="mit", is_safe=False)
                    ],
                ),
            ),
            (  # Scenario - A taxon with a filtering property (one is a user set value)
                Query(
                    "Pflanzen mit 3 Kelchblättern",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=8,
                            text="Pflanzen",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={Uri("https://www.biofid.de/ontology/pflanzen")},
                        ),
                        Annotation(
                            begin=15,
                            end=28,
                            text="Kelchblättern",
                            named_entity_type=NamedEntityType.MISCELLANEOUS,
                            uris={
                                Uri(
                                    "https://pato.org/has_petal_count",
                                    position_in_triple=2,
                                )
                            },
                        ),
                    ],
                    literals=[
                        LiteralString(begin=9, end=12, text="mit", is_safe=False),
                        LiteralString(begin=13, end=14, text="3", is_safe=False),
                    ],
                    statements=[
                        Statement(
                            subject={Uri("https://www.biofid.de/ontology/pflanzen")},
                            predicate={
                                Uri(
                                    "https://pato.org/has_petal_count",
                                    position_in_triple=2,
                                )
                            },
                            object=LiteralString(
                                begin=13, end=14, text="3", is_safe=False
                            ),
                        )
                    ],
                ),
                ExpectedQuery(
                    "Pflanzen mit 3 Kelchblättern",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=8,
                            text="Pflanzen",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={
                                Uri(
                                    "https://www.biofid.de/ontology"
                                    "/plant_with_red_flower_and_3_petals",
                                    is_safe=True,
                                ),
                            },
                            features=[
                                Feature(
                                    property=None,
                                    value={
                                        Uri("https://www.biofid.de/ontology/pflanzen")
                                    },
                                ),
                                Feature(
                                    property={
                                        Uri(
                                            "https://pato.org/has_petal_count",
                                            position_in_triple=2,
                                        )
                                    },
                                    value=LiteralString(begin=13, end=14, text="3"),
                                ),
                            ],
                        ),
                    ],
                    literals=[
                        LiteralString(begin=9, end=12, text="mit", is_safe=False)
                    ],
                ),
            ),
            (  # Scenario - There are no URIs in the Knowledge DB fitting the criteria
                Query(
                    "Pflanzen mit 25 Kelchblättern",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=8,
                            text="Pflanzen",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={Uri("https://www.biofid.de/ontology/pflanzen")},
                        ),
                        Annotation(
                            begin=16,
                            end=29,
                            text="Kelchblättern",
                            named_entity_type=NamedEntityType.MISCELLANEOUS,
                            uris={
                                Uri(
                                    "https://pato.org/has_petal_count",
                                    position_in_triple=2,
                                )
                            },
                        ),
                    ],
                    literals=[
                        LiteralString(begin=9, end=12, text="mit", is_safe=False),
                        LiteralString(begin=13, end=15, text="25", is_safe=False),
                    ],
                    statements=[
                        Statement(
                            subject={Uri("https://www.biofid.de/ontology/pflanzen")},
                            predicate={
                                Uri(
                                    "https://pato.org/has_petal_count",
                                    position_in_triple=2,
                                )
                            },
                            object=LiteralString(
                                begin=13, end=15, text="25", is_safe=False
                            ),
                        )
                    ],
                ),
                ExpectedQuery(
                    "Pflanzen mit 25 Kelchblättern",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=8,
                            text="Pflanzen",
                            named_entity_type=NamedEntityType.PLANT,
                            uris=set(),
                            features=[
                                Feature(
                                    property=None,
                                    value={
                                        Uri("https://www.biofid.de/ontology/pflanzen")
                                    },
                                ),
                                Feature(
                                    property={
                                        Uri(
                                            "https://pato.org/has_petal_count",
                                            position_in_triple=2,
                                        )
                                    },
                                    value=LiteralString(begin=13, end=15, text="25"),
                                ),
                            ],
                        ),
                    ],
                    literals=[
                        LiteralString(begin=9, end=12, text="mit", is_safe=False),
                    ],
                ),
            ),
            (  # Scenario - An ambitious annotation is enriched
                Query(
                    "Paris mit grünen Blüten",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=5,
                            text="Paris",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={Uri("https://www.biofid.de/ontology/paris")},
                            ambiguous_annotations={
                                Annotation(
                                    begin=0,
                                    end=5,
                                    text="Paris",
                                    named_entity_type=NamedEntityType.LOCATION,
                                    uris={Uri("https://sws.geonames.org/Paris")},
                                    features=[
                                        Feature(
                                            property={
                                                Uri("https://pato.org/flower_part")
                                            },
                                            value={Uri("https://pato.org/red_color")},
                                        )
                                    ],
                                )
                            },
                        ),
                        Annotation(
                            begin=10,
                            end=16,
                            text="grünen",
                            named_entity_type=NamedEntityType.MISCELLANEOUS,
                            uris={Uri("https://pato.org/green_color")},
                        ),
                        Annotation(
                            begin=17,
                            end=23,
                            text="Blüten",
                            named_entity_type=NamedEntityType.MISCELLANEOUS,
                            uris={
                                Uri(
                                    "https://pato.org/flower_part", position_in_triple=2
                                )
                            },
                        ),
                    ],
                    literals=[
                        LiteralString(begin=6, end=9, text="mit", is_safe=False),
                    ],
                    statements=[
                        Statement(
                            subject={Uri("https://www.biofid.de/ontology/paris")},
                            predicate={
                                Uri(
                                    "https://pato.org/flower_part", position_in_triple=2
                                )
                            },
                            object={Uri("https://pato.org/green_color")},
                        )
                    ],
                ),
                ExpectedQuery(
                    "Paris mit grünen Blüten",
                    annotations=[
                        Annotation(
                            begin=0,
                            end=5,
                            text="Paris",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={
                                Uri(
                                    "https://www.biofid.de/ontology/paris_quadrifolia",
                                    is_safe=True,
                                )
                            },
                            features=[
                                Feature(
                                    property=None,
                                    value={Uri("https://www.biofid.de/ontology/paris")},
                                ),
                                Feature(
                                    property={
                                        Uri(
                                            "https://pato.org/flower_part",
                                            position_in_triple=2,
                                        )
                                    },
                                    value={Uri("https://pato.org/green_color")},
                                ),
                            ],
                        ),
                    ],
                    literals=[
                        LiteralString(begin=6, end=9, text="mit", is_safe=False),
                    ],
                ),
            ),
        ],
    )
    def test_resolve_query_annotations(self, query, expected_query, query_processor):
        """Feature: A given query is appropriately enriched, if necessary."""
        query_processor.resolve_query_annotations(query)

        query.statements.clear()  # Here, we don't care about statements
        assert query == expected_query

    @pytest.mark.parametrize(
        ["query", "expected_annotations"],
        [
            (  # Scenario - No annotation data available
                Query("Something not in the database"),
                [],
            ),
            (  # Scenario - A multi-token taxon
                Query(
                    original_string="Fagus sylvatica",
                ),
                [
                    Annotation(
                        begin=0,
                        end=15,
                        text="Fagus sylvatica",
                        lemma="Fagus sylvatica",
                        named_entity_type=NamedEntityType.PLANT,
                        uris={Uri("https://www.biofid.de/ontology/fagus_sylvatica")},
                    )
                ],
            ),
            (  # Scenario - A taxon with a location in a IN-relation
                Query(
                    original_string="Fagus in Deutschland",
                ),
                [
                    Annotation(
                        begin=0,
                        end=5,
                        text="Fagus",
                        lemma="Fagus",
                        named_entity_type=NamedEntityType.PLANT,
                        uris={Uri("https://www.biofid.de/ontology/fagus")},
                    ),
                    Annotation(
                        begin=9,
                        end=20,
                        text="Deutschland",
                        lemma="Deutschland",
                        named_entity_type=NamedEntityType.LOCATION,
                        uris={Uri("https://sws.geonames.org/deutschland")},
                    ),
                ],
            ),
        ],
    )
    def test_update_query_with_annotations(
        self,
        query: Query,
        expected_annotations: List[Annotation],
        query_processor: SemanticQueryProcessor,
    ):
        """Feature: The annotations of a Query are correctly assigned."""
        query_processor.update_query_with_annotations(query)
        assert query.annotations == expected_annotations

    @pytest.mark.parametrize(
        ["query", "expected_statements"],
        [
            (  # Scenario - No statements
                Query(
                    "Fagus sylvatica",
                ),
                [],
            ),
            (  # Scenario - Single statement
                Query(
                    "Pflanzen mit roten Blüten",
                ),
                [
                    Statement(
                        subject={Uri("https://www.biofid.de/ontology/pflanzen")},
                        predicate={
                            Uri(
                                url="https://pato.org/flower_part",
                                position_in_triple=2,
                            )
                        },
                        object={Uri(url="https://pato.org/red_color")},
                    )
                ],
            ),
            (  # Scenario - OR-conjunction
                Query("Pflanzen oder Hafen"),
                [
                    Statement(
                        subject={Uri("https://www.biofid.de/ontology/pflanzen")},
                        object=LiteralString(
                            begin=14, end=19, text="Hafen", is_safe=False
                        ),
                        relationship=RelationshipType.OR,
                    )
                ],
            ),
        ],
    )
    def test_update_query_with_statements(
        self,
        query: Query,
        expected_statements: List[Statement],
        query_processor: SemanticQueryProcessor,
    ):
        """Feature: The statements of the annotations are correctly deduced."""
        query_processor.update_query_with_annotations(query)
        assert query.statements == expected_statements

    def test_no_database_query_with_no_data(self, text_annotator):
        """Feature: The SemanticEngine does not not call the database when there
        are no Statements.
        """

        # The database of this SemanticEngine will raise as soon as it is called.
        query_processor = SemanticQueryProcessor(
            semantic_engine_name="failing-sparql-engine", text_annotator=text_annotator
        )
        query = Query("Foo")

        query_processor.resolve_query_annotations(query)
        assert query.statements == []

    @pytest.fixture
    def query_processor(self, text_annotator: TextAnnotator):
        return SemanticQueryProcessor(
            semantic_engine_name="sparql", text_annotator=text_annotator
        )
