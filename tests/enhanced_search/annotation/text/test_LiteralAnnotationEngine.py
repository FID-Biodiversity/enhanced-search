from typing import List

import pytest

from enhanced_search.annotation import (
    Annotation,
    AnnotationResult,
    LiteralString,
    NamedEntityType,
    Uri,
)
from enhanced_search.annotation.text import AnnotationEngine


class TestLiteralAnnotationEngine:
    @pytest.mark.parametrize(
        ["text", "annotation_result", "expected_literals"],
        [
            (
                "Fagus sylvatica L.",
                AnnotationResult(
                    named_entity_recognition=[
                        Annotation(
                            begin=0,
                            end=18,
                            text="Fagus sylvatica L.",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={
                                Uri("https://www.biofid.de/ontology/fagus_sylvatica")
                            },
                        )
                    ],
                    tokens=[
                        LiteralString(begin=0, end=5, text="Fagus"),
                        LiteralString(begin=7, end=15, text="sylvatica"),
                        LiteralString(begin=16, end=18, text="L."),
                    ],
                ),
                [],
            ),
            (
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
                    tokens=[
                        LiteralString(begin=0, end=5, text="Fagus"),
                        LiteralString(begin=6, end=8, text="in"),
                        LiteralString(begin=9, end=20, text="Deutschland"),
                    ],
                ),
                [LiteralString(begin=6, end=8, text="in", is_safe=False)],
            ),
            (
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
                    tokens=[
                        LiteralString(begin=0, end=8, text="Pflanzen"),
                        LiteralString(begin=9, end=12, text="mit"),
                        LiteralString(begin=13, end=14, text="3"),
                        LiteralString(begin=15, end=28, text="Kelchblätter"),
                    ],
                ),
                [
                    LiteralString(begin=9, end=12, text="mit", is_safe=False),
                    LiteralString(begin=13, end=14, text="3", is_safe=False),
                ],
            ),
            (
                "'The quoted Journal Name' Pflanzen",
                AnnotationResult(
                    named_entity_recognition=[
                        Annotation(
                            begin=26,
                            end=34,
                            text="Pflanzen",
                            named_entity_type=NamedEntityType.PLANT,
                            uris={Uri("https://www.biofid.de/ontology/pflanzen")},
                        )
                    ],
                    tokens=[
                        LiteralString(
                            begin=0,
                            end=25,
                            text="The quoted Journal Name",
                            is_quoted=True,
                        ),
                        LiteralString(begin=26, end=34, text="Pflanzen"),
                    ],
                ),
                [
                    LiteralString(
                        begin=0,
                        end=25,
                        text="The quoted Journal Name",
                        is_quoted=True,
                    )
                ],
            ),
        ],
    )
    def test_parse(
        self,
        text: str,
        annotation_result: AnnotationResult,
        expected_literals: List[LiteralString],
        annotator_engine: AnnotationEngine,
    ):
        annotator_engine.parse(text, annotation_result)
        assert annotation_result.literals == expected_literals

    @pytest.fixture(scope="session")
    def annotator_engine(self, literal_annotator_engine):
        return literal_annotator_engine
