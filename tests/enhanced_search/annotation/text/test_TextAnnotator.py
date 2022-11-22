import pytest

from enhanced_search.annotation import Annotation, LiteralString, NamedEntityType, Uri


class TestTextAnnotator:
    @pytest.mark.parametrize(
        ["text", "expected_annotations", "expected_literals"],
        [
            (  # Scenario: Taxon with some literals
                "ich suche Fagus Sylvatica!",
                [
                    Annotation(
                        begin=10,
                        end=25,
                        text="Fagus Sylvatica",
                        lemma="Fagus Sylvatica",
                        named_entity_type=NamedEntityType.PLANT,
                        uris={
                            Uri(url="https://www.biofid.de/ontology/fagus_sylvatica")
                        },
                    ),
                ],
                [
                    LiteralString(begin=0, end=3, text="ich"),
                    LiteralString(begin=4, end=9, text="suche"),
                ],
            ),
            (  # Scenario: Ambiguous terms
                "Paris in Paris",
                [
                    Annotation(
                        begin=0,
                        end=5,
                        text="Paris",
                        lemma="Paris",
                        named_entity_type=NamedEntityType.PLANT,
                        uris={Uri(url="https://www.biofid.de/ontology/paris")},
                    ),
                    Annotation(
                        begin=9,
                        end=14,
                        text="Paris",
                        lemma="Paris",
                        named_entity_type=NamedEntityType.LOCATION,
                        uris={Uri(url="https://sws.geonames.org/paris")},
                    ),
                ],
                [
                    LiteralString(begin=6, end=8, text="in"),
                ],
            ),
            (  # Scenario: All lowercase words and no complete sentence
                "Pflanze rote blüten",
                [
                    Annotation(
                        begin=0,
                        end=7,
                        text="Pflanze",
                        lemma="Pflanze",
                        named_entity_type=NamedEntityType.PLANT,
                        uris={Uri(url="https://www.biofid.de/ontology/pflanzen")},
                    ),
                    Annotation(
                        begin=8,
                        end=12,
                        text="rote",
                        lemma="rot",
                        named_entity_type=NamedEntityType.MISCELLANEOUS,
                        uris={Uri(url="https://pato.org/red_color")},
                    ),
                    Annotation(
                        begin=13,
                        end=19,
                        text="blüten",
                        lemma="Blüte",
                        named_entity_type=NamedEntityType.MISCELLANEOUS,
                        uris={
                            Uri(
                                url="https://pato.org/flower_part", position_in_triple=2
                            )
                        },
                    ),
                ],
                [],
            ),
        ],
    )
    def test_annotate(
        self, text, expected_annotations, expected_literals, text_annotator
    ):
        """Feature: The TextAnnotator annotates a given text as expected."""
        annotation_result = text_annotator.annotate(text)
        assert annotation_result.named_entity_recognition == expected_annotations
        assert annotation_result.literals == expected_literals
