from typing import Union

from enhanced_search.annotation import Query, Uri, LiteralString, Annotation


def convert_query_to_abstracted_string(query: Query) -> str:
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
    annotated_query_string = query.original_string

    tokens = query.annotations + query.literals

    for token in sorted(
        tokens, key=lambda t: t.begin, reverse=True
    ):
        if isinstance(token, Annotation):
            substitution_text = f"{{{token.named_entity_type.value.lower()}" \
                                f"<{token.id}>}}"
        elif isinstance(token, LiteralString):
            substitution_text = f"{token.text}<{token.id}>"
        else:
            raise TypeError(f"The given token has type {type(token)}, "
                            f"while a Token is demanded!")

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
    If the uri already has brackets, the original string is returned. If the given
    string is not an URI (indicated by starting with "http"), the original string is
    returned too.
    If given a Uri object, it will be converted to its string representation without
    further escaping!
    If given a LiteralString, the unescaped text will be returned. If the text is a
    string, it will be quoted. If it is an integer, it will be annotated
    appropriately.
    """
    if isinstance(value, Uri):
        value = value.url
    if isinstance(value, LiteralString):
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
