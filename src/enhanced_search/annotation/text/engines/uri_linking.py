import json

from enhanced_search.annotation import Annotation, AnnotationResult, Uri
from enhanced_search.databases import KeyValueDatabase

from ..utils import convert_annotation_string_to_named_entity_type


class UriLinkerAnnotatorEngine:
    """Associates Annotations with their respective URIs.
    The association is done purely on a string base and not disambiguated.
    The URIs are retrieved from a KeyValueDatabase.

    Obeys the AnnotatorEngine interface!
    """

    def __init__(self, db: KeyValueDatabase):
        self._db = db

    def parse(self, text: str, annotation_result: AnnotationResult) -> None:
        """Adds URIs from a database to each annotation, if possible.
        The URIs are NOT directly added to the annotations, but stored separately!

        The `text` parameter is not needed but required for interface-compliance.
        """

        if annotation_result.named_entity_recognition is None:
            raise ValueError("No annotation data is provided!")

        linked_uri_data = {}
        for annotation in annotation_result.named_entity_recognition:
            corresponding_data = self._db.read(annotation.text.lower())

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
        for named_entity_type_string, uri_data_list in annotation_data.items():
            uris = {
                Uri(url=uri, position_in_triple=position)
                for uri, position in uri_data_list
            }

            is_updated = self._add_to_dict_if_ne_type_fits(
                annotation, named_entity_type_string, uris, linked_uri_data
            )

            if not is_updated:
                for ambiguity in annotation.ambiguous_annotations:
                    self._add_to_dict_if_ne_type_fits(
                        ambiguity, named_entity_type_string, uris, linked_uri_data
                    )

    @staticmethod
    def _add_to_dict_if_ne_type_fits(
        ann: Annotation, processed_ne_type: str, uri_list: set, linked_uri_data: dict
    ) -> bool:
        if ann.named_entity_type == convert_annotation_string_to_named_entity_type(
            processed_ne_type
        ):
            linked_uri_data[ann] = uri_list
            return True

        return False
