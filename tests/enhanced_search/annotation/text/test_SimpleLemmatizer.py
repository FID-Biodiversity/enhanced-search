from dataclasses import dataclass
from typing import List, Optional

import pytest

from enhanced_search.annotation import AnnotationResult, LiteralString


@dataclass
class Token(LiteralString):
    def __init__(self, text: str, lemma: Optional[str] = None):
        self.text = text
        self.lemma = lemma
        self.begin = 0
        self.end = 1


class TestSimpleLemmatizer:
    @pytest.mark.parametrize(
        ["tokens", "expected_lemmas"],
        [
            (
                [Token("Das"), Token("ist"), Token("ein"), Token("Test")],
                ["Das", "sein", "ein", "Test"],
            ),
            ([Token("Pflanze")], ["Pflanze"]),
            ([Token("Pflanzen")], ["Pflanze"]),
            ([Token("Fagus sylvatica")], ["Fagus sylvatica"]),
            ([Token("gelben"), Token("Blüten")], ["gelb", "Blüte"]),
        ],
    )
    def test_parse(
        self, tokens: List[Token], expected_lemmas: List[str], simple_lemmatizer
    ):
        """Feature: Tokens are correctly lemmatized."""
        annotation_results = AnnotationResult(tokens=tokens)  # type: ignore
        simple_lemmatizer.parse("foo", annotation_results)

        assert [token.lemma for token in annotation_results.tokens] == expected_lemmas
