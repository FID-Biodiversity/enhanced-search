from dataclasses import dataclass, field
from enum import Enum
from typing import Set, Optional, List, Union


class NamedEntityType(Enum):
    """A normalizing class for Named Entity type names."""

    TAXON = "Taxon"
    ANIMAL = "Animal"
    PLANT = "Plant"
    LOCATION = "Location"


@dataclass
class Uri:
    """A representation of an URI."""

    url: str
    is_property: bool = False  # If True, this URI is on second position in
    # a triple. On third position otherwise
    labels: Set[str] = field(default_factory=set)
    parent: Optional["Uri"] = None
    children: Set["Uri"] = field(default_factory=set)


@dataclass
class Feature:
    """Holds feature data (in the form of [predicate] [value]) and should
    always be associated with an Annotation.
    """

    property: Optional[Union[str, Uri]] = None
    value: Optional[Union[str, Uri, int]] = None


@dataclass
class Annotation:
    """A messenger class for a single text annotation."""

    begin: int
    end: int
    text: str
    uris: Set[Uri] = field(default_factory=set)
    named_entity_type: Optional[NamedEntityType] = None
    ambiguous_annotations: Set["Annotation"] = field(default_factory=set)
    feature: List[Feature] = field(default_factory=list)

    def __hash__(self):
        return hash((self.begin, self.end, self.named_entity_type))


@dataclass
class AnnotationResult:
    """Holds the current state of the annotation process."""

    named_entity_recognition: List[Annotation] = field(default_factory=list)
