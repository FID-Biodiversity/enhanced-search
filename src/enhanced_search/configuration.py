"""This is the base configuration file.
The variables can be overridden by importing them like:

    from enhanced_search import configuration as config

To set the databases appropriately, you even need to do this by specifying the data
for DATABASES and SEMANTIC_ENGINES. How to configure these two, you can see in the
classes "factories.DatabaseFactory" and "factories.SemanticEngineFactory", respectively.
"""

# Annotations
PLANT_ANNOTATION_STRING = "Plant_Flora"
ANIMAL_ANNOTATION_STRING = "Animal_Fauna"
LOCATION_ANNOTATION_STRING = "Location_Place"
TAXON_ANNOTATION_STRING = "Taxon"

ANNOTATION_PRIORITY = [
    PLANT_ANNOTATION_STRING,
    ANIMAL_ANNOTATION_STRING,
    TAXON_ANNOTATION_STRING,
    LOCATION_ANNOTATION_STRING,
]

# TextAnnotator
TAXON_CONTEXT_KEYWORD = "taxon"
LOCATION_CONTEXT_KEYWORD = "location"
PREDICATE_CONTEXT_KEYWORD = "predicate"
PREDICATE_VALUE_CONTEXT_KEYWORD = "predicate_value"

# Databases
# See module factories.DatabaseFactory for an example of how databases are configured.
DATABASES: dict = {}


# Semantic Engines
# Probably you only need one, but you never know...
# For how to configure, see factories.SemanticEngineFactory
SEMANTIC_ENGINES: dict = {}
