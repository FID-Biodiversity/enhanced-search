import pytest

from enhanced_search.annotation import Annotation, NamedEntityType, AnnotationResult


class TestDisambiguationAnnotationEngine:
    @pytest.mark.parametrize(
        ["text", "annotations", "expected_disambiguated_annotations"],
        [
            (  # No ambiguity => Nothing happens
                "Fagus sylvatica",
                [
                    Annotation(
                        begin=0,
                        end=15,
                        text="Fagus sylvatica",
                        named_entity_type=NamedEntityType.PLANT,
                    )
                ],
                {},
            ),
            (  # Ambiguity, but probably no location => Taxon is preferred
                "Fagus sylvatica Paris",
                [
                    Annotation(
                        begin=0,
                        end=15,
                        text="Fagus sylvatica",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=16,
                        end=21,
                        text="Paris",
                        named_entity_type=NamedEntityType.PLANT,
                        ambiguous_annotations={
                            Annotation(
                                begin=16,
                                end=21,
                                text="Paris",
                                named_entity_type=NamedEntityType.LOCATION,
                            )
                        },
                    ),
                ],
                {
                    Annotation(
                        begin=16,
                        end=21,
                        text="Paris",
                        named_entity_type=NamedEntityType.PLANT,
                        ambiguous_annotations={
                            Annotation(
                                begin=16,
                                end=21,
                                text="Paris",
                                named_entity_type=NamedEntityType.LOCATION,
                            )
                        },
                    ): Annotation(
                        begin=16,
                        end=21,
                        text="Paris",
                        named_entity_type=NamedEntityType.PLANT,
                    )
                },
            ),
            (  # Clearly a location => Annotation is resolved as Location
                    "Fagus sylvatica in Paris",
                    [
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus sylvatica",
                            named_entity_type=NamedEntityType.PLANT,
                        ),
                        Annotation(
                            begin=19,
                            end=24,
                            text="Paris",
                            named_entity_type=NamedEntityType.PLANT,
                            ambiguous_annotations={
                                Annotation(
                                    begin=19,
                                    end=24,
                                    text="Paris",
                                    named_entity_type=NamedEntityType.LOCATION,
                                )
                            },
                        ),
                    ],
                    {
                        Annotation(
                            begin=19,
                            end=24,
                            text="Paris",
                            named_entity_type=NamedEntityType.PLANT,
                            ambiguous_annotations={
                                Annotation(
                                    begin=19,
                                    end=24,
                                    text="Paris",
                                    named_entity_type=NamedEntityType.LOCATION,
                                )
                            },
                        ): Annotation(
                            begin=19,
                            end=24,
                            text="Paris",
                            named_entity_type=NamedEntityType.LOCATION,
                        )
                    },
            ),
            (  # Multiple locations
                    "Fagus sylvatica in Berlin, New York und Paris",
                    [
                        Annotation(
                            begin=0,
                            end=15,
                            text="Fagus sylvatica",
                            named_entity_type=NamedEntityType.PLANT,
                        ),
                        Annotation(
                            begin=27,
                            end=35,
                            text="New York",
                            named_entity_type=NamedEntityType.LOCATION,
                        ),
                        Annotation(
                            begin=40,
                            end=45,
                            text="Paris",
                            named_entity_type=NamedEntityType.PLANT,
                            ambiguous_annotations={
                                Annotation(
                                    begin=40,
                                    end=45,
                                    text="Paris",
                                    named_entity_type=NamedEntityType.LOCATION,
                                )
                            },
                        ),
                    ],
                    {
                        Annotation(
                            begin=40,
                            end=45,
                            text="Paris",
                            named_entity_type=NamedEntityType.PLANT,
                            ambiguous_annotations={
                                Annotation(
                                    begin=40,
                                    end=45,
                                    text="Paris",
                                    named_entity_type=NamedEntityType.LOCATION,
                                )
                            },
                        ): Annotation(
                            begin=40,
                            end=45,
                            text="Paris",
                            named_entity_type=NamedEntityType.LOCATION,
                        )
                    },
            ),
        ],
    )
    def test_parse(
        self,
        text,
        annotations,
        expected_disambiguated_annotations,
        disambiguation_annotator_engine,
    ):
        annotation_result = AnnotationResult()
        annotation_result.named_entity_recognition = annotations

        disambiguation_annotator_engine.parse(text, annotation_result)

        assert (
            annotation_result.disambiguated_annotations
            == expected_disambiguated_annotations
        )
