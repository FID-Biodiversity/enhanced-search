import pytest

from enhanced_search.annotation import AnnotationResult


class TestSimpleLanguageDetector:
    @pytest.mark.parametrize(
        ["text", "expected_language"],
        [
            ("Ich suche Bäume!", "de"),
            ("I am searching trees!", "en"),
            ("Fagus sylvatica", None),
            ("Eulen Berlin", "de"),
            ("Owls Berlin", "en"),
            ("Fagus in Frankfurt", None),
        ]
    )
    def test_parse(self, text, expected_language, simple_language_detector):
        annotation_result = AnnotationResult()
        simple_language_detector.parse(text, annotation_result)

        assert annotation_result.text_language == expected_language
