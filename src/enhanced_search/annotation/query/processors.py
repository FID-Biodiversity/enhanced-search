from typing import Optional, Set, Union

from enhanced_search.annotation import (
    Annotation,
    Feature,
    LiteralString,
    Query,
    Statement,
    Uri,
)
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

    Annotations that are associated with another Annotation, by e.g. describing it
    further (in the query "Plants with red flowers", "red" and "flowers" are associated
    with "Plants"). These Annotations are converted to a Feature and appended to the
    associated Annotation. The Annotations that build the Feature are removed from the
    Query Annotation List.

    If no corresponding data for an Annotation could be found in a database, the
    corresponding Annotation will have an empty URI list. But only if a database was
    searched (hence, only with Annotations with additional descriptive Annotations,
    not with simple queries like "Fagus sylvatica" or "Fagus sylvatica in Berlin".
    """

    def __init__(
        self,
        semantic_engine_name: str = None,
        text_annotator: TextAnnotator = None,
    ):
        self.text_annotator = text_annotator
        self.semantic_engine_name = semantic_engine_name

    def update_query_with_annotations(self, query: Query) -> None:
        """Adds further semantic data to the given query.
        The query object is updated in-place!
        """
        annotation_result = self.text_annotator.annotate(query.original_string)
        query.annotations = annotation_result.named_entity_recognition

    def resolve_query_annotations(self, query: Query) -> None:
        """Adds further data to the annotations of the query.
        This is e.g. inferencing URIs of Annotations, if necessary (i.e. querying
        URIs of Annotation features like "plants with red flowers").
        If the inferencing is successful, and there are URIs in the database fitting
        the criteria, the received URIs are updating the Annotations uris. The original
        URI(s) for this annotation
        """
        engine_factory = SemanticEngineFactory()
        semantic_engine = engine_factory.create(self.semantic_engine_name)
        additional_annotation_data = semantic_engine.generate_query_semantics(query)

        update_annotations(additional_annotation_data, query)

        update_query(query)


def update_annotations(annotation_data: dict, query: Query) -> None:
    """Adds the enriched annotation data to the respective Annotations
    in the given Query.

    This updates the Annotation's features (if appropriate), where a Feature is
    composed of the data of the other Annotations in the same query. Furthermore,
    the Annotation's URIs are updated with retrieved URIs (if any).
    """
    update_annotation_features(query)

    for annotation, uris in annotation_data.items():
        annotation.uris = uris

    for annotation in query.annotations:
        purge_ambiguous_annotations(annotation)


def update_annotation_features(query: Query) -> None:
    """Handles the Feature creation for each Annotation."""
    annotation_by_uri_index = {
        freeze_key(annotation.uris): annotation for annotation in query.annotations
    }

    for statement in query.statements:
        annotation = annotation_by_uri_index.get(freeze_key(statement.subject))
        create_features_from_statements(annotation, statement)
        annotation.uris = set()


def create_features_from_statements(
    annotation: Annotation, statement: Statement
) -> None:
    """Creates a Feature for the given Statement and adds it
    to the given Annotation.
    """
    feature = create_feature_from_uris(annotation.uris)

    if feature is not None:
        annotation.features.append(feature)

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


def update_query(query: Query) -> None:
    """Updates the internal consistency of the Query object.
    This method removes all Annotations that were assigned to be Features of another
    Annotation.
    """

    features = tuple(
        feature for annotation in query.annotations for feature in annotation.features
    )

    uri_to_annotation_index = {
        freeze_key(annotation.uris): annotation
        for annotation in query.annotations
        if annotation.uris
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


def purge_ambiguous_annotations(annotation: Annotation) -> None:
    """Removes all ambiguous annotations associated with an Annotation."""
    annotation.ambiguous_annotations = set()


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


def freeze_key(set_to_freeze: Union[Set[Uri], Uri]) -> tuple:
    """Returns a tuple of either a sorted set or containing a single Uri."""
    if isinstance(set_to_freeze, Uri):
        return (Uri,)
    else:
        return tuple(sorted(set_to_freeze, key=lambda a: a.url))
