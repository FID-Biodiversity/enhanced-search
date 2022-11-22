"""Some handy methods that are shared between multiple moduless."""

import json
import shlex
from copy import deepcopy
from typing import Generator, List, Set, Tuple

from enhanced_search import configuration as config
from enhanced_search.annotation import Annotation, NamedEntityType, Word

named_entity_mapping = {
    config.PLANT_ANNOTATION_STRING.lower(): NamedEntityType.PLANT,
    config.ANIMAL_ANNOTATION_STRING.lower(): NamedEntityType.ANIMAL,
    config.LOCATION_ANNOTATION_STRING.lower(): NamedEntityType.LOCATION,
    config.MISC_ANNOTATION_STRING.lower(): NamedEntityType.MISCELLANEOUS,
    "plant": NamedEntityType.PLANT,
    "animal": NamedEntityType.ANIMAL,
    "location": NamedEntityType.LOCATION,
    "taxon": NamedEntityType.TAXON,
    "misc": NamedEntityType.MISCELLANEOUS,
}


def convert_annotation_string_to_named_entity_type(
    annotation_string: str,
) -> NamedEntityType:
    """Takes a string (e.g. "Plant_Flora") and retrieves the corresponding
    NamedEntityType.
    """
    number_of_expected_named_entity_types = 5

    if len(NamedEntityType) != number_of_expected_named_entity_types:
        raise LookupError(
            "The NamedEntityType class has not the expected number of types. "
            "Hence, the mapping needs to be updated!"
        )

    lowered_annotation_string = annotation_string.lower()
    named_entity_type = named_entity_mapping.get(lowered_annotation_string)

    if named_entity_type is None:
        raise TypeError(
            f"The given string {annotation_string} does not correspond to any "
            f"Named Entity Type!"
        )

    return named_entity_type


named_entity_priority = [
    convert_annotation_string_to_named_entity_type(annotation_string)
    for annotation_string in config.ANNOTATION_PRIORITY
]


def sort_named_entities_by_priority(named_entity_type_string: str) -> int:
    """A custom sorting algorithm for NamedEntityTypes."""

    return named_entity_priority.index(
        convert_annotation_string_to_named_entity_type(named_entity_type_string)
    )


def tokenize_text(text: str, keep_quotations: bool = False) -> List[str]:
    """Splits a given text by whitespaces, but preserves quoted strings."""
    return shlex.split(text, posix=not keep_quotations)


def stream_words_from_tokens(
    tokens: List[Word],
) -> Generator[Tuple[str, int, int], None, None]:
    """Returns strings by concatenating the given tokens in a deterministic order.

    Characters like question marks (?) and exclamation marks (!) are removed from a
    returned word. The words are returned with its original case, no general lower
    casing.

    A token is tested for both its text and its lemma. If both are the same, only one
    is applied.

    Returns:
        A tuple holding a concatenated string, the beginning position and the end
        position - in this order.
    """
    for index, token in enumerate(tokens):
        token_strings = get_word_text_and_lemma_set(token)

        for text in token_strings:
            yield text, token.begin, token.end

            for extending_token in tokens[index + 1 :]:
                text += f" {extending_token.text}"
                yield text, token.begin, extending_token.end


def get_word_text_and_lemma_set(word: Word) -> Set[str]:
    """Creates a set holding both text and lemma of the given word.
    Guarantees to not contain None as value.
    """
    return {string for string in {word.text, word.lemma} if string is not None}


def update_annotation_with_data(
    annotation: Annotation, json_string_data: str
) -> Annotation:
    """Updates the given Annotation with the given data.
    Example data:
        '{"Plant_Flora":
        [["https://www.biofid.de/bio-ontologies/Tracheophyta#GBIF_2874875", 3]
        ]}'

    The data follows this schema:
        {named_entity_type1: [[uri_string1, position_in_a_triple], ...],
        named_entity_type2: [[uri_string2, position_in_a_triple]
        ...}
    """
    json_data = json.loads(json_string_data)

    original_annotation = annotation
    counter = 0
    for named_entity_type_string in sorted(
        json_data.keys(),
        key=lambda item_key: sort_named_entities_by_priority(item_key),
    ):
        if counter != 0:
            annotation = deepcopy(original_annotation)

        annotation.named_entity_type = convert_annotation_string_to_named_entity_type(
            named_entity_type_string
        )

        if counter != 0:
            original_annotation.ambiguous_annotations.add(annotation)

        counter += 1

    return original_annotation
