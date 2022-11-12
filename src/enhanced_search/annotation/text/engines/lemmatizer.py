import simplemma

from enhanced_search.annotation import AnnotationResult


class SimpleLemmatizer:
    """A Lemmatizer building on the Simplemma package.

    Simplemma uses a dictionary approach to lemmatize words in various languages.
    Source: https://github.com/adbar/simplemma

    If no language is given in the AnnotationResult, the fallback is German ('de').

    Obeys the AnnotatorEngine interface!
    """

    DEFAULT_LANGUAGE = "de"

    def parse(self, text: str, annotation_result: AnnotationResult) -> None:
        """Add a lemma to the each Annotations."""
        for token in annotation_result.tokens:
            token.lemma = simplemma.lemmatize(
                token.text, lang=self.DEFAULT_LANGUAGE
            )
            i = 1
