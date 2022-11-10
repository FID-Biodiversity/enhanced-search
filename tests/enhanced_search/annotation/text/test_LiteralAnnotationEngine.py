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
                    ]
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
                ),
                [
                    LiteralString(begin=9, end=12, text="mit", is_safe=False),
                    LiteralString(begin=13, end=14, text="3", is_safe=False),
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
