from typing import Protocol

from enhanced_search.annotation import AnnotationResult

from .dependencies import PatternDependencyAnnotationEngine
from .disambiguation import DisambiguationAnnotationEngine
from .literals import LiteralAnnotationEngine
from .named_entity_recognition import StringBasedNamedEntityAnnotatorEngine
from .entity_linking import UriLinkerAnnotatorEngine


class AnnotationEngine(Protocol):
    """An interface class for all classes that interact with the
    TextAnnotator.
    """

    def parse(self, text: str, annotations: AnnotationResult) -> None:
        """Provide the text and the current state (the AnnotationResult) of
        the annotations to this AnnotationEngine.
        The method updates the AnnotationResult object.
        """
