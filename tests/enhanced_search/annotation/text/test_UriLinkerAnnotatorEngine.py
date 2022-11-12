from typing import List, Dict

import pytest

from enhanced_search.annotation import (
    Annotation,
    AnnotationResult,
    Uri,
    NamedEntityType,
)
from enhanced_search.annotation.text.engines import UriLinkerAnnotatorEngine


class TestUriLinkerAnnotatorEngine:
    @pytest.mark.parametrize(
        ["annotations", "expected_linked_entities"],
        [
            (  # Scenario - Simple annotation
                [
                    Annotation(
                        begin=0,
                        end=15,
                        text="Fagus sylvatica",
                        lemma="Fagus sylvatica",
                        named_entity_type=NamedEntityType.PLANT,
                    )
                ],
                {
                    "0/15": {
                        NamedEntityType.PLANT: {
                            Uri(
                                url="https://www.biofid.de/ontology/fagus_sylvatica",
                                position_in_triple=3,
                            )
                        }
                    }
                },
            ),
            (  # Scenario - Ambitious annotation
                [
                    Annotation(
                        begin=0,
                        end=5,
                        text="Paris",
                        lemma="Paris",
                        named_entity_type=NamedEntityType.PLANT,
                        ambiguous_annotations={
                            Annotation(
                                begin=0,
                                end=5,
                                text="Paris",
                                lemma="Paris",
                                named_entity_type=NamedEntityType.LOCATION,
                            )
                        },
                    ),
                ],
                {
                    "0/5": {
                        NamedEntityType.PLANT: {
                            Uri(
                                url="https://www.biofid.de/ontology/paris",
                                position_in_triple=3,
                            )
                        },
                        NamedEntityType.LOCATION: {
                            Uri(
                                url="https://sws.geonames.org/paris",
                                position_in_triple=3,
                            )
                        },
                    }
                },
            ),
        ],
    )
    def test_parse(
        self,
        annotations: List[Annotation],
        expected_linked_entities: Dict[Annotation, List[Uri]],
        uri_linker_annotator_engine: UriLinkerAnnotatorEngine,
    ):
        """Feature: Basic entity linking."""
        annotation_result = AnnotationResult(named_entity_recognition=annotations)
        uri_linker_annotator_engine.parse("Foo", annotation_result)

        assert annotation_result.entity_linking == expected_linked_entities
