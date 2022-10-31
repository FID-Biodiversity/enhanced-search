from typing import List

import pytest

from enhanced_search.annotation.text import Annotation, TextAnnotator
from enhanced_search.annotation.text.engines import (
    StringBasedNamedEntityAnnotatorEngine,
)
from enhanced_search.annotation.text.data import (
    TextAnnotatorConfiguration,
    NamedEntityType,
)


class TestStringBasedNamedEntityAnnotatorEngine:
    @pytest.mark.parametrize(
        ["text", "expected_annotations"],
        [
            (  # Scenario - Only a genus is given
                "Quercus",
                [
                    Annotation(
                        begin=0,
                        end=7,
                        text="Quercus",
                        named_entity_type=NamedEntityType.PLANT,
                    )
                ],
            ),
            (  # Scenario - Full species name is provided
                "Quercus sylvestris",
                [
                    Annotation(
                        begin=0,
                        end=18,
                        text="Quercus sylvestris",
                        named_entity_type=NamedEntityType.PLANT,
                    )
                ],
            ),
            (  # Scenario - AND-conjuncted species with a genus
                "Quercus sylvestris und Fagus",
                [
                    Annotation(
                        begin=0,
                        end=18,
                        text="Quercus sylvestris",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=23,
                        end=28,
                        text="Fagus",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                ],
            ),
            (  # Scenario - OR-conjuncted species with genus
                "Quercus sylvestris oder Fagus",
                [
                    Annotation(
                        begin=0,
                        end=18,
                        text="Quercus sylvestris",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=24,
                        end=29,
                        text="Fagus",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                ],
            ),
            (  # Scenario - A single genus with a location with an "in"
                "Fagus in Deutschland",
                [
                    Annotation(
                        begin=0,
                        end=5,
                        text="Fagus",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=9,
                        end=20,
                        text="Deutschland",
                        named_entity_type=NamedEntityType.LOCATION,
                    ),
                ],
            ),
            (  # Scenario - Single genus with location with no "in"
                "Fagus Deutschland",
                [
                    Annotation(
                        begin=0,
                        end=5,
                        text="Fagus",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=6,
                        end=17,
                        text="Deutschland",
                        named_entity_type=NamedEntityType.LOCATION,
                    ),
                ],
            ),
            (  # Scenario - Species with location with no "in"
                "Fagus sylvatica Deutschland",
                [
                    Annotation(
                        begin=0,
                        end=15,
                        text="Fagus sylvatica",
                        named_entity_type=NamedEntityType.PLANT,
                    ),
                    Annotation(
                        begin=16,
                        end=27,
                        text="Deutschland",
                        named_entity_type=NamedEntityType.LOCATION,
                    ),
                ],
            ),
            (  # Scenario - A species name in quotes
                "'Fagus sylvatica'",
                [
                    Annotation(
                        begin=0,
                        end=15,
                        text="Fagus sylvatica",
                        named_entity_type=NamedEntityType.PLANT,
                    )
                ],
            ),
            (  # Scenario - A genus name within a longer quoted string
                "'A quoted Fagus journal'",
                [],
            ),
            (  # Scenario - An ambiguous term
                "What about Paris?",
                [
                    Annotation(
                        begin=11,
                        end=16,
                        text="Paris",
                        named_entity_type=NamedEntityType.PLANT,
                        ambiguous_annotations={
                            Annotation(
                                begin=11,
                                end=16,
                                text="Paris",
                                named_entity_type=NamedEntityType.LOCATION,
                            )
                        },
                    ),
                ],
            ),
        ],
    )
    def test_annotation(
        self,
        annotator: TextAnnotator,
        text: str,
        expected_annotations: List[Annotation],
    ):
        """Feature: Basic annotation with the KeywordAnnotationEngine."""
        annotations = annotator.annotate(text)
        assert annotations == expected_annotations

    @pytest.fixture
    def annotator(self, database):
        ne_engine = StringBasedNamedEntityAnnotatorEngine(database)
        configuration = TextAnnotatorConfiguration(named_entity_recognition=ne_engine)
        return TextAnnotator(configuration)

    @pytest.fixture
    def database(self):
        return DummyKeyValueDatabase()


class DummyKeyValueDatabase:
    def __init__(self):
        self.data = {
            "quercus": '{"Plant_Flora": '
            '[["https://www.biofid.de/ontology/quercus", 3]]}',
            "quercus sylvestris": '{"Plant_Flora": '
            '[["https://www.biofid.de/ontology/quercus_sylvestris", 3]]}',
            "fagus": '{"Plant_Flora": '
            '[["https://www.biofid.de/ontology/fagus", 3]]}',
            "fagus sylvatica": '{"Plant_Flora": '
            '[["https://www.biofid.de/ontology/fagus_sylvatica", 3]]}',
            "deutschland": '{"Location_Place": [['
            '"https://sws.geonames.org/deutschland", 3]]}',
            "paris": '{"Location_Place": [["https://sws.geonames.org/paris", 3]],'
            '"Plant_Flora": [["https://www.biofid.de/ontology/fagus_sylvatica"'
            ", 3]]}",
        }

    def read(self, query: str) -> str:
        return self.data.get(query)
