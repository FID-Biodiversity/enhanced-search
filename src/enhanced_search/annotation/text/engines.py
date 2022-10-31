from typing import Protocol

from enhanced_search.databases import KeyValueDatabase
from .data import AnnotationResult, Annotation
from .utils import (
    stream_words_from_query,
    update_annotation_with_data,
)


class AnnotationEngine(Protocol):
    """An interface class for all classes that interact with the
    TextAnnotator.
    """

    def parse(self, text: str, annotations: AnnotationResult) -> None:
        """Provide the text and the current state (the AnnotationResult) of
        the annotations to this AnnotationEngine.
        The method updates the AnnotationResult object.
        """
        ...


class StringBasedNamedEntityAnnotatorEngine:
    """Annotates all NamedEntities on a string base. The annotation is done
    purely by a string comparison.
    No further semantics are extracted.

    Obeys the AnnotatorEngine interface!
    """

    def __init__(self, db: KeyValueDatabase):
        self._db = db

    def parse(self, text: str, annotations: AnnotationResult) -> None:
        """Provide the text and the current state (the AnnotationResult) of
        the annotations to this AnnotationEngine.
        The method updates the AnnotationResult object.
        """
        previous_token_data = None
        retrieved_annotations = []
        end_of_last_complete_named_entity = 0

        for word, begin, end in stream_words_from_query(text):
            if begin < end_of_last_complete_named_entity:
                continue

            corresponding_data = self._db.read(word.lower())

            if corresponding_data is not None:
                previous_token_data = (begin, end, word, corresponding_data)
            elif previous_token_data is not None:
                ann = self._create_annotation(*previous_token_data)
                retrieved_annotations.append(ann)

                end_of_last_complete_named_entity = previous_token_data[1]
                previous_token_data = None
        else:
            # The for-loop is done! Clean up any remaining annotations!
            if previous_token_data is not None:
                ann = self._create_annotation(*previous_token_data)
                retrieved_annotations.append(ann)

        annotations.named_entity_recognition = retrieved_annotations

    def _create_annotation(self, begin: int, end: int, word: str, annotation_data: str):
        annotation = Annotation(begin=begin, end=end, text=word)
        update_annotation_with_data(annotation, annotation_data)
        return annotation
