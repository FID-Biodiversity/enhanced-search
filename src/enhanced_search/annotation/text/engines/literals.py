from enhanced_search.annotation import AnnotationResult, LiteralString

from ..utils import tokenize_text


class LiteralAnnotationEngine:
    """Simply only puts all tokens that are not Annotations into a list.

    Obeys the AnnotatorEngine interface!
    """

    def parse(self, text: str, annotation_result: AnnotationResult) -> None:
        """Puts all tokens into a list."""

        annotation_by_start_index = {
            annotation.begin: annotation
            for annotation in annotation_result.named_entity_recognition
        }

        literals = []
        token_start = 0
        last_annotation_end = -1
        for token in tokenize_text(text):
            if (
                token_start not in annotation_by_start_index
                and token_start > last_annotation_end
            ):
                token_end = token_start + len(token)
                literal = LiteralString(begin=token_start, end=token_end, text=token)
                literals.append(literal)
            else:
                annotation = annotation_by_start_index.get(token_start)
                if annotation is not None:
                    last_annotation_end = annotation.end

            token_start += len(token) + 1

        annotation_result.literals = literals
