from enhanced_search.annotation import AnnotationResult
from simplemma.langdetect import lang_detector


class SimpleLanguageDetector:
    """Simple language detection based on Simplemma.
    Only languages set in the `LANGUAGE_CODES_TO_CONSIDER` variable are considered.
    In the mentioned variable, you have to define language codes (e.g. "de" or "en").
    If the language cannot be determined, None will be the result.

    Simplemma Source: https://github.com/adbar/simplemma

    Obeys the AnnotatorEngine interface!
    """

    LANGUAGE_CODES_TO_CONSIDER = tuple(["de", "en"])
    UNKNOWN_LANGUAGE_STRING = "unk"

    def parse(self, text: str, annotation_result: AnnotationResult) -> None:
        """Tries to guess the language of the given text."""
        language_probabilities = lang_detector(
            text, lang=self.LANGUAGE_CODES_TO_CONSIDER
        )

        most_likely_language = language_probabilities[0]
        language_code = most_likely_language[0]
        if language_code != self.UNKNOWN_LANGUAGE_STRING:
            annotation_result.text_language = language_code
