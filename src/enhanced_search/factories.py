"""Here, factory classes are defined that allow the easy creation of complex objects."""

import importlib
from copy import deepcopy
from typing import Any, Optional, Type

from enhanced_search import configuration as config
from enhanced_search.annotation.query.engines import SemanticEngine
from enhanced_search.annotation.text import TextAnnotator, TextAnnotatorConfiguration
from enhanced_search.annotation.text.engines import (
    StringBasedNamedEntityAnnotatorEngine,
    LiteralAnnotationEngine,
    PatternDependencyAnnotationEngine,
    UriLinkerAnnotatorEngine,
    DisambiguationAnnotationEngine,
)
from enhanced_search.databases.interface import Database

CLASS_PATH_KEYWORD = "class"


class TextAnnotatorFactory:
    """A simple factory that takes care of all the configuration of a TextAnnotator."""

    def create(self) -> TextAnnotator:
        """Create a new TextAnnotator object."""
        configuration = self._get_default_configuration()
        return self.create_by_configuration(configuration)

    def create_by_configuration(
        self, configuration: TextAnnotatorConfiguration
    ) -> TextAnnotator:
        """Creates a TextAnnotator object by the given configuration."""
        return TextAnnotator(configuration)

    def _get_default_configuration(self):
        database_factory = DatabaseFactory()

        try:
            key_value_db = database_factory.create("key-value")
            ne_engine = StringBasedNamedEntityAnnotatorEngine(db=key_value_db)
            literal_engine = LiteralAnnotationEngine()
            dependency_parser = PatternDependencyAnnotationEngine()
            entity_linker = UriLinkerAnnotatorEngine(db=key_value_db)
            disambiguation_engine = DisambiguationAnnotationEngine()

            return TextAnnotatorConfiguration(
                dependency_recognition=dependency_parser,
                disambiguation_engine=disambiguation_engine,
                entity_linker=entity_linker,
                literal_recognition=literal_engine,
                named_entity_recognition=ne_engine,
            )
        except KeyError:
            raise RuntimeError(
                "There is no default database available for the"
                "TextAnnotator to be instantiated!"
            )


class SemanticEngineFactory:
    """Orchestrates the creation of SemanticEngine objects.

    This factory retrieves its configuration from the configuration.py . Use the
    variable SEMANTIC_ENGINES for this. An example for the configuration is:

    SEMANTIC_ENGINES = {
        "sparql": {
            "class": "enhanced_search.annotation.query.engines.SparqlSemanticEngine",
            "database": "sparql",
        },
        ...
    }

    Each engine has to have a "class" keyword that provides the module path from where
    the engine should be loaded. The "database" keyword is optional and should reference
    the key of a database defined in the variable DATABASES, which is also in the
    configuration.py . All other parameters will be used as input variables for the
    constructor of the SemanticEngine.
    """

    DATABASE_NAME_CONFIGURATION_KEYWORD = "database"

    def create(self, engine_name: str) -> SemanticEngine:
        """Creates a Semantic Engine object.

        :raises KeyError: When the given engine_name is not defined.
        """
        registered_engines = self._retrieve_engine_configurations()
        engine_parameters: dict = deepcopy(registered_engines[engine_name])

        self._load_database(engine_parameters)

        engine_import_path = engine_parameters.pop(CLASS_PATH_KEYWORD)
        semantic_engine_callable = load_class(
            module_path=engine_import_path, required_type=SemanticEngine
        )

        return semantic_engine_callable(**engine_parameters)

    def _retrieve_engine_configurations(self) -> dict:
        return config.SEMANTIC_ENGINES

    def _load_database(self, engine_parameters: dict) -> None:
        database_name = engine_parameters.pop(
            self.DATABASE_NAME_CONFIGURATION_KEYWORD, None
        )
        if database_name is not None:
            database_factory = DatabaseFactory()
            database = database_factory.create(database_name)
            engine_parameters[self.DATABASE_NAME_CONFIGURATION_KEYWORD] = database


class DatabaseFactory:
    """Orchestrates the creation of configured Database objects.

    This factory retrieves its configuration from the configuration.py . Use the
    variable DATABASES for this. An example for the configuration is:

    DATABASES = {
        "sparql": {
            "class": "enhanced_search.databases.SparqlGraphDatabase",
            "url": "http://localhost:1234",
        },
        "key-value": {
            "class": "enhanced_search.databases.RedisDatabase",
            "url": "http://localhost",
            "port": 5678,
            "db_number": 0,
            "user": "user",
            "password": "secret"
        }
    }

    The key of the configuration is the name that the factory will take to create
    the respective Database object.
    The only required key in the value dictionary is the "class" parameter, which
    provides the import path for the required Database class.
    Everything else in the value dictionary will be used as input parameters for
    the Database constructor.
    """

    def create(self, database_name: str) -> Database:
        """Creates a fully configured Database object.

        :raises KeyError: If the given name does not exist.
        :raises TypeError: If the provided class does not obey the Database interface.
        """
        database_configurations = self._retrieve_database_configurations()
        requested_database_parameters: dict = deepcopy(
            database_configurations[database_name]
        )

        if CLASS_PATH_KEYWORD not in requested_database_parameters:
            raise KeyError(
                f"You have to provide the key "
                f"'{CLASS_PATH_KEYWORD}' in a database "
                f"configuration!"
            )

        database_module_path_to_load = requested_database_parameters.pop(
            CLASS_PATH_KEYWORD
        )
        database_callable = self.load_database(database_module_path_to_load)

        return database_callable(**requested_database_parameters)

    def _retrieve_database_configurations(self) -> dict:
        return config.DATABASES

    def load_database(self, module_path: str) -> Type[Database]:
        """Load a Database type class from the given module path."""
        return load_class(module_path, Database)


def load_class(module_path: str, required_type: Optional[type] = None) -> Type[Any]:
    """Load a type class from the given module path.

    :raises TypeError: If the required_type is not None and if the loaded class is not
    a subclass of the required_type.
    """
    module, clazz = module_path.rsplit(".", 1)
    module_type = importlib.import_module(module)
    class_callable = getattr(module_type, clazz)

    if required_type is not None and not issubclass(class_callable, required_type):
        raise TypeError(
            f"You have to provide a class obeying the Database interface! "
            f"The module '{module_path}' does not do so!"
        )

    return class_callable
