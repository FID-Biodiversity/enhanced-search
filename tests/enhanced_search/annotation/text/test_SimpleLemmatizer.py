from dataclasses import dataclass
from typing import List, Optional
import pytest

from enhanced_search.annotation import AnnotationResult, Word


@dataclass
class Token:
    text: str
    lemma: Optional[str] = None


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
        ],
    )
    def test_parse(
        self, tokens: List[Token], expected_lemmas: List[str], simple_lemmatizer
    ):
        """Feature: Tokens are correctly lemmatized."""
        annotation_results = AnnotationResult(tokens=tokens)
        simple_lemmatizer.parse("foo", annotation_results)

        assert [token.lemma for token in annotation_results.tokens] == expected_lemmas
