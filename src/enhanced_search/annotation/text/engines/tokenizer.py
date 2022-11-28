"""Provides AnnotationEngines for tokenizing a given text."""

from typing import List

from enhanced_search.annotation import AnnotationResult, LiteralString, Word
from enhanced_search.annotation.text.utils import tokenize_text


class SimpleTokenizer:
    """A very simple tokenizing AnnotationEngine.

    Splits on any whitespace, expect if there is a quotation. Quotations are not split!
    The quotation marks remain on the token!

    Obeys the AnnotatorEngine interface!
    """

    def parse(self, text: str, annotation_result: AnnotationResult) -> None:
        """Tokenizes the given text and adds it to the AnnotationResult."""
        tokens = tokenize_text(text, keep_quotations=True)
        tokens = self._filter_tokens(tokens)
        words = tokens_to_literal_string_objects(tokens, text)

        annotation_result.tokens = words

    def _filter_tokens(self, tokens: List[str]) -> List[str]:
        filters = [remove_punctuation_marks]

        updated_tokens = []
        for token in tokens:
            for f in filters:
                token = f(token)
            updated_tokens.append(token)

        return updated_tokens


def remove_punctuation_marks(token: str) -> str:
    """Removes question marks, exclamation marks etc. at the beginning
    or end of a token.
    """
    return token.strip("!?;")


def tokens_to_literal_string_objects(
    tokens: List[str], text: str
) -> List[LiteralString]:
    """Converts a list of strings to a list of LiteralStrings.
    All tokens in the list have to exist in the given text!
    """
    literals = []
    last_end = 0
    for token in tokens:
        token_start = text.index(token, last_end)
        last_end = token_start + len(token)
        literal = LiteralString(begin=token_start, end=last_end, text=token)
        word_quotation_check(literal)
        literals.append(literal)

    return literals


def word_quotation_check(word: Word) -> None:
    """Checks for a word, if it is quoted in the original text.
    Also strips the quotation from the word's text.
    """
    quotation_characters = ('"', "'", '\\"', "\\'")

    text = word.text

    word.is_quoted = text.startswith(quotation_characters) and text.endswith(
        quotation_characters
    )
    word.text = text.strip("".join(quotation_characters))
