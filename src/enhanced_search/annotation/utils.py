"""Some handy methods that are useful in several places within the package."""

from typing import List, Union

from enhanced_search.annotation import Annotation, LiteralString, Uri
from enhanced_search.utils import escape_characters


def convert_text_to_abstracted_string(
    text: str, annotations: List[Annotation], literals: List[LiteralString]
) -> str:
    """Creates a abstracted version of the original query string.
    The abstraction is depending on the annotations and the literals.
    If no annotation is given in the query, the original string will be returned.
    Example:
        Query string: "I am looking for Fagus sylvatica in Germany"
        Annotations: ["Fagus sylvatica" = Plant, "Germany" = Location]
        Literals: ["I", "am", "looking", "for", "in"]
        Resulting string:
        "I<342dd2> am<4653f4> looking<3f43f> for<23ff3d> {plant<d7d6fs>}
        in<4vk8e> {location<d97dsc3>}"
    The hash in the <> is the ID of the respective Annotation/LiteralString
    for reference.
    """
    annotated_query_string = text

    tokens = annotations + literals

    for token in sorted(tokens, key=lambda t: t.begin, reverse=True):
        if isinstance(token, Annotation):
            text = (
                token.named_entity_type.value.lower()
                if token.named_entity_type is not None
                else token.text
            )
            substitution_text = f"{{{text}" f"<{token.id}>}}"
        elif isinstance(token, LiteralString):
            substitution_text = f"{token.text}<{token.id}>"
        else:
            raise TypeError(
                f"The given token has type {type(token)}, "
                f"while a Token is demanded!"
            )

        annotated_query_string = replace_substring_between_positions(
            original_text=annotated_query_string,
            substituting_text=substitution_text,
            begin=token.begin,
            end=token.end,
        )

    return annotated_query_string


def replace_substring_between_positions(
    original_text: str, substituting_text: str, begin: int, end: int
) -> str:
    """Replaces a text's substring by a given substring between two positions.
    :param original_text: The text that should change.
    :param substituting_text: The text that should be inserted.
    :param begin: The first character position in the original_text.
    :param end: The last character position in the original_text.
    :return: The manipulated string.
    """
    return "".join(
        (
            original_text[:begin],
            substituting_text,
            original_text[end:],
        )
    )


def prepare_value_for_sparql(value: Union[str, Uri, LiteralString]) -> str:
    """Prepares a given dataclass for insertion into a SPARQL query string.
    Adds "<" and ">" to an URI at start and end, respectively.
    If the URI already has brackets, the original string is returned. If the given
    string is not an URI (indicated by starting with "http"), the original string is
    returned too.
    If given a LiteralString, the text will be returned. If the text is a
    string, it will be quoted. If it is an integer, it will be annotated
    appropriately.
    The method acknowledges the `is_safe` flag. If this flag is True, the string
    will not be escaped. Otherwise, the string is escaped appropriate for a
    sane SPARQL query.
    """
    if isinstance(value, str):
        value = escape_sparql_input_string(value)

    elif isinstance(value, Uri):
        if not value.is_safe:
            value = escape_sparql_input_string(value.url)
        else:
            value = value.url
    elif isinstance(value, LiteralString):
        if not value.is_safe:
            original_text = escape_sparql_input_string(value.text)
        else:
            original_text = value.text

        text = f'"{original_text}"'
        if original_text.isnumeric():
            text = f"{text}^^<http://www.w3.org/2001/XMLSchema#integer>"

        return text

    if not value.startswith("http"):
        return value
    if not value.startswith("<"):
        return f"<{value}>"
    return value


def escape_sparql_input_string(text: str) -> str:
    """Escapes any potential malicious character in a text.

    Characters malicious for SPARQL databases:
        * Single quotation
        * Double quotation
        * Hashtags (currently left out)
        * Greater than sign (">")
        * Less than sign ("<")
    """

    characters = ("'", '"', "<", ">")
    return escape_characters(text, characters)
