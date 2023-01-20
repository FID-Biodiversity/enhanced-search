"""The definitions of all engines running the query enrichment."""

import json
from copy import deepcopy
from typing import List, Optional, Protocol, runtime_checkable

from SPARQLBurger.SPARQLQueryBuilder import SPARQLGraphPattern, SPARQLSelectQuery
from SPARQLBurger.SPARQLSyntaxTerms import Prefix, Triple

from enhanced_search.annotation import (
    LiteralString,
    NamedEntityType,
    Query,
    Statement,
    Uri,
)
from enhanced_search.annotation.utils import prepare_value_for_sparql
from enhanced_search.databases.graph import KnowledgeDatabase


@runtime_checkable
class SemanticEngine(Protocol):
    """An interface class to inference the semantics of a query."""

    def generate_query_semantics(self, query: Query) -> dict:
        """Takes a query and returns data retrieved e.g. from its annotations."""


class SparqlSemanticEngine:
    """Uses a SPARQL database to retrieve additional data on a query.

    ToDo:
        Add query sanitization!

    Obeys the SemanticEngine interface.
    """

    def __init__(self, database: KnowledgeDatabase):
        self._database = database
        self._sparql_generator = SparqlQueryGenerator()

    def generate_query_semantics(
        self, query: Query, limit: Optional[int] = None
    ) -> dict:
        """Takes a Query and returns additional data on its Annotations.

        Args:
            query: The query object to provide the semantics.
            limit: The maximum number of results to return.
        """
        taxon_variable_name = "taxon"
        db_response_string = None

        if query.statements:
            sparql_query = self._sparql_generator.generate(
                f"?{taxon_variable_name}", query.statements, limit=limit
            )

            db_response_string = self._database.read(sparql_query, is_safe=True)

        if db_response_string is not None:
            data = self._extract_data_from_response(db_response_string)
        else:
            data = {}

        return self._generate_result(query, data, taxon_variable_name)

    def _extract_data_from_response(self, db_response_string: str) -> dict:
        data = json.loads(db_response_string)
        return data["results"]["bindings"]

    def _generate_result(self, query: Query, data: dict, taxon_name: str) -> dict:
        """Currently, only adds all results to the first taxon result."""
        taxon_annotations = [
            annotation
            for annotation in query.annotations
            if annotation.named_entity_type
            in {NamedEntityType.TAXON, NamedEntityType.PLANT, NamedEntityType.ANIMAL}
        ]

        updated_data = {
            Uri(row[taxon_name]["value"], is_safe=True) for row in data if row
        }

        if not taxon_annotations or not updated_data:
            return {}

        taxon_annotation = taxon_annotations[0]

        return {taxon_annotation: updated_data}


class SparqlQueryGenerator:
    """Creates SPARQL query strings generated from an annotation context."""

    NAMESPACES = {"terms": "https://dwc.tdwg.org/terms/#"}
    DEFAULT_LIMIT = 1000

    SYSTEMATIC_HIERARCHY_PREDICATES = [
        "terms:kingdom",
        "terms:class",
        "terms:order",
        "terms:family",
        "terms:genus",
        "terms:phylum",
        "terms:parentNameUsageID",
        "terms:acceptedNameUsageID",
    ]

    def __init__(self):
        self.select_limit = self.DEFAULT_LIMIT
        self.namespaces = self.NAMESPACES

    def generate(
        self,
        variable_name: str,
        statements: List[Statement],
        limit: Optional[int] = None,
    ) -> str:
        """Generates a new SPARQL query string from the given context.

        The variable name(s) provided have to be prefixed with a "?", e.g. "?parent".

        To limit the number of results, give `limit` a positive integer. If this
        limit should always apply, you should set the `select_limit` attribute of
        the object.
        """

        select_pattern = self._setup_select_query(namespaces=self.namespaces)

        select_pattern.add_variables([variable_name])

        main_pattern = SPARQLGraphPattern()
        select_pattern.set_where_pattern(main_pattern)

        for index, statement in enumerate(deepcopy(statements)):
            is_optional = index > 0
            pattern = SPARQLGraphPattern(optional=is_optional)
            self._add_taxon_triple(pattern, variable_name, statement)
            self._add_filtering_triples(pattern, variable_name, statement)

            main_pattern.add_nested_graph_pattern(pattern)

        select_query_string = select_pattern.get_text()

        limit = self.select_limit if limit is None else limit
        select_query_string += f"ORDER BY {variable_name}\n LIMIT {limit}"

        return select_query_string

    def _setup_select_query(self, namespaces: dict) -> SPARQLSelectQuery:
        select_query = SPARQLSelectQuery(distinct=True)

        for name, url in namespaces.items():
            select_query.add_prefix(prefix=Prefix(prefix=name, namespace=url))

        return select_query

    def _add_taxon_triple(
        self,
        pattern: SPARQLGraphPattern,
        taxon_variable_name: str,
        statement: Statement,
    ) -> None:
        if statement.subject is None:
            return

        hierarchical_values = Triple(
            subject="VALUES",
            predicate="?hasParent",
            object=f"{{{' '.join(self.SYSTEMATIC_HIERARCHY_PREDICATES)}}}",
        )

        subject_variable_name = "?subject"

        if isinstance(statement.subject, (Uri, LiteralString)):
            subject_variable_name = prepare_value_for_sparql(statement.subject)
        else:
            subjects = " ".join(
                prepare_value_for_sparql(uri) for uri in statement.subject
            )
            taxon_values = Triple(
                subject="VALUES",
                predicate=subject_variable_name,
                object=f"{{{subjects}}}",
            )
            pattern.add_triples([taxon_values])

        taxon_triple = Triple(
            subject=taxon_variable_name,
            predicate="?hasParent",
            object=subject_variable_name,
        )

        pattern.add_triples([hierarchical_values, taxon_triple])

    def _add_filtering_triples(
        self,
        pattern: SPARQLGraphPattern,
        taxon_variable_name: str,
        statement: Statement,
    ):
        predicates = statement.predicate
        values = statement.object
        if predicates is None and values is None:
            return

        predicate_variable_name = "?predicates"
        values_variable_name = "?predicateValues"
        if predicates is not None:
            predicate_values = " ".join(
                prepare_value_for_sparql(uri) for uri in predicates
            )
            value_triple = Triple(
                subject="VALUES",
                predicate=predicate_variable_name,
                object=f"{{{predicate_values}}}",
            )
            pattern.add_triples([value_triple])

        if values is not None:
            if isinstance(values, LiteralString):
                values_variable_name = prepare_value_for_sparql(values)
            elif len(values) > 1:
                values_values = " ".join(
                    prepare_value_for_sparql(uri) for uri in values
                )
                value_triple = Triple(
                    subject="VALUES",
                    predicate=values_variable_name,
                    object=f"{{{values_values}}}",
                )
                pattern.add_triples([value_triple])
            else:
                values_variable_name = prepare_value_for_sparql(values.pop())

        triple = Triple(
            subject=taxon_variable_name,
            predicate=predicate_variable_name,
            object=values_variable_name,
        )
        pattern.add_triples([triple])
