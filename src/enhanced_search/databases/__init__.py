"""Interfaces to talk to databases."""

from .graph import SparqlGraphDatabase
from .key_value import RedisDatabase

__all__ = ["SparqlGraphDatabase", "RedisDatabase"]
