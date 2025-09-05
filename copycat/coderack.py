import random

from .coderack_bin import CoderackBin

# in the original copycat implementation, there were 7 urgency bins:
# these are extremely-low, very-low, low, medium, high, very-high, extremely-high
# quantizing urgency into 7 levels reduces jitter and the chasing of tiny differences
# it avoids starving low urgency codelets by giving them some small chance of running.

MAX_CODERACK_POPULATION = 100  # check this
URGENCY_TEMPERATURE_FUNCTION = lambda u, t: (u + 1) ** ((110 - t) / 15)


class Coderack:
    def __init__(self, urgency_bins: list, urgency_lookup_table: list):
        self.urgency_bins = urgency_bins
        self.urgency_lookup_table = urgency_lookup_table
        self.number_of_codelets_run = 0

    @classmethod
    def create(cls, number_of_bins):
        urgency_bins = [CoderackBin() for _ in range(number_of_bins)]
        urgency_temperature_lookup_table = [
            [URGENCY_TEMPERATURE_FUNCTION(u, t) for u in range(urgency_bins)]
            for t in range(101)
        ]
        return cls(urgency_bins, urgency_temperature_lookup_table)

    @property
    def codelets(self):
        return [
            codelet
            for urgency_bin in self.urgency_bins
            for codelet in urgency_bin.codelets
        ]

    @property
    def population(self):
        return sum([len(urgency_bin) for urgency_bin in self.urgency_bins])

    def get_urgency_bin_weights(self, temperature: float):
        temperature_index = round(self.temperature * 100, 0)
        return self.urgency_lookup_table[temperature_index]

    def empty(self):
        self.urgency_bins = [CoderackBin() for _ in self.urgency_bins]

    def post(self, codelet: "Codelet", temperature: float):
        if self.population > MAX_CODERACK_POPULATION:
            self.remove_codelets(1, temperature)
        self._post(codelet)

    def post_many(self, codelets: list, temperature: float):
        number_of_codelets_to_remove = max(
            self.population + len(codelets) - MAX_CODERACK_POPULATION, 0
        )
        self.remove_codelets(number_to_remove, temperature)
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
        codelets_to_remove = random.choice(self.codelets, weights=removal_probabilities)
        for codelet in codelets_to_remove:
            self._remove(codelet)

    def choose(self, temperature: float):
        chosen_urgency_bin = random.choice(
            self.urgency_bins,
            weights=[
                urgency_bin.total_urgency * urgency_bin_weight
                for urgency_bin, urgency_bin_weight in zip(
                    self.urgency_bins, self.get_urgency_bin_weights(temperature)
                )
            ],
        )
        chosen_codelet = chosen_urgency_bin.choose()
        self.number_of_codelets_run += 1
        return codelet

    def _post(self, codelet):
        urgency_bin_number = (codelet.urgency * 10) % len(self.urgency_bins)
        self.urgency_bins[urgency_bin_number].add(codelet)
        codelet.birth_time = self.number_of_codelets_run

    def _remove(self, codelet):
        """Remove codelet from coderack and
        If codelet is not a breaker and its argument is not rule or description,
        delete the argument from the workspace."""
        self.urgency_bins[codelet.urgency_bin].remove(codelet)
        # TODO: remove arguments of workspace structures

    def post_bottom_up_codelets(self):
        """Adds bottom up codelets in amount and with urgency according to need."""
        if random.random() > 0.5:
            for _ in range(self.codelets_to_post["description"]):
                self.post_codelet(BottomUpDescriptionScout(), self.urgency_bins[2])
        if random.random() > 0.5:
            for _ in range(self.codelets_to_post["bond"]):
                self.post_codelet(BottomUpBondScout(), self.urgency_bins[2])
        if random.random() > 0.5:
            for _ in range(self.codelets_to_post["group"]):
                self.post_codelet(WholeStringGroupScout(), self.urgency_bins[2])
        if random.random() > 0.5:
            for _ in range(self.codelets_to_post["replacement"]):
                self.post_codelet(ReplacementFinder(), self.urgency_bins[2])
        if random.random() > 0.5:
            for _ in range(self.codelets_to_post["correspondence"]):
                self.post_codelet(BottomUpCorrespondenceScout(), self.urgency_bins[2])
                self.post_codelet(
                    ImportantObjectCorrespondenceScout(), self.urgency_bins[2]
                )
        if random.random() > 0.5:
            for _ in range(self.codelets_to_post["rule"]):
                self.post_codelet(RuleScout(), self.urgency_bins[2])
        if random.random() > 0.5:
            for _ in range(self.codelets_to_post["translated-rule"]):
                urgency_bin = (
                    self.urgency_bins[2]
                    if self.temperature > 25
                    else self.urgency_bins[6]
                )
                self.post_codelet(TranslatedRule(), urgency_bin)
        self.post_codelet(Breaker(), self.urgency_bins[0])
