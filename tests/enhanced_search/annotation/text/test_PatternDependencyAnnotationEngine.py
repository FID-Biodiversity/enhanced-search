from typing import List

import pytest

from enhanced_search.annotation import (
    Annotation,
    AnnotationResult,
    LiteralString,
    NamedEntityType,
    RelationshipType,
    Statement,
    Uri,
)
from enhanced_search.annotation.text import AnnotationEngine


class TestPatternDependencyAnnotationEngine:
    @pytest.mark.parametrize(
        ["text", "annotation_result", "expected_statements"],
        [
            (  # Scenario - No annotations
                "Something not in the database",
                AnnotationResult(),
                [],
            ),
            (  # Scenario - A species is searched
                "Fagus sylvatica",
                AnnotationResult(
                    named_entity_recognition=[
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={
                                Uri("https://www.biofid.de/ontology/fagus_sylvatica")
                            },
                        )
                    ]
                ),
                [],
            ),
            (  # Scenario - A taxon with a location
                "Fagus in Deutschland",
                AnnotationResult(
                    named_entity_recognition=[
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
                [],
            ),
            (  # Scenario - A taxon with a filtering property (both are URIs)
                "Pflanzen mit roten Blüten",
                AnnotationResult(
                    named_entity_recognition=[
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
                ),
                [{"subject": "0/8", "predicate": "19/25", "object": "13/18"}],
            ),
            (  # Scenario - A taxon with a filtering property (filtering property is
                # multi-token entity containing both adjective and noun)
                "Pflanzen mit gelben Blüten",
                AnnotationResult(
                    named_entity_recognition=[
                        Annotation(
                            begin=0,
                            end=8,
                            text="Pflanzen",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={Uri("https://www.biofid.de/ontology/pflanzen")},
                        ),
                        Annotation(
                            begin=13,
                            end=26,
                            text="gelben Blüten",
                            named_entity_type=NamedEntityType.MISCELLANEOUS,
                            uris={
                                Uri(
                                    url="https://flopo.org/yellow_flower",
                                    position_in_triple=3,
                                )
                            },
                        ),
                    ],
                    literals=[
                        LiteralString(begin=9, end=12, text="mit", is_safe=False)
                    ],
                ),
                [{"subject": "0/8", "predicate": None, "object": "13/26"}],
            ),
            (  # Scenario - A taxon with a filtering property (one is a user set value)
                "Pflanzen mit 3 Kelchblättern",
                AnnotationResult(
                    named_entity_recognition=[
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
                ),
                [
                    {
                        "subject": "0/8",
                        "predicate": "15/28",
                        "object": "13/14",
                    }
                ],
            ),
            (  # Scenario - An ambitious annotation is enriched
                "Paris mit grünen Blüten",
                AnnotationResult(
                    named_entity_recognition=[
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
                ),
                [
                    {
                        "subject": "0/5",
                        "predicate": "17/23",
                        "object": "10/16",
                    }
                ],
            ),
            (  # Scenario - Literals with an OR-conjunction
                "Gerste oder Malz",
                AnnotationResult(
                    literals=[
                        LiteralString(begin=0, end=6, text="Gerste", is_safe=False),
                        LiteralString(begin=7, end=11, text="oder", is_safe=False),
                        LiteralString(begin=12, end=16, text="Malz", is_safe=False),
                    ],
                ),
                [
                    {
                        "subject": "0/6",
                        "object": "12/16",
                        "relationship": RelationshipType.OR,
                    }
                ],
            ),
            (  # Scenario - Quoted literals with an OR-conjunction
                "'Gerste oder Malz'",
                AnnotationResult(
                    literals=[
                        LiteralString(begin=0, end=6, text="Gerste", is_safe=False),
                        LiteralString(begin=7, end=11, text="oder", is_safe=False),
                        LiteralString(begin=12, end=16, text="Malz", is_safe=False),
                    ],
                ),
                [],
            ),
            (  # Scenario - Literal and taxon in OR-conjunction
                "Fagus oder Gerste",
                AnnotationResult(
                    named_entity_recognition=[
                        Annotation(
                            begin=0,
                            end=5,
                            text="Fagus",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={
                                Uri("https://www.biofid.de/ontology/fagus_sylvatica")
                            },
                        )
                    ],
                    literals=[
                        LiteralString(begin=6, end=10, text="oder", is_safe=False),
                        LiteralString(begin=11, end=17, text="Gerste", is_safe=False),
                    ],
                ),
                [
                    {
                        "subject": "0/5",
                        "object": "11/17",
                        "relationship": RelationshipType.OR,
                    }
                ],
            ),
        ],
    )
    def test_parse(
        self,
        text: str,
        annotation_result: AnnotationResult,
        expected_statements: List[Statement],
        annotation_engine: AnnotationEngine,
    ):
        annotation_engine.parse(text, annotation_result)
        assert annotation_result.annotation_relationships == expected_statements

    @pytest.fixture(scope="session")
    def annotation_engine(self, pattern_dependency_annotator_engine):
        return pattern_dependency_annotator_engine
