import json
import re
from copy import deepcopy
from typing import Protocol

from enhanced_search.annotation import (
    AnnotationResult,
    Annotation,
    Uri, NamedEntityType,
)
from enhanced_search.databases import KeyValueDatabase
from .utils import (
    stream_words_from_query,
    update_annotation_with_data,
    convert_annotation_string_to_named_entity_type,
)
from ..utils import replace_substring_between_positions


class AnnotationEngine(Protocol):
    """An interface class for all classes that interact with the
    TextAnnotator.
    """

    def parse(self, text: str, annotations: AnnotationResult) -> None:
        """Provide the text and the current state (the AnnotationResult) of
        the annotations to this AnnotationEngine.
        The method updates the AnnotationResult object.
        """


class StringBasedNamedEntityAnnotatorEngine:
    """Annotates all NamedEntities on a string base. The annotation is done
    purely by a string comparison.
    No further semantics are extracted. Hence, URIs are NOT linked to the respective
    Annotation object. For adding URIs, parse the Annotation to an URI-Linker.

    Obeys the AnnotatorEngine interface!
    """

    def __init__(self, db: KeyValueDatabase):
        self._db = db

    def parse(self, text: str, annotations: AnnotationResult) -> None:
        """Provide the text and the current state (the AnnotationResult) of
        the annotations to this AnnotationEngine.
        The method updates the AnnotationResult object.
        """
        previous_token_data = None
        retrieved_annotations = []
        end_of_last_complete_named_entity = 0

        for word, begin, end in stream_words_from_query(text):
            if begin < end_of_last_complete_named_entity:
                continue

            corresponding_data = self._db.read(word.lower())

            if corresponding_data is not None:
                previous_token_data = (begin, end, word, corresponding_data)
            elif previous_token_data is not None:
                ann = self._create_annotation(*previous_token_data)
                retrieved_annotations.append(ann)

                end_of_last_complete_named_entity = previous_token_data[1]
                previous_token_data = None
        else:
            # The for-loop is done! Clean up any remaining annotations!
            if previous_token_data is not None:
                ann = self._create_annotation(*previous_token_data)
                retrieved_annotations.append(ann)

        annotations.named_entity_recognition = retrieved_annotations

    def _create_annotation(self, begin: int, end: int, word: str, annotation_data: str):
        annotation = Annotation(begin=begin, end=end, text=word)
        update_annotation_with_data(annotation, annotation_data)
        return annotation


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


class DisambiguationAnnotationEngine:
    """If present, resolves ambiguity in an Annotation.

    The updated Annotation objects are added separately. The original Annotation is NOT
    overwritten!

    Obeys the AnnotatorEngine interface!
    """

    regex_query_for_location = re.compile(r".* in .*?{location}")

    def parse(self, text: str, annotation_result: AnnotationResult) -> None:
        """Adds a dataset set to the AnnotationResult with disambiguated Annotations.
        Currently, this is only handling ambiguity for locations.
        """
        disambiguated_annotations = {}

        # TODO: This can be done nicer than with if-else!
        for annotation in annotation_result.named_entity_recognition:
            for ann in annotation.ambiguous_annotations:
                if self.is_location(ann, text):
                    disambiguated_annotations[annotation] = ann
                else:
                    # No pattern applies, hence the current annotation is used!
                    updated_annotation = deepcopy(annotation)
                    updated_annotation.ambiguous_annotations.clear()
                    disambiguated_annotations[annotation] = updated_annotation

        annotation_result.disambiguated_annotations = disambiguated_annotations

    def is_location(self, annotation: Annotation, text: str) -> bool:
        """Checks if the given ambitious annotation is a location."""
        if not annotation.named_entity_type == NamedEntityType.LOCATION:
            return False

        abstracted_text = replace_substring_between_positions(
            original_text=text,
            substituting_text="{location}",
            begin=annotation.begin,
            end=annotation.end,
        )

        matches = self.regex_query_for_location.match(abstracted_text)

        return matches is not None
