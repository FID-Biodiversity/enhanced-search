"""Provides processors that can enrich Query objects semantically."""

from typing import Any, Dict, List, Optional, Set, Union

from enhanced_search import configuration as config
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
        semantic_engine_name: Optional[str] = None,
        text_annotator: Optional[TextAnnotator] = None,
    ):
        self.text_annotator = text_annotator
        self.semantic_engine_name = semantic_engine_name

    def update_query_with_annotations(self, query: Query) -> None:
        """Adds further semantic data to the given query.

        The query object is updated in-place!

        Args:
            query: The query object to process.
        """
        if self.text_annotator is None:
            raise ValueError("The TextAnnotator is not set! Operation not possible!")

        annotation_result = self.text_annotator.annotate(query.original_string)

        query.annotations = annotation_result.named_entity_recognition
        query.literals = annotation_result.literals

        query.statements = create_statements_from_dependencies(
            dependencies=annotation_result.annotation_relationships,
            annotations=query.annotations,
            literals=query.literals,
        )

    def resolve_query_annotations(
        self, query: Query, limit: Optional[int] = None
    ) -> bool:
        """Adds further data to the annotations of the query.

        This is e.g. inferencing URIs of Annotations, if necessary (i.e. querying
        URIs of Annotation features like "plants with red flowers").
        If the inferencing is successful, and there are URIs in the database fitting
        the criteria, the received URIs are updating the Annotations URIs.

        Args:
            query: The query object to process.
            limit: A positive integer, setting the maximum number of returned results.

        Returns:
            A boolean value to indicate, whether the annotations resolved in more data
                (True) or if no data could be found for the given criteria (False).
        """
        if self.semantic_engine_name is None:
            raise ValueError("The Semantic Engine is not set! Operation not possible!")

        engine_factory = SemanticEngineFactory()
        semantic_engine = engine_factory.create(self.semantic_engine_name)
        additional_annotation_data = semantic_engine.generate_query_semantics(
            query, limit=limit
        )

        was_enrichment_successful = bool(additional_annotation_data)

        update_annotations(additional_annotation_data, query)
        update_query(query)

        return was_enrichment_successful


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
        if statement.subject is not None:
            annotation = annotation_by_uri_index.get(freeze_key(statement.subject))

            if annotation is not None:
                create_features_from_statements(annotation, statement)

                for feature in annotation.features:
                    _update_feature(feature, annotation, annotation_by_uri_index)


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
        if statement_object is not None and feature is not None:
            feature.value = statement_object
    else:
        feature.property = statement.predicate

    if feature is not None:
        annotation.features.append(feature)


def create_statements_from_dependencies(
    dependencies: List[Dict[str, Any]],
    annotations: List[Annotation],
    literals: List[LiteralString],
) -> List[Statement]:
    """Compiles the output of the dependency parser to
    generate a list of Statements.
    """
    annotation_by_id_index = {annotation.id: annotation for annotation in annotations}
    literal_by_id_index = {literal.id: literal for literal in literals}

    statements = []
    for dependency in dependencies:
        statement_parameters: Dict[str, Any] = {
            name: annotation_by_id_index[annotation_id].uris
            for name, annotation_id in dependency.items()
            if annotation_id in annotation_by_id_index
        }

        statement_parameters.update(
            {
                name: literal_by_id_index[literal_id]
                for name, literal_id in dependency.items()
                if literal_id in literal_by_id_index
            }
        )

        relationship_type = dependency.get(config.RELATIONSHIP_STRING)
        if relationship_type is not None:
            statement_parameters[config.RELATIONSHIP_STRING] = relationship_type

        statement = Statement(**statement_parameters)
        statements.append(statement)

    return statements


def update_query(query: Query) -> None:
    """Updates the internal consistency of the Query object.

    This method removes all Annotations that were assigned to
    be Features of another Annotation.
    """

    features = tuple(
        feature for annotation in query.annotations for feature in annotation.features
    )

    uri_to_annotation_index = {
        freeze_key(annotation.uris): annotation
        for annotation in query.annotations
        if annotation.is_feature
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


def create_feature_from_uris(
    uris: Optional[Union[Set[Uri], LiteralString]]
) -> Optional[Feature]:
    """Creates a Feature object from the given URIs."""
    if not uris or isinstance(uris, LiteralString) or uris is None:
        return None

    feature = Feature()
    elem = next(uris.__iter__())  # pylint: disable=C2801
    if elem.position_in_triple == 2:
        feature.property = uris
    else:
        feature.value = uris

    return feature


def _update_feature(
    feature: Feature, annotation: Annotation, annotation_by_uri_index: dict
) -> None:
    for attr in [feature.value, feature.property]:
        if attr is None:
            continue

        referencing_annotation = annotation_by_uri_index.get(freeze_key(attr))
        if (
            referencing_annotation is not None
            and referencing_annotation is not annotation
        ):
            # Mark only non-self referencing annotations as feature
            referencing_annotation.is_feature = True


def freeze_key(set_to_freeze: Union[Set[Uri], Uri, LiteralString]) -> tuple:
    """Returns a tuple of either a sorted set or containing a single Uri."""
    if isinstance(set_to_freeze, (Uri, LiteralString)):
        return (set_to_freeze,)

    return tuple(sorted(set_to_freeze, key=lambda a: a.url))
