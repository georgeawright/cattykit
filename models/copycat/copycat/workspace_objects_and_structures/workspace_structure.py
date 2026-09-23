from copycat.tools import fake_reciprocal


class WorkspaceStructure:
    def __init__(self):
        self.internal_strength = 0
        self.external_strength = 0
        self.total_strength = 0
        self.total_weakness = 1

    def __hash__(self):
        return self.hash_id

    def update_strength_values(self):
        self.internal_strength = self.calculate_internal_strength()
        self.external_strength = self.calculate_external_strength()
        self.total_strength = self.calculate_total_strength()
        self.total_weakness = fake_reciprocal(
            (100 * self.total_strength) ** 0.95 / 100
        )

    def calculate_internal_strength(self):
        raise NotImplementedError("Subclasses must implement this method")

    def calculate_external_strength(self):
        raise NotImplementedError("Subclasses must implement this method")

    def calculate_total_strength(self):
        """Return the combined internal and external strength.

        The bounds of both component strengths are maintained by their
        respective calculators; the pure helper is contract-checked by
        CrossHair.
        """
        return self._combine_strengths(
            self.internal_strength,
            self.external_strength,
        )

    @staticmethod
    def _combine_strengths(internal_strength: float, external_strength: float) -> float:
        """Combine a structure's internally and externally derived strengths.

        pre: 0.0 <= internal_strength <= 1.0
        pre: 0.0 <= external_strength <= 1.0
        post: 0.0 <= _ <= 1.0
        post: _ >= internal_strength * internal_strength
        """
        return internal_strength * internal_strength + external_strength * fake_reciprocal(
            internal_strength
        )
