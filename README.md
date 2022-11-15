# BIOfid Enhanced Search Framework: Semantic user query enrichment

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
![Code style black](https://img.shields.io/badge/code%20style-black-000000.svg)

This package provides the annotation and search tools used in the [BIOfid portal](https://www.biofid.de). It is not a search by itself but, as the names says, provides the framework for query annotation as well as database configuration and usage.

Currently, the package provides only the query annotation module. This will be extended in the future.

This package is under ongoing development. It is very likely that functions will be deprecated, return formats or parameter may change, or classes change their module.

## Installation
Currently, the package is not available via PyPI. Hence, you have to clone the repo (or a commit/release of your choice) via `git clone https://github.com/FID-Biodiversity/enhanced-search.git`.

Subsequently, you can install the package via:

```shell
cd enhanced-search/
virtualenv venv
source venv/bin/activate
pip install .
```

## Overview
The main part of the package is the query and text annotation. The annotation allows to get the semantics of the given query string. The text annotation part will do what most other NLP tools do (e.g. [Spacy](https://spacy.io/)), but in a more simplistic way. For example, there is no [part of speech tagging](https://en.wikipedia.org/wiki/Part-of-speech_tagging), but instead the framework relies on [Simplemma](https://github.com/adbar/simplemma), which uses a language-depending dictionary approach, without the need for part of speech.

Using this simplified, rules-based approach has the advantage that the start-up time is very fast, because no models need to be loaded. `simplelemma` needs roughly 700 ms to load when first used. Subsequent usages are much faster. Additionally, the RAM usage of this package is much smaller than any NLP tool. Also, query strings that do not follow common grammar (like a list of keywords: "Germany Plants") can be very easily resolved with this approach while a full NLP framework may misjudge this query (e.g. in this case annotating "Plants" as a verb).

### Dependency Linking
To recognize dependencies between the words in a given query, the current approach is to use a [pattern recognition based on Regex](https://github.com/FID-Biodiversity/enhanced-search/blob/main/src/enhanced_search/annotation/text/engines/dependencies.py). I chose this approach, since it returns reliably correct, reproducible results. Furthermore, the range of potential user queries is quite small and can be caught by this simple tool. Another advantage is that it can resolve disambiguation quite easily.

### Caveat
All the above means, on the other side, that this framework is not applicable to any full text annotation efforts. For this purpose, I recommend going with tools like [Spacy](https://spacy.io/) or the [TextImager of the TTLab](https://textimager.hucompute.org/).

## Text Annotation
The `TextAnnotator` class does the heavy lifting in regard of processing a user query. The `TextAnnotator` relies on a customizable list of `engines`. It passes the `text` through all engines in the given order.

An engine could be e.g. a tokenizer, or a named entity recognizer. Some engines depend on previous results, while others are completely independent and only use the given `text` to generate their output. However, all engines have in common that they obey the [AnnotationEngine interface](https://github.com/FID-Biodiversity/enhanced-search/blob/main/src/enhanced_search/annotation/text/engines/__init__.py).

### Example
For getting started, you can simply call the `TextAnnotatorFactory` to create a new default `TextAnnotator` object. In the background it holds a tiny database that is aware of named entities like "Pflanze", "Fagus", "Fagus sylvatica", "Deutschland", and "Paris" (the latter can be both [the city](https://en.wikipedia.org/wiki/Paris) or the [plant genus](https://en.wikipedia.org/wiki/Paris_(plant))).

```python
from enhanced_search.factories import TextAnnotatorFactory

factory = TextAnnotatorFactory()
text_annotator = factory.create()

# Currently, only German language is supported for lemmas.
annotation_result = text_annotator.annotate("Wo finde ich Fagus sylvatica in Paris?")

for ne in annotation_result.named_entity_recognition:
    print(f"'{ne.text}' is a {ne.named_entity_type.value}!")
# Output:
# 'Fagus sylvatica' is a Plant!
# 'Paris' is a Location!
```

The framework is designed to also handle text input that does not follow usual grammar.

```python
annotation_result = text_annotator.annotate("Fagus sylvatica Deutschland")

for ne in annotation_result.named_entity_recognition:
    print(f"'{ne.text}' is a {ne.named_entity_type.value}!")
# Output:
# 'Fagus sylvatica' is a Plant!
# 'Deutschland' is a Location!
```

Finally, the disambiguation engine should at least catch the most common issues. Remember the ambiguity between Paris (the city) and Paris (the plant genus)?

```python
annotation_result = text_annotator.annotate("Paris in Paris")

for ne in annotation_result.named_entity_recognition:
    print(f"'{ne.text}' (positions: {ne.begin}-{ne.end}) is a {ne.named_entity_type.value}!")
# Output:
# 'Paris' (positions: 0-5) is a Plant!
# 'Paris' (positions: 9-14) is a Location!
```

The disambiguation is mostly done by having the indicator "in". If you would just provide "Paris Paris", the `TextAnnoator` would just see the plant in both words. Why the plant? Because internally the `TextAnnotator` holds a named entity type priority list (in the variable `ANNOTATION_PRIORITY` in the `configuration`). If you do not like it, you can swap the elements of the list.

```python
from enhanced_search import configuration as config
print(config.ANNOTATION_PRIORITY)
# Output:
# ['Plant_Flora', 'Animal_Fauna', 'Taxon', 'Location_Place', 'Miscellaneous']
```

In this case, the `Plant_Flora` annotation will always outrule all other annotations, if in doubt.

The `TextAnnotator` should NOT be used in production with its default settings, since it only knows a few words for demonstration purposes! For production, you need a full database (best would be a key-value database like [Redis](https://redis.io/)) filled with data according the required [data structure](#data-structure).

After you have [configured](#configuration) your databases, you could create your custom `TextAnnotator` object:

```python
from enhanced_search.annotation.text.engines import *
from enhanced_search.annotation.text.engines.tokenizer import SimpleTokenizer
from enhanced_search.annotation.text.engines.lemmatizer import SimpleLemmatizer
from enhanced_search.factories import DatabaseFactory, TextAnnotatorFactory

db_factory = DatabaseFactory()

# Uses a database with the name "key-value" that was defined in the configuration
key_value_database = db_factory.create("key-value")
engines = [
    # The engine order matters!
    # Some engines depend on the results of previous engines!
    SimpleTokenizer(),
    SimpleLemmatizer(),
    StringBasedNamedEntityAnnotatorEngine(key_value_database),
    LiteralAnnotationEngine(),
    UriLinkerAnnotatorEngine(key_value_database),
    DisambiguationAnnotationEngine(),
    PatternDependencyAnnotationEngine(),
]

annotator_factory = TextAnnotatorFactory()
text_annotator = annotator_factory.create_by_configuration(engines)
```

### Data Structure
The [Example](#example) applies data that is put into the [`enhanced_search.configuration.FALLBACK_DATABASE_DATA`](https://github.com/FID-Biodiversity/enhanced-search/blob/main/src/enhanced_search/configuration.py) variable. You could fill this variable with your own data and go with it in production, but I do not recommend this approach, since I do not know if this approach scales well and if it is robust.

Before you go further, you should know that you do not need this data structure. In fact, you could go with your very own dataset. However, at least the `StringBasedNamedEntityAnnotatorEngine` and the `UriLinkerAnnotatorEngine` rely on this data structure. If you do not provide this structure, for any reason, you could leave these two `AnnotationEngine` out, but would not receive any annotations and finally would just throw away the annotation functionality of this framework. So, the much more likely consequence would be that you have to implement classes yourself that implement your schema and return the data appropriately. This also applies, if you want to go with another database than Redis. If you have a relational database and want to use it, you have to write a class that can speaks to the database and can convert its response.

But for now let's assume you stick with the given data structure. How does the data look like?

```python
from enhanced_search import configuration as config
print(config.FALLBACK_DATABASE_DATA)
# Output (truncated):
# ...
# 'pflanze': '{"Plant_Flora": [["https://www.biofid.de/ontology/pflanzen", 3]]}',
# ...
# 'paris': '{"Location_Place": [["https://sws.geonames.org/paris", 3]],"Plant_Flora": [["https://www.biofid.de/ontology/paris", 3]]}'
# ...
```
You see that the data uses a lowercase key for accessing the values. The respective value is a JSON string with the named entity type as key (e.g. "Plant_Flora"). If there is an ambiguity, both named entity types are added to the ambiguous label. Hence, the search framework receives the information about both possible meanings of "Paris" from the same key.

When inspecting the JSON string further, you see that there is a nested list associated with each named entity type. Each of the inner lists (e.g. `["https://www.biofid.de/ontology/pflanzen", 3]`) hold exactly one URI and one numeric value. The latter can be either `2` or `3`. This numeric value is the position that the given URI would take in a triple (or in a SPARQL query; hence it cannot be `1`, because on first position would be the variable, we are querying for). The outer list that wraps this list, only has the purpose to handle the possibility that a single label with a given named entity could have multiple URIs. Hence, a potential data structure could look like this:

```python
{'paris': '{
    "Location_Place": [["https://sws.geonames.org/paris", 3]],
    "Plant_Flora": [["https://www.biofid.de/ontology/paris", 3], 
                    ["https://www.biofid.de/ontology/another_paris_uri, 3]
}'}
```

#### Custom Named Entities
Currently, the search framework only provides a few named entity types (you can find the most recent implementation [here](https://github.com/FID-Biodiversity/enhanced-search/blob/main/src/enhanced_search/annotation/text/utils.py)). It is very likely that you would like to extend the named entity types by some of your own. However, there is currently no flexible way to do so. Still, to give you a starting point, you need add your new type to the [`NamedEntityType` class](https://github.com/FID-Biodiversity/enhanced-search/blob/main/src/enhanced_search/annotation/__init__.py). Additionally, you have to add the named entity strings in the [`named_entity_mapping` dictionary](https://github.com/FID-Biodiversity/enhanced-search/blob/main/src/enhanced_search/annotation/text/utils.py).

## Query Processing
The query processing represents a layer of abstraction higher than the text annotation. This means the class `SemanticQueryProcessor` applies a `TextAnnotator` for the annotation and subsequently can runs further enrichment (if necessary), using a `SemanticEngine` (see also in the [Configuration](#semantic-engine)).

```python
from enhanced_search.annotation import Query
from enhanced_search.annotation.query.processors import SemanticQueryProcessor
from enhanced_search.factories import TextAnnotatorFactory
from enhanced_search import configuration as config

config.DATABASES = {
    "sparql": {
        "class": "tests.dummies.DummySparqlKnowledgeDatabase",
        "rdf_source_path": "./tests/resources/rdf/default.nt",
    }
}

config.SEMANTIC_ENGINES = {
    "sparql-engine": {
        "class": "enhanced_search.annotation.query.engines.SparqlSemanticEngine",
        "database": "sparql",
    }
}

annotator_factory = TextAnnotatorFactory()
text_annotator = annotator_factory.create()

query_processor = SemanticQueryProcessor(
    # Uses a SemanticEngine with the name "sparql" as defined in the configuration
    semantic_engine_name="sparql-engine",
    text_annotator=text_annotator
)

query = Query("Pflanzen mit roten Blüten")

# Runs the TextAnnotator and parses the results to the query object
query_processor.update_query_with_annotations(query)

for statement in query.statements:
    print(f"Subject: {statement.subject}\n"
          f"Predicate: {statement.predicate}\n"
          f"Object: {statement.object}")
# Output:
# Subject: {Uri(url='https://www.biofid.de/ontology/pflanzen', position_in_triple=3, is_safe=False, labels=set(), parent=None, children=set())}
# Predicate: {Uri(url='https://pato.org/flower_part', position_in_triple=2, is_safe=False, labels=set(), parent=None, children=set())}
# Object: {Uri(url='https://pato.org/red_color', position_in_triple=3, is_safe=False, labels=set(), parent=None, children=set())}
```

All this code above simply creates a `TextAnnoator` object, which does its jobs and then parses its results to the query object. Most notably, the query object holds a `statements` variable that holds information on how named entities in the query are related with each other. In the above example, the `TextAnnotator` realized that there is a plant (the subject) that has a flower (the predicate) with red color (the object).

Yet, we do not know which plants have red flowers. If we want to get the URIs of plants that fit these criteria, we can do:

```python
print([uri.url for uri in query.annotations[0].uris])
# Output:
# ['https://www.biofid.de/ontology/pflanzen']

query_processor.resolve_query_annotations(query)

print([uri.url for uri in query.annotations[0].uris])
# Output:
# ['https://www.biofid.de/ontology/plant_with_red_flower_1', 
# 'https://www.biofid.de/ontology/plant_with_red_flower_3', 
# 'https://www.biofid.de/ontology/plant_with_red_flower_2', 
# 'https://www.biofid.de/ontology/plant_with_red_flower_and_3_petals']
```

The `resolve_query_annotations` method used the database in the background to look up which taxa fit the criteria given in the query's `statements`.

The original data is not lost. It is stored in the `features` variable of the respective annotation.

```python
print(query.annotations[0].features)
# Output:
# [Feature(
#   property=None, value={Uri(url='https://www.biofid.de/ontology/pflanzen', position_in_triple=3, is_safe=False, labels=set(), parent=None, children=set())}), 
# Feature(
#   property={Uri(url='https://pato.org/flower_part', position_in_triple=2, is_safe=False, labels=set(), parent=None, children=set())}, 
#   value={Uri(url='https://pato.org/red_color', position_in_triple=3, is_safe=False, labels=set(), parent=None, children=set())}
#)]
```

You see that the annotation's features hold the original URI of the annotation (´https://www.biofid.de/ontology/pflanzen´) and as another feature the criteria that it has red flowers in the form of `property` (which is the predicate, in this the flower) and `value` (which is the object, in this case the color red).

## Configuration
To add configurations flexible, just modify the variables stored in the `enhanced_search.configuration`. Be aware, that you have to add your data there, before calling the functions of the framework. Otherwise, it is not guaranteed that your settings will apply!

### Database

First, you need to specify the databases you will need. This applies to any database you want to use with the search framework. You have to specify the database in the variable `DATABASE` in the `configuration`! Let's say, you want to set a SPARQL and a Redis database for now. This would look like this:

```python
from enhanced_search import configuration as config
import os

config.DATABASES = {
    # The name of the database to reference it from both other configuration or the code
    "sparql": {
        # The import path of the class to use
        "class": "enhanced_search.databases.SparqlGraphDatabase",
        # All other keys that are not "class" will be handed to the class as parameters.
        "url": "http://localhost:1234",
    },
    # The below database will be called with "key-value" from other configurations or
    # from the code. It will use the "RedisDatabase" class that is defined in the
    # enhanced_search.database module. The parameters "url", "port", "db_number", "user",
    # and "password" will be handed to the class "RedisDatabase" as construction
    # parameters.
    "key-value": {
        "class": "enhanced_search.databases.RedisDatabase",
        "url": "http://localhost",
        "port": 5678,
        "db_number": 0,
        "user": os.getenv("key-value-user"),
        "password": os.getenv("key-value-password")
    }
}
```

Now, you could from anywhere in the code call:

```python
from enhanced_search.factories import DatabaseFactory

factory = DatabaseFactory()
db = factory.create("key-value")
# The variable "db" will now hold an object of the "RedisDatabase" class.
```

### Semantic Engine

After you defined the database, you can also define the semantic engine in the variable `SEMANTIC_ENGINES` (if you want to use e.g. the `SemanticQueryProcessor`. Currently, there is only one semantic engine implemented that can translate a query to a SPARQL query and convert back the SPARQL response into a proper Python format.

To set the semantic engine appropriately simply call:

```python
from enhanced_search import configuration as config
config.SEMANTIC_ENGINES = {
    # The name of the semantic engine
    "sparql": {
        # The import path of the class to use
        "class": "enhanced_search.annotation.query.engines.SparqlSemanticEngine",
        # The name of the database you want to use with this engine
        "database": "sparql",
    }
}
```

You can see, that we used the name "sparql" (case-sensitive!) to tell the semantic engine that it should use the database with the respective name, as defined in the `DATABASES` variable.


## Development
### Setup
For any development, you need to install the development dependencies:

```shell
# When you are in the package root directory
pip install -e .[dev]
```

### Running Tests
When in the package root directory, simply call:

```shell
pytest
```

This should run the tests, test coverage, linters, and static testing tools.

## License
![AGPL-3.0 License](https://www.gnu.org/graphics/agplv3-88x31.png)
