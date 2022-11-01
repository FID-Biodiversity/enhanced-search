import json
import shlex
from copy import deepcopy
from typing import Generator, Tuple

from enhanced_search import configuration as config
from enhanced_search.annotation.text.data import NamedEntityType, Annotation

named_entity_mapping = {
    config.PLANT_ANNOTATION_STRING.lower(): NamedEntityType.PLANT,
    config.ANIMAL_ANNOTATION_STRING.lower(): NamedEntityType.ANIMAL,
    config.LOCATION_ANNOTATION_STRING.lower(): NamedEntityType.LOCATION,
    "plant": NamedEntityType.PLANT,
    "animal": NamedEntityType.ANIMAL,
    "location": NamedEntityType.LOCATION,
    "taxon": NamedEntityType.TAXON,
}


def convert_annotation_string_to_named_entity_type(
    annotation_string: str,
) -> NamedEntityType:
    """Takes a string (e.g. "Plant_Flora") and retrieves the corresponding
    NamedEntityType.
    """
    number_of_expected_named_entity_types = 4

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


def stream_words_from_query(text: str) -> Generator[Tuple[str, int, int], None, None]:
    """Returns substrings of the given query in a deterministic order.
    Characters like question marks (?) and exclamation marks (!) are removed from a
    returned word. The word are returned with its original case, no general lower
    casing.
    """
    tokens = shlex.split(text)  # Splits on whitespace, but preserves quotations
    strip_characters = "?! "

    current_start_position = 0
    for index, starting_token in enumerate(tokens):
        text = starting_token.strip(strip_characters)

        token_length = len(text)
        current_end_position = current_start_position + token_length

        yield text, current_start_position, current_end_position

        for extending_token in tokens[index + 1 :]:
            extending_token = extending_token.strip(strip_characters)
            text = " ".join((text, extending_token))
            current_end_position += len(extending_token) + 1  # +1: Added whitespace

            yield text, current_start_position, current_end_position

        current_start_position += token_length + 1


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
    for named_entity_type_string, data in sorted(
        json_data.items(), key=lambda item: sort_named_entities_by_priority(item[0])
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
