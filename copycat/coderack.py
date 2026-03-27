from __future__ import annotations
import random

from .coderack_bin import CoderackBin

# in the original copycat implementation, there were 7 urgency bins:
# these are extremely-low, very-low, low, medium, high, very-high, extremely-high
# quantizing urgency into 7 levels reduces jitter and the chasing of tiny differences
# it avoids starving low urgency codelets by giving them some small chance of running.

URGENCY_TEMPERATURE_FUNCTION = lambda u, t: (u + 1) ** ((110 - t) / 15)


class Coderack:
    def __init__(
        self, urgency_bins: list, urgency_lookup_table: list, max_population: int
    ):
        self._urgency_bins = urgency_bins
        self.urgency_lookup_table = urgency_lookup_table
        self.max_population = max_population
        self.number_of_codelets_run = 0
        self.codelets_to_post = []

    @classmethod
    def create(cls, number_of_bins: int, max_population: int) -> Coderack:
        urgency_bins = [CoderackBin(i + 1) for i in range(number_of_bins)]
        urgency_temperature_lookup_table = [
            [URGENCY_TEMPERATURE_FUNCTION(u, t) for u in range(number_of_bins)]
            for t in range(101)
        ]
        return cls(urgency_bins, urgency_temperature_lookup_table, max_population)

    @classmethod
    def from_json(cls, json_data: dict) -> Coderack:
        return cls.create(json_data["number_of_bins"], json_data["max_population"])

    @property
    def codelets(self):
        return [
            codelet
            for urgency_bin in self._urgency_bins
            for codelet in urgency_bin.codelets
        ]

    @property
    def population(self) -> int:
        return sum([len(urgency_bin) for urgency_bin in self._urgency_bins])

    def is_empty(self) -> bool:
        return self.population == 0

    def get_urgency_bin(self, urgency_level):
        return self._urgency_bins[urgency_level - 1]

    def get_urgency_bin_weights(self, temperature: float):
        temperature_index = int(round(temperature * 100, 0))
        return self.urgency_lookup_table[temperature_index]

    def empty(self):
        self.urgency_bins = [
            CoderackBin(i + 1) for i, _ in enumerate(self._urgency_bins)
        ]

    def post(self, codelet: "Codelet", temperature: float):
        if self.population >= self.max_population:
            self.remove_codelets(1, temperature)
        self._post(codelet)

    def post_many(self, codelets: list, temperature: float):
        number_of_codelets_to_remove = max(
            self.population + len(codelets) - self.max_population, 0
        )
        if number_of_codelets_to_remove > 0:
            self.remove_codelets(number_of_codelets_to_remove, temperature)
        for codelet in codelets:
            self._post(codelet)

    def remove_codelets(self, number_to_remove: int, temperature: float):
        """Probabilistically remove codelets.
        More likely to remove low urgency, older codelets."""
        urgency_bin_weights = self.get_urgency_bin_weights(temperature)
        removal_probabilities = [
            (self.number_of_codelets_run - codelet.birth_time)
            * (1 + urgency_bin_weights[-1] - urgency_bin_weights[codelet.urgency_bin])
            for codelet in self.codelets
        ]
        codelets_to_remove = random.choices(
            self.codelets,
            weights=removal_probabilities,
            k=number_to_remove,
        )
        for codelet in codelets_to_remove:
            self._remove(codelet)

    def choose(self, temperature: float):
        chosen_urgency_bin = random.choices(
            self._urgency_bins,
            weights=[
                urgency_bin.total_urgency * urgency_bin_weight
                for urgency_bin, urgency_bin_weight in zip(
                    self._urgency_bins, self.get_urgency_bin_weights(temperature)
                )
            ],
            k=1,
        )[0]
        chosen_codelet = random.choice(chosen_urgency_bin.codelets)
        self.number_of_codelets_run += 1
        return chosen_codelet

    def _post(self, codelet):
        self.get_urgency_bin(codelet.urgency_bin).add(codelet)
        codelet.birth_time = self.number_of_codelets_run

    def _remove(self, codelet):
        """Remove codelet from coderack and
        If codelet is not a breaker and its argument is not rule or description,
        delete the argument from the workspace."""
        print(codelet)
        print(codelet.urgency_bin)
        print(self.get_urgency_bin(codelet.urgency_bin).codelets)
        self.get_urgency_bin(codelet.urgency_bin).remove(codelet)
        # TODO: remove arguments of workspace structures
