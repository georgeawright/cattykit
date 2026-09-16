"""Stable identifiers assigned by model loggers."""


class LoggerIdentifiers:
    """Provide the serial identifiers used in logged model events.

    Models pass their domain objects to these helpers rather than coupling their
    implementation to the storage format used by a logger.
    """

    def entity_id(self, entity: str, value: object) -> str:
        """Return the logged identifier for *value* in an entity namespace."""
        identifier = getattr(value, "hash_id", getattr(value, "name", value))
        return f"{entity}:{identifier}"

    def codelet_id(self, codelet: object) -> str:
        """Return the logged identifier for a codelet."""
        return self.entity_id("codelet", codelet)

    def object_id(self, obj: object) -> str:
        """Return the logged identifier for a workspace object or structure."""
        if isinstance(obj, str):
            return obj
        if type(obj).__name__ == "WorkspaceString":
            return f"string:{obj.string_id}"
        if not hasattr(obj, "hash_id") and not hasattr(obj, "name"):
            return type(obj).__name__.lower()
        return self.entity_id(type(obj).__name__.lower(), obj)

    def event_data(self, kind: str, data: dict[str, object]) -> dict[str, object]:
        """Extract storage-ready fields from the domain objects in an event."""
        result = dict(data)
        if "object" in result:
            result["object_id"] = self.object_id(result.pop("object"))
        if "codelet" in result and not isinstance(result["codelet"], str):
            codelet = result.pop("codelet")
            result.update(
                codelet_id=self.codelet_id(codelet),
                codelet_type=type(codelet).__name__,
                urgency_bin=codelet.urgency_bin,
                birth_time=codelet.birth_time,
                arguments={
                    "proposed_structure": getattr(codelet, "proposed_structure", None)
                },
            )

        entity = kind.rsplit("_", maxsplit=1)[0]
        entity_key = "rule" if entity == "translated_rule" else entity
        value = result.get(entity_key)
        if entity_key in {
            "letter",
            "description",
            "bond",
            "group",
            "correspondence",
            "replacement",
            "rule",
        } and value is not None:
            result.pop(entity_key)
            result[f"{entity_key}_id"] = self.entity_id(entity_key, value)
            self._entity_attributes(entity_key, value, result)

        mapping = result.pop("concept_mapping", None)
        if mapping is not None:
            correspondence = result.pop("correspondence", None)
            if correspondence is not None:
                result["correspondence_id"] = self.entity_id(
                    "correspondence", correspondence
                )
                result["concept_mapping_id"] = self.entity_id(
                    "concept_mapping", mapping
                )
            for attribute in (
                "source_facet",
                "target_facet",
                "source_descriptor",
                "target_descriptor",
            ):
                result[attribute] = getattr(mapping, attribute).name
            result["label"] = None if mapping.label is None else mapping.label.name
        return result

    def _entity_attributes(
        self, entity: str, value: object, result: dict[str, object]
    ) -> None:
        if entity == "letter":
            result.update(
                string_id=value.string.string_id,
                position=value.left_position,
                letter_category=value.letter_category.name,
            )
        elif entity == "description":
            result.update(
                object_id=self.object_id(value.argument_object),
                facet=value.facet.name,
                descriptor=value.descriptor.name,
            )
        elif entity == "bond":
            result.update(
                string_id=value.string.string_id,
                source_id=self.object_id(value.source),
                target_id=self.object_id(value.target),
                bond_category=value.bond_category.name,
                direction_category=self._name(value.direction_category),
                bond_facet=value.bond_facet.name,
                source_descriptor=value.source_descriptor.name,
                target_descriptor=value.target_descriptor.name,
            )
        elif entity == "group":
            result.update(
                string_id=value.string.string_id,
                group_category=value.group_category.name,
                direction_category=self._name(value.direction_category),
                bond_category=value.bond_category.name,
                bond_facet=self._name(value.bond_facet),
                left_position=value.left_position,
                right_position=value.right_position,
                members=[self.object_id(member) for member in value.objects],
                bonds=[self.entity_id("bond", bond) for bond in value.bonds],
            )
        elif entity in {"correspondence", "replacement"}:
            result.update(
                source_id=self.object_id(value.source),
                target_id=self.object_id(value.target),
            )
        elif entity == "rule":
            result.update(
                **{
                    attribute: self._name(getattr(value, attribute))
                    for attribute in (
                        "source_object_category",
                        "source_facet",
                        "source_descriptor",
                        "target_object_category",
                        "target_descriptor",
                        "replaced_facet",
                        "relation",
                    )
                }
            )

    @staticmethod
    def _name(value: object | None) -> str | None:
        return None if value is None else value.name
