"""Annotation Module

The Annotation module holds a text annotation pipeline and a query processing module.
The text annotation pipeline is split into the TextAnnotator, which is the
conductor for the text annotation, and the engines. The engines process the
single steps in the text annotation and can be customized and put into a specific
order to achieve the desired outcome.

The query processing is split into the processor, which has the corresponding task
to the TextAnnotator, only on the query level, and the engines. On the query
level the engines have the task to enrich the query with further data, if necessary.

This module also holds some dataclasses for allowing an isolated communication between
the single engines and the TextAnnotator.
"""

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


class RelationshipType(Enum):
    """A normalizing class for Relationships between Word objects."""

    AND = "and"
    OR = "or"


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
        """The Word's ID."""
        return f"{self.begin}/{self.end}"

    begin: int
    end: int
    text: str
    lemma: Optional[str] = None
    is_quoted: bool = False

    def __hash__(self):
        return hash((self.begin, self.end, self.text))

    def __str__(self):
        text = self.text
        if self.is_quoted:
            text = f'"{text}"'
        return text

    def __add__(self, other: "Word"):
        if not isinstance(other, Word):
            raise TypeError("Concatenating operation only possible with Word object!")
        begin = min(self.begin, other.begin)
        end = max(self.end, other.end)
        text = f"{self.text} {other.text}"
        lemma = f"{self.lemma} {other.lemma}"

        return Word(begin=begin, end=end, text=text, lemma=lemma)


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

    subject: Optional[Union[Set[Uri], LiteralString]] = None
    predicate: Optional[Set[Uri]] = None
    object: Optional[Union[Set[Uri], LiteralString]] = None
    relationship: Optional[RelationshipType] = None


@dataclass
class AnnotationResult:
    """Holds the current state of the annotation process."""

    text_language: Optional[str] = None
    tokens: List[LiteralString] = field(default_factory=list)
    named_entity_recognition: List[Annotation] = field(default_factory=list)
    literals: List[LiteralString] = field(default_factory=list)
    entity_linking: Dict[str, Dict[NamedEntityType, List[Uri]]] = field(
        default_factory=dict
    )
    disambiguated_annotations: Dict[Annotation, Annotation] = field(
        default_factory=dict
    )
    annotation_relationships: List[dict] = field(default_factory=list)


@dataclass
class Query:
    """Holds all data (enrichment) of a user query."""

    original_string: str
    annotations: List[Annotation] = field(default_factory=list)
    statements: List[Statement] = field(default_factory=list)
    literals: List[LiteralString] = field(default_factory=list)
