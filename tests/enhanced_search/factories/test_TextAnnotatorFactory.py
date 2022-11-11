from typing import List, Type

import pytest

from enhanced_search.annotation.text import AnnotationEngine, TextAnnotator
from enhanced_search.annotation.text.engines import (
    DisambiguationAnnotationEngine,
    LiteralAnnotationEngine,
    PatternDependencyAnnotationEngine,
    StringBasedNamedEntityAnnotatorEngine,
    UriLinkerAnnotatorEngine,
)
from enhanced_search.factories import TextAnnotatorFactory


class TestTextAnnotatorFactory:
    def test_create(self, text_annotator_factory):
        """Feature: Create a pre-configured TextAnnotator"""
        text_annotator = text_annotator_factory.create()
        assert_has_annotation_engines(
            text_annotator,
            [
                DisambiguationAnnotationEngine,
                LiteralAnnotationEngine,
                PatternDependencyAnnotationEngine,
                StringBasedNamedEntityAnnotatorEngine,
                UriLinkerAnnotatorEngine,
            ],
        )

    @pytest.fixture(scope="session")
    def text_annotator_factory(self):
        return TextAnnotatorFactory()


def assert_has_annotation_engines(
    text_annotator: TextAnnotator, annotation_engines: List[Type[AnnotationEngine]]
) -> None:
    is_engine_in_text_annotator = []
    for engine in annotation_engines:
        for applied_engine in text_annotator.annotation_engines:
            if isinstance(applied_engine, engine):
                is_engine_in_text_annotator.append(True)
                break
        else:
            is_engine_in_text_annotator.append(False)

    assert all(is_engine_in_text_annotator)
