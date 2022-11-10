import json
import re
from copy import deepcopy
from typing import Generator, Protocol

from enhanced_search.annotation import (
    Annotation,
    AnnotationResult,
    NamedEntityType,
    Uri, LiteralString,
)
from enhanced_search.databases import KeyValueDatabase

from ..utils import replace_substring_between_positions
from .dependencies import patterns
from .utils import (
    convert_annotation_string_to_named_entity_type,
    stream_words_from_query,
    tokenize_text,
    update_annotation_with_data,
)


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

    # This prevents strings of causing noise with little information
    STRING_BLACKLIST = {"l.", "(l.)", "R.", "&", "var.", "in"}

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
            lowered_word = word.lower()
            if begin < end_of_last_complete_named_entity or not self._is_word_valid(
                lowered_word
            ):
                continue

            corresponding_data = self._db.read(lowered_word)

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

    def _is_word_valid(self, word: str) -> bool:
        """Disapproves very short words (< 2 characters) and numerical strings,
        as well as words in the STRING_BLACKLIST."""
        return (
            not word.isnumeric() and len(word) > 2 and word not in self.STRING_BLACKLIST
        )


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


class PatternDependencyAnnotationEngine:
    """Inferences semantic relationships between Annotations and returns them
    as Statement.

    This AnnotationEngine relies on the fact that there already exists an
    Annotation list. The inferencing is done RegEx patterns.

    Obeys the AnnotatorEngine interface!
    """

    patterns = [
        patterns.TaxonPropertyPattern(),
        patterns.TaxonNumericalPropertyPattern(),
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


class LiteralAnnotationEngine:
    """Simply only puts all tokens that are not Annotations into a list.

    Obeys the AnnotatorEngine interface!
    """

    def parse(self, text: str, annotation_result: AnnotationResult) -> None:
        """Puts all tokens into a list."""

        annotation_by_start_index = {
            annotation.begin: annotation
            for annotation in annotation_result.named_entity_recognition
        }

        literals = []
        token_start = 0
        last_annotation_end = -1
        for token in tokenize_text(text):
            if (
                token_start not in annotation_by_start_index
                and token_start > last_annotation_end
            ):
                token_end = token_start + len(token)
                literal = LiteralString(begin=token_start, end=token_end, text=token)
                literals.append(literal)
            else:
                annotation = annotation_by_start_index.get(token_start)
                if annotation is not None:
                    last_annotation_end = annotation.end

            token_start += len(token) + 1

        annotation_result.literals = literals
