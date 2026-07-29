from dataclasses import dataclass
from enum import StrEnum


class FizzleReason(StrEnum):
    NO_OBJECTS = "No objects in workspace"
    NO_POSSIBLE_DESCRIPTORS = "No possible descriptors for chosen object"
    NO_RELEVANT_DESCRIPTIONS = "No relevant descriptions for chosen object"
    NO_RELEVANT_HAS_PROPERTY_LINKS = (
        "No relevant has-property links for chosen descriptor"
    )
    OBJECTS_NO_LONGER_EXIST = "Proposed structure's objects no longer exist"
    STRUCTURE_ALREADY_EXISTS = "Proposed structure already exists"
    REQUIRED_BONDS_NO_LONGER_EXIST = "Required bonds no longer exist"
    INCOMPATIBLE_STRUCTURES_WON = "Incompatible structures won the fight"
    PROPOSED_STRUCTURE_TOO_WEAK = "Proposed structure was not strong enough"
    NO_NEIGHBOR = "No neighboring object for chosen object"
    NO_COMMON_BOND_FACET = "No common bond facet between chosen objects"
    NO_DESCRIPTORS_FOR_BOND_FACET = "Chosen objects lack descriptors for bond facet"
    NO_BOND_CATEGORY = "No bond category between chosen descriptors"
    NO_DIRECTED_BOND_CATEGORY = "No directed bond category between chosen descriptors"
    BOND_CATEGORY_DOES_NOT_MATCH = "Bond category does not match requested category"
    NO_BONDS = "No bonds in chosen string"
    OBJECT_SPANS_WHOLE_STRING = "Chosen object already spans the whole string"
    NO_FIRST_BOND = "No bond in chosen direction"
    BOND_DIRECTION_DOES_NOT_MATCH = "Bond direction does not match requested direction"
    BONDS_DO_NOT_SPAN_STRING = "Bonds do not span the whole string"
    NO_COMPATIBLE_GROUP_BONDS = "No compatible bonds for a group"
    INCOMPATIBLE_OBJECT_SPANS = "Only one chosen object spans its whole string"
    NO_CONCEPT_MAPPINGS = "No slippable concept mappings between chosen objects"
    NO_DISTINGUISHING_CONCEPT_MAPPINGS = (
        "No distinguishing concept mappings between chosen objects"
    )
    NO_OBJECTS_WITH_DESCRIPTOR = (
        "No objects with the chosen descriptor in the target string"
    )
    NOT_ALL_CONCEPT_MAPPINGS_RELEVANT = (
        "Not all concept mappings are relevant to the proposed correspondence"
    )
    NOT_ALL_REPLACEMENTS_FOUND = "Not all replacements have been found"
    NO_INTIAL_DESCRIPTIONS = "No initial descriptions"
    NO_MODIFIED_DESCRIPTIONS = "No modified descriptions"
    LETTER_ALREADY_HAS_REPLACEMENT = "Letter already has replacement"


@dataclass(frozen=True)
class Finish:
    pass


@dataclass(frozen=True)
class Fizzle:
    reason: FizzleReason


CodeletResult = Finish | Fizzle
