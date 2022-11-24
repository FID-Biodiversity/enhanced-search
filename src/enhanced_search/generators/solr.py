"""Holds generators that are associated with Apache Solr."""
from copy import copy
from dataclasses import dataclass
from typing import Any, Collection, List, Optional, Set, Union

from solrq import Q as SolrQueryBuilder
from solrq import Value

from enhanced_search.annotation import (
    Annotation,
    LiteralString,
    Query,
    RelationshipType,
    Statement,
    Uri,
)

OR_STRING = "OR"
AND_STRING = "AND"


@dataclass
class SolrQuery:
    """Holds a proper Solr query string and associated metadata."""

    string: str


class SolrQueryGenerator:
    """Converts the given data to proper Solr queries.

    Attributes:
        default_search_field: The search field that is used for generating the query.
        default_conjunction_type: The conjunction that is used to connect otherwise
                            unrelated search terms (default: "AND").

        The defaults can be modified both on the class and on the object level.

    Multiple URIs referencing the same entity are OR-conjuncted.
    """

    DEFAULT_SEARCH_FIELD = "q"
    DEFAULT_CONJUNCTION_TYPE = RelationshipType.AND

    def __init__(self):
        self.default_search_field = self.DEFAULT_SEARCH_FIELD
        self.default_conjunction_type = self.DEFAULT_CONJUNCTION_TYPE

    def to_solr_query(self, query: Query) -> SolrQuery:
        """Creates a valid SolrQuery object from the given Query.

        Notes:
            * The query string is NOT sanitized!
            * URIs are always wrapped in quotation marks.
            * Strings are quoted with double quotation marks.
        """
        query_builder = None

        annotations = copy(query.annotations)
        literals = copy(query.literals)

        query_builder = self._update_query_builder_from_statements(
            query_builder=query_builder,
            statements=query.statements,
            solr_search_field=self.default_search_field,
            annotations=annotations,
            literals=literals,
        )

        for annotation in annotations:
            query_builder = self._add_term_collections_to_solr_query(
                # Sorting of URIs is mainly for testing purposes
                search_terms=sorted(_setup_entity(uri) for uri in annotation.uris),
                search_field_name=self.default_search_field,
                conjunction_string=OR_STRING,
                query_builder=query_builder,
            )

        if literals:
            query_builder = self._add_term_collections_to_solr_query(
                search_terms=[_setup_entity(literal) for literal in literals],
                search_field_name=self.default_search_field,
                conjunction_string=AND_STRING,
                query_builder=query_builder,
            )

        return _compile_solr_query(query_builder)

    def _update_query_builder_from_statements(
        self,
        query_builder: Optional[SolrQueryBuilder],
        statements: List[Statement],
        solr_search_field: str,
        annotations: List[Annotation],
        literals: List[LiteralString],
    ) -> SolrQueryBuilder:
        """Processes the statements and adds their semantics to a SolrQueryBuilder.

        This process also updates the `annotations` and `literals`. I.e. it removes
        all elements that where processed.
        """
        statement_query_builders = []

        for statement in statements:
            if statement.relationship is not None:
                subj = _to_collection(statement.subject)
                element_a_builder = self._add_term_collections_to_solr_query(
                    search_terms=sorted(_setup_entity(entity) for entity in subj),
                    search_field_name=solr_search_field,
                    conjunction_string=OR_STRING,
                )

                obj = _to_collection(statement.object)
                element_b_builder = self._add_term_collections_to_solr_query(
                    search_terms=sorted(_setup_entity(entity) for entity in obj),
                    search_field_name=solr_search_field,
                    conjunction_string=OR_STRING,
                )

                statement_query_builder = _merge_builders(
                    element_a_builder, element_b_builder, statement.relationship
                )

                statement_query_builders.append(statement_query_builder)

                for element in [statement.subject, statement.object]:
                    if element is None:
                        continue

                    if isinstance(element, LiteralString):
                        literals.remove(element)
                    else:
                        annotation = _get_annotation_for_uris(element, annotations)
                        if annotation is not None:
                            annotations.remove(annotation)

        for statement_query_builder in statement_query_builders:
            query_builder = _merge_builders(
                query_builder, statement_query_builder, self.default_conjunction_type
            )

        return query_builder

    def _add_term_collections_to_solr_query(
        self,
        search_terms: Collection[str],
        search_field_name: str,
        conjunction_string: str,
        query_builder: Optional[SolrQueryBuilder] = None,
    ) -> SolrQueryBuilder:
        """Merges to given search terms to a new SolrQueryBuilder.

        The search terms will be conjuncted with the given `conjunction string`.
        If there is more than one search term, the search terms will be wrapped into
        round brackets.

        Args:
            search_terms: The search terms to add to the Solr query.
            search_field_name: The name of the Solr search field, the URIs should be
                                searched in.
            conjunction_string: The string that will be inserted between the single
                                search terms (should be "OR" or "AND").
            query_builder: (Optional) A SolrQueryBuilder object that is merged with
                                the search terms.

        Returns:
            An new SolrQueryBuilder object.
        """

        search_terms_string = f" {conjunction_string} ".join(search_terms)

        if len(search_terms) > 1:
            search_terms_string = _wrap_in_round_brackets(search_terms_string)

        return _create_conjunction(
            query_builder,
            search_field_name,
            search_terms_string,
            self.default_conjunction_type,
        )


