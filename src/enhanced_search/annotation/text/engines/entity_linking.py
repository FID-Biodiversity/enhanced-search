"""Provides AnnotationEngines for linking Named Entities with their respective URI."""

import json
from typing import Optional

from enhanced_search.annotation import Annotation, AnnotationResult, Uri
from enhanced_search.annotation.text.utils import (
    convert_annotation_string_to_named_entity_type,
    get_word_text_and_lemma_set,
)
from enhanced_search.databases.key_value import KeyValueDatabase


class UriLinkerAnnotatorEngine:
    """Associates Annotations with their respective URIs.
    The association is done purely on a string base and not disambiguated.
    The URIs are retrieved from a KeyValueDatabase.

    The data is stored in the `entity_linking` of the AnnotationResult.
    The data is a dict with the Annotation IDs as keys. The value is
    a dict with the NamedEntityTypes of the Annotation with the respective
    URIs as values. This approach allows ambiguous Annotation resolution.

    Example:
         {
            "Annotation-ID-1": {
                "NamedEntityType.PLANT": {URI1, URI2, URI3},
                "NamedEntityType.LOCATION": {URI1},
            },
            "Annotation-ID-2": {
                "NamedEntityType.ANIMAL": {URI1, URI2}
            }
         }

    Obeys the AnnotatorEngine interface!
    """

    def __init__(self, db: KeyValueDatabase):
        self._db = db

    def parse(self, _: str, annotation_result: AnnotationResult) -> None:
        """Adds URIs from a database to each annotation, if possible.
        The URIs are NOT directly added to the annotations, but stored separately!

        The `text` parameter is not needed but required for interface-compliance.
        """

        if annotation_result.named_entity_recognition is None:
            raise ValueError("No annotation data is provided!")

        linked_uri_data: dict = {}
        for annotation in annotation_result.named_entity_recognition:
            corresponding_data = self._get_data_for_annotation_text(annotation)

            if corresponding_data is not None:
                annotation_data = json.loads(corresponding_data)

                self._update_linked_uri_data(
                    linked_uri_data, annotation, annotation_data
                )

        annotation_result.entity_linking = linked_uri_data

    def _update_linked_uri_data(
        self, linked_uri_data: dict, annotation: Annotation, annotation_data: dict
    ) -> None:
        """Updates the URI data, if the annotation or any of its ambiguities fits."""
        update_uri_data = {}
        for named_entity_type_string, uri_data_list in annotation_data.items():
            uris = {
                Uri(url=uri, position_in_triple=position)
                for uri, position in uri_data_list
            }

            normalized_ne_string = convert_annotation_string_to_named_entity_type(
                named_entity_type_string
            )

            update_uri_data[normalized_ne_string] = uris

        linked_uri_data[annotation.id] = update_uri_data

    def _get_data_for_annotation_text(self, annotation: Annotation) -> Optional[str]:
        for test_string in get_word_text_and_lemma_set(annotation):
            corresponding_data = self._db.read(test_string.lower())
            if corresponding_data is not None:
                return corresponding_data

        return None
