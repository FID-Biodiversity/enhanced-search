""" Contains all patterns to match the annotations of a text string.
I went with classes instead of simple RegEx statements, since classes allow
for further internal manipulation of the output. A procedure that is not
necessary in all patterns, but is useful in some (e.g. in situation, where there is
negation).

To allow ambiguity in an annotation (e.g. a word is recognized both as plant and as a
location, the pattern matching has to catch cases like:
    "{plant} in {plant|location}"
Hence, all patterns should apply ".*?" within the curly brackets
(i.e. "{.*?(?:taxon|plant|animal).*?}"), to consider this variability.

For testing the regex, you can use: https://regex101.com/
"""

import re
from abc import ABC
from re import Match as RegexMatch
from re import Pattern as RegexPattern
from typing import List, Optional

from enhanced_search.annotation import Annotation, LiteralString, Statement
from enhanced_search.annotation.utils import convert_text_to_abstracted_string


class Pattern(ABC):
    """A base class that allows the matching of text strings."""

    regex_pattern: RegexPattern = None

    def match(
        self, text: str, annotations: List[Annotation], literals: List[LiteralString]
    ) -> List[Statement]:
        """Checks the given text, if it fits the internal pattern.
        Returns a list of dictionaries, each holding context data of a single
        match within the text. If no match was found, the list is empty.
        """
        abstracted_matching_string = convert_text_to_abstracted_string(
            text, annotations, literals
        )
        matches = self.regex_pattern.search(abstracted_matching_string)

        return compile_result(matches, annotations, literals)


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


def compile_result(
    matches: Optional[RegexMatch],
    annotations: List[Annotation],
    literals: List[LiteralString],
) -> List[Statement]:
    """Uses the group names of the matches to generate a dict with all URI data.
    The group names are used as keys. The value of the group should be that of
    an Annotation ID. This way, the necessary Annotation is retrieved and added as
    value.
    """
    if matches is None:
        return []

    words = annotations + literals
    word_index = {word.id: word for word in words}

    context = []
    statement = Statement()
    for name, word_id in matches.groupdict().items():
        word = word_index.get(word_id)

        if isinstance(word, Annotation):
            value = word.uris
        else:
            value = word

        statement.__dict__[name] = value

    context.append(statement)

    return context
