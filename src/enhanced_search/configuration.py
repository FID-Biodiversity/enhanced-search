"""This is the base configuration file.
The variables can be overridden by importing them like:

    from enhanced_search import configuration as config

To set the databases appropriately, you even need to do this by specifying the data
for DATABASES and SEMANTIC_ENGINES. How to configure these two, you can see in the
classes "factories.DatabaseFactory" and "factories.SemanticEngineFactory", respectively.
"""
# General
UTF8_STRING = "utf-8"


# Annotations
PLANT_ANNOTATION_STRING = "Plant_Flora"
ANIMAL_ANNOTATION_STRING = "Animal_Fauna"
LOCATION_ANNOTATION_STRING = "Location_Place"
TAXON_ANNOTATION_STRING = "Taxon"
MISC_ANNOTATION_STRING = "Miscellaneous"

ANNOTATION_PRIORITY = [
    PLANT_ANNOTATION_STRING,
    ANIMAL_ANNOTATION_STRING,
    TAXON_ANNOTATION_STRING,
    LOCATION_ANNOTATION_STRING,
    MISC_ANNOTATION_STRING,
]

IGNORE_AS_NAMED_ENTITY = {"oder", "and"}

SUBJECT_STRING = "subject"
PREDICATE_STRING = "predicate"
OBJECT_STRING = "object"
RELATIONSHIP_STRING = "relationship"

# TextAnnotator
TAXON_CONTEXT_KEYWORD = "taxon"
LOCATION_CONTEXT_KEYWORD = "location"
PREDICATE_CONTEXT_KEYWORD = "predicate"
PREDICATE_VALUE_CONTEXT_KEYWORD = "predicate_value"

# Databases
ENABLE_FALLBACK_DATABASE = True
FALLBACK_DATABASE_CLASS = "enhanced_search.databases.key_value.SimpleKeyValueDatabase"
FALLBACK_DATABASE_DATA = {
    "pflanze": '{"Plant_Flora": [["https://www.biofid.de/ontology/pflanzen", 3]]}',
    "quercus": '{"Plant_Flora": [["https://www.biofid.de/ontology/quercus", 3]]}',
    "quercus sylvestris": '{"Plant_Flora": '
    '[["https://www.biofid.de/ontology/quercus_sylvestris", 3]]}',
    "fagus": '{"Plant_Flora": [["https://www.biofid.de/ontology/fagus", 3]]}',
    "fagus sylvatica": '{"Plant_Flora": '
    '[["https://www.biofid.de/ontology/fagus_sylvatica", 3]]}',
    "fagus sylvatica f. pendula (lodd.) dippel": '{"Plant_Flora": [['
    '"https://www.biofid.de/ontology/fagus_sylvatica_pendula", 3]]}',
    "deutschland": '{"Location_Place": [['
    '"https://sws.geonames.org/deutschland", 3]]}',
    "paris": '{"Location_Place": [["https://sws.geonames.org/paris", 3]],'
    '"Plant_Flora": [["https://www.biofid.de/ontology/paris"'
    ", 3]]}",
    "rot": '{"Miscellaneous": [["https://pato.org/red_color", 3]]}',
    "blüte": '{"Miscellaneous": [["https://pato.org/flower_part", 2]]}',
    "gelb blüte": '{"Miscellaneous": [["https://flopo.org/yellow_flower", 3]]}',
    "oder": '{"Location_Place": [["https://sws.geonames.org/oder_river", 3]]}',
    "vogel": '{"Animal_Fauna": [["https://www.biofid.de/ontology/voegel", 3]]}',
}

# See module factories.DatabaseFactory for an example of how databases are configured.
DATABASES: dict = {}


# Semantic Engines
# Probably you only need one, but you never know...
# For how to configure, see factories.SemanticEngineFactory
SEMANTIC_ENGINES: dict = {}