def _compile_solr_query(query_builder: SolrQueryBuilder) -> SolrQuery:
    return SolrQuery(str(query_builder))


def _create_conjunction(
    query_builder: Optional[SolrQueryBuilder],
    solr_field_name: str,
    search_string: str,
    relationship_type: RelationshipType,
) -> SolrQueryBuilder:
    """Inferences from the given `relationship_type` how to concatenate the search
    terms.

    Raises:
        NotImplementedError: If the given `relationship_type` is not implemented.

    """
    if relationship_type == RelationshipType.AND:
        return _create_and_conjunction(query_builder, solr_field_name, search_string)
    if relationship_type == RelationshipType.OR:
        return _create_or_conjunction(query_builder, solr_field_name, search_string)

    raise NotImplementedError(
        "The given RelationshipType is not implemented for this operation!"
    )


def _merge_builders(
    builder: Optional[SolrQueryBuilder],
    other_builder: SolrQueryBuilder,
    relationship_type: RelationshipType,
) -> SolrQueryBuilder:
    """Merges the builders and returns a new SolrQueryBuilder object.

    If `builder` is None, the `other_builder` is returned unmodified.

    Raises:
        NotImplementedError: If the given `relationship_type` is not implemented.

    """
    if builder is None:
        return other_builder

    if relationship_type == RelationshipType.AND:
        new_builder = builder & other_builder
    elif relationship_type == RelationshipType.OR:
        new_builder = builder | other_builder
    else:
        raise NotImplementedError(
            "The given RelationshipType is not implemented for this operation!"
        )

    return new_builder


def _create_and_conjunction(
    query_builder: Optional[SolrQueryBuilder], solr_field_name: str, search_string: str
) -> SolrQueryBuilder:
    """Creates a new SolrQueryBuilder object that holds an AND-conjunction of
    the given parameters.
    """
    new_query_builder = SolrQueryBuilder(
        **{solr_field_name: Value(search_string, safe=True)}
    )
    if query_builder is not None:
        new_query_builder = query_builder & new_query_builder

    return new_query_builder


def _create_or_conjunction(
    query_builder: Optional[SolrQueryBuilder], solr_field_name: str, search_string: str
) -> SolrQueryBuilder:
    """Creates a new SolrQueryBuilder object that holds an OR-conjunction of
    the given parameters.
    """
    new_query_builder = SolrQueryBuilder(
        **{solr_field_name: Value(search_string, safe=True)}
    )
    if query_builder is not None:
        new_query_builder = query_builder | new_query_builder  # pylint: disable=E1131

    return new_query_builder


def _setup_entity(entity: Union[Uri, LiteralString]) -> str:
    if isinstance(entity, Uri):
        text = f'"{entity.url}"'
    elif isinstance(entity, LiteralString):
        text = str(entity)
    else:
        raise NotImplementedError(f"The given type {type(entity)} cannot be setup!")

    return text


def _wrap_in_round_brackets(text: str) -> str:
    """Adds round brackets "(" and ")" before the first and after the last character
    of the given text."""
    return f"({text})"


def _get_annotation_for_uris(
    uris: Set[Uri], annotations: List[Annotation]
) -> Optional[Annotation]:
    """Returns the corresponding Annotation to the given URIs."""
    annotation_index = {
        uri: annotation for annotation in annotations for uri in annotation.uris
    }

    for uri in uris:
        annotation = annotation_index.get(uri)
        if annotation is not None:
            return annotation

    return None


def _to_collection(obj: Any) -> Collection:
    if not isinstance(obj, str) and isinstance(obj, Collection):
        return obj

    return [obj]
