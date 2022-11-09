from typing import List

from enhanced_search.annotation import Query, Statement
from . import patterns


class AnnotationPatternAnalyser:
    """Handles Pattern Matching in query annotations."""

    patterns = [
        patterns.TaxonPropertyPattern(),
        patterns.TaxonNumericalPropertyPattern(),
    ]

    def get_annotation_context(self, query: Query) -> List[Statement]:
        """Searches for patterns in a given query and returns
        a list of context data. If no pattern matches the query, the resulting list
        is empty.

        The present patterns are iterated successively and a result is returned
        as soon as a pattern matches.
        """
        for pattern in self.patterns:
            context = pattern.match(query)
            if context:
                return context

        return []
