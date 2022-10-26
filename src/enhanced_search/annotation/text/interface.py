from typing import Protocol, Set, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class NamedEntityType(Enum):
    """A normalizing class for Named Entity type names."""

    TAXON = "Taxon"
    ANIMAL = "Animal"
    PLANT = "Plant"
    LOCATION = "Location"


@dataclass
class Annotation:
    """A messenger class for a single text annotation."""

    begin: int
    end: int
    text: str
    uris: Set[str] = field(default_factory=set)
    named_entity_type: Optional[NamedEntityType] = None


class TextAnnotator(Protocol):
    """An interface class for all text annotation tasks."""

    def annotate(self, text: str) -> List[Annotation]:
        """Annotates the given text and returns a list of Annotations."""
        ...
