import pathlib

import pytest

from enhanced_search.annotation.text import TextAnnotatorConfiguration, TextAnnotator
from enhanced_search.annotation.text.engines import (
    StringBasedNamedEntityAnnotatorEngine,
    UriLinkerAnnotatorEngine,
    DisambiguationAnnotationEngine,
)
from tests.dummies import DummySparqlKnowledgeDatabase, DummyKeyValueDatabase
from enhanced_search import configuration as config


# PATHS #
@pytest.fixture(scope="session")
def test_directory() -> pathlib.Path:
    return pathlib.Path(__file__).parent


@pytest.fixture(scope="session")
def resource_directory(test_directory) -> pathlib.Path:
    return test_directory / "resources"


@pytest.fixture(scope="session")
def rdf_data_directory(resource_directory) -> pathlib.Path:
    return resource_directory / "rdf"


@pytest.fixture(scope="session")
def default_n_triples_source_path(rdf_data_directory):
    return rdf_data_directory / "default.nt"


# CONFIGURATION #
@pytest.fixture(scope="session", autouse=True)
def set_database_configuration(default_n_triples_source_path):
    config.DATABASES = {"sparql": {
        "class": "tests.dummies.DummySparqlKnowledgeDatabase",
        "rdf_source_path": default_n_triples_source_path,
    }}

    config.SEMANTIC_ENGINES = {
        "sparql": {
            "class": "enhanced_search.annotation.query.engines.SparqlSemanticEngine",
            "database": "sparql"
        }
    }


# DATABASES #
@pytest.fixture(scope="session")
def loaded_sparql_database(
    default_n_triples_source_path,
) -> "DummySparqlKnowledgeDatabase":
    return DummySparqlKnowledgeDatabase(default_n_triples_source_path)


@pytest.fixture(scope="function")
def empty_sparql_database() -> "DummySparqlKnowledgeDatabase":
    return DummySparqlKnowledgeDatabase()


@pytest.fixture(scope="function")
def empty_key_value_database():
    return DummyKeyValueDatabase()


@pytest.fixture(scope="session")
def loaded_key_value_database():
    db = DummyKeyValueDatabase()
    db.data = {
        "quercus": '{"Plant_Flora": '
        '[["https://www.biofid.de/ontology/quercus", 3]]}',
        "quercus sylvestris": '{"Plant_Flora": '
        '[["https://www.biofid.de/ontology/quercus_sylvestris", 3]]}',
        "fagus": '{"Plant_Flora": ' '[["https://www.biofid.de/ontology/fagus", 3]]}',
        "fagus sylvatica": '{"Plant_Flora": '
        '[["https://www.biofid.de/ontology/fagus_sylvatica", 3]]}',
        "deutschland": '{"Location_Place": [['
        '"https://sws.geonames.org/deutschland", 3]]}',
        "paris": '{"Location_Place": [["https://sws.geonames.org/paris", 3]],'
        '"Plant_Flora": [["https://www.biofid.de/ontology/fagus_sylvatica"'
        ", 3]]}",
    }

    return db


# ANNOTATOR ENGINES #
@pytest.fixture(scope="session")
def string_based_ne_annotator_engine(loaded_key_value_database):
    return StringBasedNamedEntityAnnotatorEngine(loaded_key_value_database)


@pytest.fixture(scope="session")
def uri_linker_annotator_engine(loaded_key_value_database):
    return UriLinkerAnnotatorEngine(loaded_key_value_database)


@pytest.fixture(scope="session")
def disambiguation_annotator_engine():
    return DisambiguationAnnotationEngine()


@pytest.fixture
def text_annotator(
    string_based_ne_annotator_engine,
    uri_linker_annotator_engine,
    disambiguation_annotator_engine,
):
    configuration = TextAnnotatorConfiguration(
        named_entity_recognition=string_based_ne_annotator_engine,
        entity_linker=uri_linker_annotator_engine,
        disambiguation_engine=disambiguation_annotator_engine,
    )
    return TextAnnotator(configuration)
