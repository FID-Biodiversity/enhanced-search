from copy import copy
from dataclasses import dataclass
from typing import Dict, List, Optional

from enhanced_search.annotation import Annotation, AnnotationResult, LiteralString, Word

from .engines import AnnotationEngine


@dataclass
class TextAnnotatorConfiguration:
    """Holds the configuration data for the TextAnnotator."""

    named_entity_recognition: Optional[AnnotationEngine] = None
    dependency_recognition: Optional[AnnotationEngine] = None
    entity_linker: Optional[AnnotationEngine] = None
    disambiguation_engine: Optional[AnnotationEngine] = None
    literal_recognition: Optional[AnnotationEngine] = None


class TextAnnotator:
    """Given an AnnotationEngine object, orchestrates a text annotation."""

    def __init__(self, annotator_configuration: TextAnnotatorConfiguration):
        self.configuration = annotator_configuration

    def annotate(self, text: str) -> AnnotationResult:
        """Annotates the given text and returns a list of Annotations."""
        result = AnnotationResult()
        annotation_engines = [
            self.configuration.named_entity_recognition,
            self.configuration.literal_recognition,
            self.configuration.dependency_recognition,
            self.configuration.entity_linker,
            self.configuration.disambiguation_engine,
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


def compile_annotations(result: AnnotationResult) -> AnnotationResult:
    """Associates Annotations with their respective data."""
    result.named_entity_recognition = update_annotations_with_disambiguated_annotations(
        result.named_entity_recognition, result.disambiguated_annotations
    )

    for annotation in result.named_entity_recognition:
        uris_per_ne_type = result.entity_linking.get(annotation.id, {})
        uris = uris_per_ne_type.get(annotation.named_entity_type)
        if uris is not None:
            annotation.uris = uris

    return result


def update_annotations_with_disambiguated_annotations(
    annotations: List[Annotation], disambiguations: Dict[Annotation, Annotation]
) -> List[Annotation]:
    """Returns a new updated list of disambiguated Annotations."""
    annotations = copy(annotations)

    for original_annotation in disambiguations.keys():
        annotations.remove(original_annotation)

    annotations.extend(disambiguations.values())

    return sorted(annotations, key=lambda ann: ann.begin)
