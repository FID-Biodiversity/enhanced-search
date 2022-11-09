from typing import Set, Optional, List, Union

from enhanced_search.annotation import Query, Feature, Uri, Statement, LiteralString
from enhanced_search.annotation.analyzers import AnnotationPatternAnalyser
from enhanced_search.annotation.text import TextAnnotator
from enhanced_search.factories import SemanticEngineFactory


class SemanticQueryProcessor:
    """Orchestrates the semantic enrichment of a Query object.

    The SemanticQueryProcessor will use a TextAnnotator object to annotate any query
    object.
    If provided the name of a SemanticEngine class, the SemanticQueryProcessor will
    use Annotations of a Query, potentially inference data and further enrich the
    Annotations in the Query. If this process involves calling a database, this will
    be done automatically by the SemanticEngine.
    """

    def __init__(
        self,
        semantic_engine_name: str = None,
        text_annotator: TextAnnotator = None,
    ):
        self.text_annotator = text_annotator
        self.semantic_engine_name = semantic_engine_name

    def annotate(self, query: Query) -> None:
        """Adds further semantic data to the given query.
        The query object is updated in-place!
        """
        query.annotations = self.text_annotator.annotate(query.original_string)

    def resolve_query_annotations(self, query: Query) -> None:
        """Adds further data to the annotations of the query.
        This is e.g. inferencing URIs of Annotations, if necessary (i.e. querying
        URIs of Annotation features like "plants with red flowers").
        If the inferencing is successful, and there are URIs in the database fitting
        the criteria, the received URIs are updating the Annotations uris. The original
        URI(s) for this annotation
        """
        annotation_pattern_analyser = AnnotationPatternAnalyser()
        query.statements = annotation_pattern_analyser.get_annotation_context(query)

        engine_factory = SemanticEngineFactory()
        semantic_engine = engine_factory.create(self.semantic_engine_name)
        additional_annotation_data = semantic_engine.generate_query_semantics(query)

        update_annotation_features(additional_annotation_data, query.statements)

        update_query(query)


def update_annotation_features(
    annotation_data: dict, statements: List[Statement]
) -> None:
    """Adds the enriched annotation data to the respective Annotations.
    This updates the Annotation's features (if appropriate), where a Feature is
    composed of the data of the other Annotations in the same query. Furthermore,
    the Annotation's URIs are updated with retrieved URIs (if any).
    """
    for annotation, uris in annotation_data.items():
        feature = create_feature_from_uris(annotation.uris)

        if feature is not None:
            annotation.features.append(feature)

        relevant_statements = [
            statement
            for statement in statements
            if statement.subject == annotation.uris
        ]

        for statement in relevant_statements:
            statement_object = statement.object
            feature = create_feature_from_uris(statement_object)

            if feature is None:
                feature = create_feature_from_uris(statement.predicate)
                if statement_object is not None:
                    feature.value = statement_object
            else:
                feature.property = statement.predicate

            if feature is not None:
                annotation.features.append(feature)

        annotation.uris = set(uris)


def update_query(query: Query) -> None:
    """Updates the internal consistency of the Query object.
    This method removes all Annotations that were assigned to be Features of another
    Annotation.
    """

    features = tuple(
        feature
        for annotation in query.annotations
        for feature in annotation.features
    )

    def freeze_key(set_to_freeze: Union[Set[Uri], Uri]) -> tuple:
        if isinstance(set_to_freeze, Uri):
            return Uri,  # tuple
        else:
            return tuple(sorted(set_to_freeze, key=lambda a: a.url))

    uri_to_annotation_index = {
        freeze_key(annotation.uris): annotation
        for annotation in query.annotations
    }

    annotations_to_remove = set()
    literals_to_remove = set()
    for feature in features:
        for attr in [feature.property, feature.value]:
            if attr is not None and isinstance(attr, (set, Uri)):
                ann = uri_to_annotation_index.get(freeze_key(attr))
                if ann is not None:
                    annotations_to_remove.add(ann)
            elif isinstance(attr, LiteralString):
                literals_to_remove.add(attr)

    for annotation in annotations_to_remove:
        query.annotations.remove(annotation)

    for literal in literals_to_remove:
        query.literals.remove(literal)


def create_feature_from_uris(uris: Set[Uri]) -> Optional[Feature]:
    """Creates a Feature object from the given URIs."""
    if not uris or isinstance(uris, LiteralString):
        return None

    feature = Feature()
    elem = next(uris.__iter__())
    if elem.position_in_triple == 2:
        feature.property = uris
    else:
        feature.value = uris

    return feature
