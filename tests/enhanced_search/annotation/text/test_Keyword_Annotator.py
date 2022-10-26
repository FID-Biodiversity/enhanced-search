from typing import List

from enhanced_search.annotation.text import KeywordTextAnnotator
from enhanced_search.annotation.text.interface import Annotation


class TestKeywordAnnotator:
    def test_annotation(
        self,
        annotator: KeywordTextAnnotator,
        text: str,
        expected_annotations: List[Annotation],
    ):
        pass
