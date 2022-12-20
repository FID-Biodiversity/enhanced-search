from typing import List

import pytest

from enhanced_search.annotation import (
    Annotation,
    AnnotationResult,
    LiteralString,
    NamedEntityType,
)
from enhanced_search.annotation.text.engines import (
    StringBasedNamedEntityAnnotatorEngine,
)


class TestStringBasedNamedEntityAnnotatorEngine:
    @pytest.mark.parametrize(
        ["tokens", "expected_annotations"],
        [
            (  # Scenario - Only a genus is given
                [LiteralString(begin=0, end=7, text="Quercus", lemma="Quercus")],
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
                    LiteralString(begin=0, end=7, text="Quercus", lemma="Quercus"),
                    LiteralString(
                        begin=8, end=18, text="sylvestris", lemma="sylvestris"
                    ),
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
                    LiteralString(begin=0, end=7, text="Quercus", lemma="Quercus"),
                    LiteralString(
                        begin=8, end=18, text="sylvestris", lemma="sylvestris"
                    ),
                    LiteralString(begin=19, end=22, text="und", lemma="und"),
                    LiteralString(begin=23, end=28, text="Fagus", lemma="Fagus"),
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
                    LiteralString(begin=0, end=5, text="Fagus", lemma="Fagus"),
                    LiteralString(begin=6, end=8, text="in", lemma="in"),
                    LiteralString(
                        begin=9, end=20, text="Deutschland", lemma="Deutschland"
                    ),
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
                    LiteralString(begin=0, end=5, text="Fagus", lemma="Fagus"),
                    LiteralString(
                        begin=6, end=17, text="Deutschland", lemma="Deutschland"
                    ),
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
                    LiteralString(begin=0, end=5, text="Fagus", lemma="Fagus"),
                    LiteralString(begin=6, end=15, text="sylvatica", lemma="sylvatica"),
                    LiteralString(
                        begin=16, end=27, text="Deutschland", lemma="Deutschland"
                    ),
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
                    LiteralString(
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
                    LiteralString(
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
                    LiteralString(begin=0, end=4, text="What", lemma="What"),
                    LiteralString(begin=5, end=10, text="about", lemma="about"),
                    LiteralString(begin=11, end=16, text="Paris", lemma="Paris"),
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
            (  # Scenario - A species with many tokens and a potential ambiguity
                [
                    LiteralString(begin=0, end=5, text="Fagus", lemma="Fagus"),
                    LiteralString(begin=6, end=15, text="sylvatica", lemma="sylvatica"),
                    LiteralString(begin=16, end=18, text="f.", lemma="f."),
                    LiteralString(begin=19, end=26, text="pendula", lemma="pendula"),
                    LiteralString(begin=27, end=34, text="(Lodd.)", lemma="(Lodd.)"),
                    LiteralString(begin=35, end=41, text="Dippel", lemma="Dippel"),
                ],
                [
                    Annotation(
                        begin=0,
                        end=41,
                        text="Fagus sylvatica f. pendula (Lodd.) Dippel",
                        lemma="Fagus sylvatica f. pendula (Lodd.) Dippel",
                        named_entity_type=NamedEntityType.PLANT,
                    )
                ],
            ),
            (
                [
                    LiteralString(begin=0, end=8, text="Pflanzen", lemma="Pflanze"),
                    LiteralString(begin=9, end=15, text="gelben", lemma="gelb"),
                    LiteralString(begin=16, end=22, text="Blüten", lemma="Blüte"),
                ],
                [
                    Annotation(
                        begin=0,
                        end=8,
                        text="Pflanzen",
                        lemma="Pflanze",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=9,
                        end=22,
                        lemma="gelb Blüte",
                        text="gelben Blüten",
                        named_entity_type=NamedEntityType.MISCELLANEOUS,
                    ),
                ],
            ),
        ],
    )
    def test_parse(
        self,
        string_based_ne_annotator_engine: StringBasedNamedEntityAnnotatorEngine,
        tokens: List[LiteralString],
        expected_annotations: List[Annotation],
    ):
        """Feature: Basic annotation with the KeywordAnnotationEngine."""
        annotation_result = AnnotationResult()
        annotation_result.tokens = tokens
        string_based_ne_annotator_engine.parse("Foo", annotation_result)
        assert annotation_result.named_entity_recognition == expected_annotations
