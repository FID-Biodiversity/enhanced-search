"""Methods used for the annotation of literal strings (i.e. all strings that are
no named entities).
"""

import itertools

from enhanced_search.annotation import AnnotationResult


class LiteralAnnotationEngine:
    """Simply only puts all tokens that are not Annotations into a list.

    Obeys the AnnotatorEngine interface!
    """

    def parse(self, _: str, annotation_result: AnnotationResult) -> None:
        """Puts all tokens into a list."""

        named_entity_char_positions = set(
            itertools.chain.from_iterable(
                range(ne.begin, ne.end + 1)
                for ne in annotation_result.named_entity_recognition
            )
        )

        literals = [
            token
            for token in annotation_result.tokens
            if token.begin not in named_entity_char_positions
        ]

        annotation_result.literals = literals
