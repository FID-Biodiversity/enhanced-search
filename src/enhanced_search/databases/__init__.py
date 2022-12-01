"""Interfaces to talk to databases."""

from .documents import SolrDatabase
from .graph import SparqlGraphDatabase
from .key_value import RedisDatabase

__all__ = ["SparqlGraphDatabase", "RedisDatabase", "SolrDatabase"]
