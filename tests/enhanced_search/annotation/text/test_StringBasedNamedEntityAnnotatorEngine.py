from typing import List

import pytest

from enhanced_search.annotation import (
    Annotation,
    NamedEntityType,
    AnnotationResult,
    Word,
)
from enhanced_search.annotation.text.engines import (
    StringBasedNamedEntityAnnotatorEngine,
)


class TestStringBasedNamedEntityAnnotatorEngine:
    @pytest.mark.parametrize(
        ["tokens", "expected_annotations"],
        [
            (  # Scenario - Only a genus is given
                [Word(begin=0, end=7, text="Quercus", lemma="Quercus")],
                [
                    Annotation(
                        begin=0,
                        end=7,
                        text="Quercus",
                        lemma="Quercus",
                        named_entity_type=NamedEntityType.PLANT,
                    )
                ],
            ),
            (  # Scenario - Full species name is provided
                [
                    Word(begin=0, end=7, text="Quercus", lemma="Quercus"),
                    Word(begin=8, end=18, text="sylvestris", lemma="sylvestris"),
                ],
                [
                    Annotation(
                        begin=0,
                        end=18,
                        text="Quercus sylvestris",
                        lemma="Quercus sylvestris",
                        named_entity_type=NamedEntityType.PLANT,
                    )
                ],
            ),
            (  # Scenario - AND-conjuncted species with a genus
                [
                    Word(begin=0, end=7, text="Quercus", lemma="Quercus"),
                    Word(begin=8, end=18, text="sylvestris", lemma="sylvestris"),
                    Word(begin=19, end=22, text="und", lemma="und"),
                    Word(begin=23, end=28, text="Fagus", lemma="Fagus"),
                ],
                [
                    Annotation(
                        begin=0,
                        end=18,
                        text="Quercus sylvestris",
                        lemma="Quercus sylvestris",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=23,
                        end=28,
                        text="Fagus",
                        lemma="Fagus",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                ],
            ),
            (  # Scenario - A single genus with a location with an "in"
                [
                    Word(begin=0, end=5, text="Fagus", lemma="Fagus"),
                    Word(begin=6, end=8, text="in", lemma="in"),
                    Word(begin=9, end=20, text="Deutschland", lemma="Deutschland"),
                ],
                [
                    Annotation(
                        begin=0,
                        end=5,
                        text="Fagus",
                        lemma="Fagus",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=9,
                        end=20,
                        text="Deutschland",
                        lemma="Deutschland",
                        named_entity_type=NamedEntityType.LOCATION,
                    ),
                ],
            ),
            (  # Scenario - Single genus with location with no "in"
                [
                    Word(begin=0, end=5, text="Fagus", lemma="Fagus"),
                    Word(begin=6, end=17, text="Deutschland", lemma="Deutschland"),
                ],
                [
                    Annotation(
                        begin=0,
                        end=5,
                        text="Fagus",
                        lemma="Fagus",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=6,
                        end=17,
                        text="Deutschland",
                        lemma="Deutschland",
                        named_entity_type=NamedEntityType.LOCATION,
                    ),
                ],
            ),
            (  # Scenario - Species with location with no "in"
                [
                    Word(begin=0, end=5, text="Fagus", lemma="Fagus"),
                    Word(begin=6, end=15, text="sylvatica", lemma="sylvatica"),
                    Word(begin=16, end=27, text="Deutschland", lemma="Deutschland"),
                ],
                [
                    Annotation(
                        begin=0,
                        end=15,
                        text="Fagus sylvatica",
                        lemma="Fagus sylvatica",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=16,
                        end=27,
                        text="Deutschland",
                        lemma="Deutschland",
                        named_entity_type=NamedEntityType.LOCATION,
                    ),
                ],
            ),
            (  # Scenario - A species name in quotes
                [
                    Word(
                        begin=0,
                        end=15,
                        text="Fagus sylvatica",
                        lemma="Fagus sylvatica",
                        is_quoted=True,
                    )
                ],
                [
                    Annotation(
                        begin=0,
                        end=15,
                        text="Fagus sylvatica",
                        lemma="Fagus sylvatica",
                        named_entity_type=NamedEntityType.PLANT,
                    )
                ],
            ),
            (  # Scenario - A genus name within a longer quoted string
                [
                    Word(
                        begin=0,
                        end=5,
                        text="A quoted Fagus journal",
                        lemma="A quoted Fagus journal",
                        is_quoted=True,
                    )
                ],
                [],
            ),
            (  # Scenario - An ambiguous term
                [
                    Word(begin=0, end=4, text="What", lemma="What"),
                    Word(begin=5, end=10, text="about", lemma="about"),
                    Word(begin=11, end=16, text="Paris", lemma="Paris"),
                ],
                [
                    Annotation(
                        begin=11,
                        end=16,
                        text="Paris",
                        lemma="Paris",
                        named_entity_type=NamedEntityType.PLANT,
                        ambiguous_annotations={
                            Annotation(
                                begin=11,
                                end=16,
                                text="Paris",
                                lemma="Paris",
                                named_entity_type=NamedEntityType.LOCATION,
                            )
                        },
                    ),
                ],
            ),
        ],
    )
    def test_parse(
        self,
        string_based_ne_annotator_engine: StringBasedNamedEntityAnnotatorEngine,
        tokens: List[Word],
        expected_annotations: List[Annotation],
    ):
        """Feature: Basic annotation with the KeywordAnnotationEngine."""
        annotation_result = AnnotationResult()
        annotation_result.tokens = tokens
        string_based_ne_annotator_engine.parse("Foo", annotation_result)
        assert annotation_result.named_entity_recognition == expected_annotations
