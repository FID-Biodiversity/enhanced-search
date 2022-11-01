from dataclasses import dataclass
from typing import List, Optional

from .data import Annotation, AnnotationResult
from .engines import AnnotationEngine


@dataclass
class TextAnnotatorConfiguration:
    """Holds the configuration data for the TextAnnotator."""

    named_entity_recognition: Optional[AnnotationEngine] = None
    dependency_recognition: Optional[AnnotationEngine] = None
    entity_linker: Optional[AnnotationEngine] = None


class TextAnnotator:
    """Given an AnnotationEngine object, orchestrates a text annotation."""

    def __init__(self, annotator_configuration: TextAnnotatorConfiguration):
        self.configuration = annotator_configuration

    def annotate(self, text: str) -> List[Annotation]:
        """Annotates the given text and returns a list of Annotations."""
        result = AnnotationResult()
        annotation_engines = [
            self.configuration.named_entity_recognition,
            self.configuration.dependency_recognition,
            self.configuration.entity_linker,
        ]

        for engine in annotation_engines:
            parse_data_to_engine_if_not_none(engine, text, result)

        return compile_annotations(result)


def parse_data_to_engine_if_not_none(
    annotation_engine: Optional[AnnotationEngine],
    text: str,
    result: AnnotationResult,
):
    if annotation_engine is not None:
        annotation_engine.parse(text, result)


def compile_annotations(result: AnnotationResult) -> List[Annotation]:
    """Assembles all annotation data into one list of annotations."""
    return result.named_entity_recognition
