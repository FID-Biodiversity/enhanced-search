"""Common fixtures for pytest."""

import pathlib

import pytest

from enhanced_search import configuration as config
from enhanced_search.annotation.text import TextAnnotator
from enhanced_search.annotation.text.engines import (
    DisambiguationAnnotationEngine,
    LiteralAnnotationEngine,
    PatternDependencyAnnotationEngine,
    StringBasedNamedEntityAnnotatorEngine,
    UriLinkerAnnotatorEngine,
)
from enhanced_search.annotation.text.engines.language import SimpleLanguageDetector
from enhanced_search.annotation.text.engines.lemmatizer import SimpleLemmatizer
from enhanced_search.annotation.text.engines.tokenizer import SimpleTokenizer
from tests.dummies import DummyKeyValueDatabase, DummySparqlKnowledgeDatabase


# PATHS #
@pytest.fixture(scope="session")
def test_directory() -> pathlib.Path:
    """The path of the test directory."""
    return pathlib.Path(__file__).parent


@pytest.fixture(scope="session")
def resource_directory(test_directory) -> pathlib.Path:
    """The path of the resources directory."""
    return test_directory / "resources"


@pytest.fixture(scope="session")
def rdf_data_directory(resource_directory) -> pathlib.Path:
    """The path of the directory holding all RDF data."""
    return resource_directory / "rdf"


@pytest.fixture(scope="session")
def default_n_triples_source_path(rdf_data_directory):
    """The path to the default ontology in the N-Triples format."""
    return rdf_data_directory / "default.nt"


# CONFIGURATION #
@pytest.fixture(scope="session", autouse=True)
def set_database_configuration(default_n_triples_source_path):
    """Set dummy database configurations automatically."""
    config.DATABASES = {
        "sparql": {
            "class": "tests.dummies.DummySparqlKnowledgeDatabase",
            "rdf_source_path": default_n_triples_source_path,
        },
        "key-value": {
            "class": "tests.dummies.DummyKeyValueDatabase",
        },
        "failing-db": {
            "class": "tests.dummies.FailingDatabase",
        },
    }

    config.SEMANTIC_ENGINES = {
        "sparql": {
            "class": "enhanced_search.annotation.query.engines.SparqlSemanticEngine",
            "database": "sparql",
        },
        "failing-sparql-engine": {
            "class": "enhanced_search.annotation.query.engines.SparqlSemanticEngine",
            "database": "failing-db",
        },
    }


# DATABASES #
@pytest.fixture(scope="function")
def empty_sparql_database() -> "DummySparqlKnowledgeDatabase":
    """An empty SPARQL database."""
    return DummySparqlKnowledgeDatabase()


@pytest.fixture(scope="function")
def empty_key_value_database():
    """An empty key-value database."""
    return DummyKeyValueDatabase()


@pytest.fixture(scope="session")
def loaded_sparql_database(
    default_n_triples_source_path,
) -> "DummySparqlKnowledgeDatabase":
    """A SPARQL database that already holds data of the default ontology."""
    return DummySparqlKnowledgeDatabase(default_n_triples_source_path)


@pytest.fixture(scope="session")
def loaded_key_value_database():
    """A key-value database occupied with some hardcoded data.
    All keys are in lowercase."""
    db = DummyKeyValueDatabase()
    db.data = config.FALLBACK_DATABASE_DATA

    return db


# ANNOTATOR ENGINES #
@pytest.fixture(scope="session")
def simple_tokenizer():
    """Returns an instance of the SimpleTokenizer."""
    return SimpleTokenizer()


@pytest.fixture(scope="session")
def simple_lemmatizer():
    """Returns an instance of the SimpleLemmatizer."""
    return SimpleLemmatizer()


@pytest.fixture(scope="session")
def simple_language_detector():
    """Returns an instance of the SimpleLanguageDetector."""
    return SimpleLanguageDetector()


@pytest.fixture(scope="session")
def string_based_ne_annotator_engine(loaded_key_value_database):
    """A Named Entity AnnotationEngine."""
    return StringBasedNamedEntityAnnotatorEngine(loaded_key_value_database)


@pytest.fixture(scope="session")
def uri_linker_annotator_engine(loaded_key_value_database):
    """An AnnotationEngine linking Annotations to a fitting URI."""
    return UriLinkerAnnotatorEngine(loaded_key_value_database)


@pytest.fixture(scope="session")
def disambiguation_annotator_engine():
    """An AnnotationEngine trying to resolve disambiguation."""
    return DisambiguationAnnotationEngine()


@pytest.fixture(scope="session")
def pattern_dependency_annotator_engine():
    """An AnnotationEngine finding relationships between Annotations
    and LiteralStrings.
    """
    return PatternDependencyAnnotationEngine()


@pytest.fixture(scope="session")
def literal_annotator_engine():
    """An AnnotationEngine that wraps all non-Annotation tokens into
    a LiteralString.
    """
    return LiteralAnnotationEngine()


@pytest.fixture
def text_annotator(
    simple_tokenizer,
    simple_lemmatizer,
    string_based_ne_annotator_engine,
    uri_linker_annotator_engine,
    disambiguation_annotator_engine,
    literal_annotator_engine,
    pattern_dependency_annotator_engine,
):
    """A TextAnnotator that can analyse a Query object."""
    engines = [
        simple_tokenizer,
        simple_lemmatizer,
        string_based_ne_annotator_engine,
        literal_annotator_engine,
        uri_linker_annotator_engine,
        disambiguation_annotator_engine,
        pattern_dependency_annotator_engine,
    ]
    return TextAnnotator(engines)
