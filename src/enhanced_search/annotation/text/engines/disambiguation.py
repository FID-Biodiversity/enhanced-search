import re
from copy import deepcopy

from enhanced_search.annotation import Annotation, AnnotationResult, NamedEntityType
from enhanced_search.annotation.utils import replace_substring_between_positions


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
