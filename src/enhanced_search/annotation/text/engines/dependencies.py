"""Provides AnnotationEngines for deducing word dependencies in a text."""

import re
from abc import ABC
from re import Match as RegexMatch
from re import Pattern as RegexPattern
from typing import List, Optional

from enhanced_search.annotation import (
    Annotation,
    AnnotationResult,
    LiteralString,
    RelationshipType,
)
from enhanced_search.annotation.utils import convert_text_to_abstracted_string


class Pattern(ABC):
    """All patterns to match the annotations of a text string.
    I went with classes instead of simple RegEx statements, since classes allow
    for further internal manipulation of the output. A procedure that is not
    necessary in all patterns, but is useful in some (e.g. in situation, where there is
    negation).

    To allow ambiguity in an annotation (e.g. a word is recognized both as plant and
    as a location, the pattern matching has to catch cases like:
        "{plant} in {plant|location}"
    Hence, all patterns should apply ".*?" within the curly brackets
    (i.e. "{.*?(?:taxon|plant|animal).*?}"), to consider this variability.

    For testing the regex, you can use: https://regex101.com/
    """

    regex_pattern: Optional[RegexPattern] = None
    additional_data: dict = {}

    def match(
        self, text: str, annotations: List[Annotation], literals: List[LiteralString]
    ) -> List[dict]:
        """Checks the given text, if it fits the internal pattern.
        Returns a list of dictionaries, each holding context data of a single
        match within the text. If no match was found, the list is empty.
        """
        if self.regex_pattern is None:
            raise NotImplementedError(
                "You did not provide a `regex_pattern` variable for this class!"
            )

        abstracted_matching_string = convert_text_to_abstracted_string(
            text, annotations, literals
        )
        matches = self.regex_pattern.search(abstracted_matching_string)

        additional_data = self.additional_data

        return compile_result(matches, **additional_data)


class OnlyTaxonPattern(Pattern):
    """Matching text examples:

    * "Fagus"
    * "Fagus sylvatica"
    """

    regex_pattern = re.compile(r"{.*?(?:taxon|plant|animal)<(?P<taxon>.*?)>}")


class SimpleTaxonLocationPattern(Pattern):
    """Matching text examples:

    * "Fagus Deutschland"
    * "Fagus in Deutschland"
    * "Fagus in New Zealand"
    """

    regex_pattern = re.compile(
        r"{.*?(?:taxon|plant|animal)<(?P<taxon>.*?)>} +(?:in +)?"
        r"{.*?location<(?P<location>.*?)>}"
    )


class TaxonPropertyPattern(Pattern):
    """Matching text examples:

    * "Pflanzen mit roten Blüten"
    * "Plant with red flowers"
    * "Plant red flowers"
    """

    regex_pattern = re.compile(
        r"{.*?(?:taxon|plant|animal)<(?P<subject>.+?)>} +(?:mit<.+?> +|with<.+?> +)?"
        r"{.*?miscellaneous<(?P<object>.+?)>} +"
        r"{.*?miscellaneous<(?P<predicate>.+?)>}"
    )


class TaxonNumericalPropertyPattern(Pattern):
    """Matching text examples:

    * "Pflanzen mit 3 Kelchblättern"
    * "Plant with 3 petals"
    * "Plant 3 petals"
    """

    regex_pattern = re.compile(
        r"{.*?(?:taxon|plant|animal)<(?P<subject>.+?)>} +(?:mit<.+?> +|with<.+?> +)?"
        r"[0-9]+<(?P<object>.+?)> +"
        r"{.*?miscellaneous<(?P<predicate>.+?)>}"
    )


class AndConjunctionPattern(Pattern):
    """Recognizes AND-conjuncted terms."""

    regex_pattern = re.compile(
        r"\S+<(?P<subject>.+?)>}? (?:und<.+?>|and<.+?>) \S+<(?P<object>.+?)>"
    )
    additional_data = {"relationship": RelationshipType.AND}


class OrConjunctionPattern(Pattern):
    """Recognize OR-conjuncted terms."""

    regex_pattern = re.compile(
        r"\S+<(?P<subject>.+?)>}? (?:oder<.+?>|or<.+?>) \S+<(?P<object>.+?)>"
    )
    additional_data = {"relationship": RelationshipType.OR}


class PatternDependencyAnnotationEngine:
    """Inferences semantic relationships between Annotations and returns them
    as Statement.

    This AnnotationEngine relies on the fact that there already exists an
    Annotation list. The inferencing is done RegEx patterns.

    Obeys the AnnotatorEngine interface!
    """

    patterns = [
        TaxonPropertyPattern(),
        TaxonNumericalPropertyPattern(),
        AndConjunctionPattern(),
        OrConjunctionPattern(),
    ]

    def parse(self, text: str, annotation_result: AnnotationResult) -> None:
        """Searches for patterns in a given query and returns
        a list of context data. If no pattern matches the query, the resulting list
        is empty.

        The present patterns are iterated successively and a result is returned
        as soon as a pattern matches.
        """
        statements = []

        for pattern in self.patterns:
            statements = pattern.match(
                text=text,
                annotations=annotation_result.named_entity_recognition,
                literals=annotation_result.literals,
            )
            if statements:
                break

        annotation_result.annotation_relationships = statements


def compile_result(matches: Optional[RegexMatch], **kwargs) -> List[dict]:
    """Uses the group names of the matches to generate a dict with all URI data.
    The group names are used as keys. The value of the group is that of
    an Annotation ID.
    """
    if matches is None:
        return []

    context = []
    statement = {}
    for name, word_id in matches.groupdict().items():
        statement[name] = word_id

    for name, value in kwargs.items():
        statement[name] = value

    context.append(statement)

    return context
