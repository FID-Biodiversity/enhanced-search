from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Union


class NamedEntityType(Enum):
    """A normalizing class for Named Entity type names."""

    TAXON = "Taxon"
    ANIMAL = "Animal"
    PLANT = "Plant"
    LOCATION = "Location"
    MISCELLANEOUS = "Miscellaneous"


@dataclass
class Uri:
    """A representation of an URI."""

    url: str

    # Positions can be 2 (its a predicate) or 3 (its an object)
    position_in_triple: int = 3
    is_safe: bool = False

    labels: Set[str] = field(default_factory=set)
    parent: Optional["Uri"] = None
    children: Set["Uri"] = field(default_factory=set)

    def __hash__(self):
        return hash(self.url)


@dataclass
class Word:
    """A base class for any word in a query.
    A word can contain multiple tokens!
    """

    @property
    def id(self):
        return f"{self.begin}/{self.end}"

    begin: int
    end: int
    text: str

    def __hash__(self):
        return hash((self.begin, self.end, self.text))


@dataclass
class LiteralString(Word):
    """Any token or multi-token in a given query is a LiteralString."""

    is_safe: bool = False

    def __hash__(self):
        return hash((self.begin, self.end, self.text))


@dataclass
class Feature:
    """Holds feature data (in the form of [predicate] [value]) and should
    always be associated with an Annotation.
    """

    property: Optional[Union[LiteralString, Set[Uri]]] = None
    value: Optional[Union[LiteralString, Set[Uri]]] = None


@dataclass
class Annotation(Word):
    """A text annotation."""

    uris: Set[Uri] = field(default_factory=set)
    named_entity_type: Optional[NamedEntityType] = None
    ambiguous_annotations: Set["Annotation"] = field(default_factory=set)
    features: List[Feature] = field(default_factory=list)

    def __hash__(self):
        return hash((self.begin, self.end, self.named_entity_type))


@dataclass
class Statement:
    """A statement extracted from the query.
    It has the same semantic as a triple, since it is more or less that.
    However, none of the three data fields (subject, predicate, object) is demanded.
    So, there can be a Statement with only predicate and object given. Or only with
    subject and object.
    """

    subject: Optional[Set[Uri]] = None
    predicate: Optional[Set[Uri]] = None
    object: Optional[Set[Uri], LiteralString] = None


@dataclass
class AnnotationResult:
    """Holds the current state of the annotation process."""

    named_entity_recognition: List[Annotation] = field(default_factory=list)
    literals: List[LiteralString] = field(default_factory=list)
    entity_linking: Dict[Annotation, List[Uri]] = field(default_factory=dict)
    disambiguated_annotations: Dict[Annotation, Annotation] = field(
        default_factory=dict
    )
    annotation_relationships: List[Statement] = field(default_factory=list)


@dataclass
class Query:
    """Holds all data (enrichment) of a user query."""

    original_string: str
    annotations: List[Annotation] = field(default_factory=list)
    statements: List[Statement] = field(default_factory=list)
    literals: List[LiteralString] = field(default_factory=list)
