import token

from typing import Optional, Tuple

from enhanced_search.annotation import Annotation, AnnotationResult, Word
from enhanced_search.databases import KeyValueDatabase

from ..utils import update_annotation_with_data


class StringBasedNamedEntityAnnotatorEngine:
    """Annotates all NamedEntities on a string base. The annotation is done
    purely by a string comparison.
    No further semantics are extracted. Hence, URIs are NOT linked to the respective
    Annotation object. For adding URIs, parse the Annotation to an URI-Linker.

    Obeys the AnnotatorEngine interface!
    """

    # This prevents strings of causing noise with little information
    STRING_BLACKLIST = {"l.", "(l.)", "R.", "&", "var.", "in"}

    def __init__(self, db: KeyValueDatabase):
        self._db = db

    def parse(self, text: str, annotation_result: AnnotationResult) -> None:
        """Provide the text and the current state (the AnnotationResult) of
        the annotations to this AnnotationEngine.
        The method updates the AnnotationResult object.
        """
        retrieved_annotations = []

        for index, token in enumerate(annotation_result.tokens):
            _, text, corresponding_data = self._get_data_for_token(token)

            annotation_data = []
            if corresponding_data is not None:
                annotation_data.append((token, text, corresponding_data))

            # Quoted strings should be taken as encapsulated entities
            if text is not None and not token.is_quoted:
                for following_token in annotation_result.tokens[index + 1 :]:
                    text += f" {following_token.text}"
                    extended_word_data = self._db.read(text.lower())
                    if extended_word_data is not None:
                        annotation_data.append(
                            (following_token, text, extended_word_data)
                        )
                    else:
                        break

            if annotation_data:
                relevant_data = annotation_data[-1]
                ann = self._create_annotation(token, *relevant_data)
                retrieved_annotations.append(ann)

        annotation_result.named_entity_recognition = retrieved_annotations

    def _get_data_for_token(
        self, token: Word
    ) -> Tuple[Optional[Word], Optional[str], Optional[str]]:
        for test_string in [token.text, token.lemma]:
            if self._is_word_valid(test_string):
                corresponding_data = self._db.read(test_string.lower())
                if corresponding_data is not None:
                    return token, test_string, corresponding_data

        return None, None, None

    def _create_annotation(
        self, start_token: Word, end_token: Word, text: str, annotation_data: str
    ):
        lemma = start_token.lemma if start_token == end_token else text
        annotation = Annotation(
            begin=start_token.begin, end=end_token.end, text=text, lemma=lemma
        )
        update_annotation_with_data(annotation, annotation_data)
        return annotation

    def _is_word_valid(self, word: str) -> bool:
        """Disapproves very short words (< 2 characters) and numerical strings,
        as well as words in the STRING_BLACKLIST."""
        return (
            not word.isnumeric() and len(word) > 2 and word not in self.STRING_BLACKLIST
        )
