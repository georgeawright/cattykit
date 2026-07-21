from dataclasses import dataclass
from enum import StrEnum


class FizzleReason(StrEnum):
    NO_OBJECTS = "No objects in workspace"
    NO_POSSIBLE_DESCRIPTORS = "No possible descriptors for chosen object"
    NO_RELEVANT_DESCRIPTIONS = "No relevant descriptions for chosen object"
    NO_RELEVANT_HAS_PROPERTY_LINKS = (
        "No relevant has-property links for chosen descriptor"
    )


@dataclass(frozen=True)
class Finish:
    pass


@dataclass(frozen=True)
class Fizzle:
    reason: FizzleReason


CodeletResult = Finish | Fizzle
