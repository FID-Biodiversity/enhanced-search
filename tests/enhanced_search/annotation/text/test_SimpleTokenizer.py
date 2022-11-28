import pytest

from enhanced_search.annotation import AnnotationResult


class TestSimpleTokenizer:
    @pytest.mark.parametrize(
        ["text", "expected_tokens"],
        [
            ("Das ist ein Test!", ["Das", "ist", "ein", "Test"]),
            ("Ich suche 'Fagus sylvatica'", ["Ich", "suche", "Fagus sylvatica"]),
            (
                "Fagus sylvatica f. pendula (Lodd.) Dippel",
                ["Fagus", "sylvatica", "f.", "pendula", "(Lodd.)", "Dippel"],
            ),
        ],
    )
    def test_parse(self, text, expected_tokens, tokenizer, annotation_result):
        tokenizer.parse(text, annotation_result)
        assert [token.text for token in annotation_result.tokens] == expected_tokens

    @pytest.mark.parametrize(
        ["text", "is_quoted"],
        [
            ("Das ist ein Test!", [False, False, False, False]),
            ("Ich suche 'Fagus sylvatica'", [False, False, True]),
            ("'Fagus sylvatica' is great!", [True, False, False]),
        ],
    )
    def test_token_is_marked_as_quoted(
        self, text, is_quoted, tokenizer, annotation_result
    ):
        tokenizer.parse(text, annotation_result)
        assert [token.is_quoted for token in annotation_result.tokens] == is_quoted

    @pytest.mark.parametrize(
        ["text", "begins", "ends"],
        [
            ("Das ist ein Test!", [0, 4, 8, 12], [3, 7, 11, 16]),
            (
                "Ich suche 'Fagus sylvatica'    in  Hessen",
                [0, 4, 10, 31, 35],
                [3, 9, 27, 33, 41],
            ),
        ],
    )
    def test_token_has_correct_start_and_end(
        self, text, begins, ends, tokenizer, annotation_result
    ):
        tokenizer.parse(text, annotation_result)
        assert [token.begin for token in annotation_result.tokens] == begins
        assert [token.end for token in annotation_result.tokens] == ends

    @pytest.fixture(scope="session")
    def tokenizer(self, simple_tokenizer):
        return simple_tokenizer

    @pytest.fixture
    def annotation_result(self):
        return AnnotationResult()
