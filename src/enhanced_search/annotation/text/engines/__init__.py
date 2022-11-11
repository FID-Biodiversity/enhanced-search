from typing import Protocol, runtime_checkable

from enhanced_search.annotation import AnnotationResult

from .dependencies import PatternDependencyAnnotationEngine
from .disambiguation import DisambiguationAnnotationEngine
from .entity_linking import UriLinkerAnnotatorEngine
from .literals import LiteralAnnotationEngine
from .named_entity_recognition import StringBasedNamedEntityAnnotatorEngine


@runtime_checkable
class AnnotationEngine(Protocol):
    """An interface class for all classes that interact with the
    TextAnnotator.
    """

    def parse(self, text: str, annotations: AnnotationResult) -> None:
        """Provide the text and the current state (the AnnotationResult) of
        the annotations to this AnnotationEngine.
        The method updates the AnnotationResult object.
        """
