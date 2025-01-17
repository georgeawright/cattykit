import random

NO_OF_URGENCY_BINS = 7
# in the original copycat implementation,
# these are extremely-low, very-low, low, medium, high, very-high, extremely-high

MAX_CODERACK_POPULATION = 100 # check this

class Coderack:
    def __init__(self):
        self.urgency_bins = [{} for _ in range(NO_OF_URGENCY_BINS)]
        self.codelets = {}

    @property
    def population(self):
        return sum(len(urgency_bin) for urgency_bin in self.urgency_bins)

    @property
    def total_urgency(self):
        return sum(codelet.urgency for codelet in self.codelets)

    def empty(self):
        self.urgency_bins = []
        self.codelets = {}

    def post_codelet(self, codelet: "Codelet", remove_excess: bool=False):
        if self.population > MAX_CODERACK_POPULATION and remove_excess:
            self.remove_codelets(1)
        urgency_bin = (codelet.urgency * 10) % NO_OF_URGENCY_BINS
        self.urgency_bins[urgency_bin][codelet.codelet_id] = codelet
        self.codelets[codelet.codelet_id] = codelet

    def remove_codelets(self, count: int):
        """probabilistically remove count codelets.
        More likely to remove low urgency, older codelets.
        If codelet is not a breaker and its argument is not rule or description,
        delete the argument from the workspace."""
        raise NotImplementedError

    def choose_codelet(self):
        chosen_urgency_bin = random.choice(
            self.urgency_bins,
            weights=[
                sum(codelet.urgency for codelet in urgency_bin)
                for urgency_bin in self.urgency_bins
            ],
        )
        chosen_codelet_id = random.choice(chosen_urgency_bin)
        chosen_codelet = self.codelets[chosen_codelet_id]
        chosen_urgency_bin.remove(chosen_codelet_id)
        self.codelets.remove(chosen_codelet_id)

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
                self.post_codelet(ImportantObjectCorrespondenceScout(), self.urgency_bins[2])
        if random.random() > 0.5:
            for _ in range(self.codelets_to_post["rule"]):
                self.post_codelet(RuleScout(), self.urgency_bins[2])
        if random.random() > 0.5:
            for _ in range(self.codelets_to_post["translated-rule"]):
                urgency_bin = self.urgency_bins[2] if self.temperature > 25 else self.urgency_bins[6]
                self.post_codelet(TranslatedRule(), urgency_bin)
        self.post_codelet(Breaker(), self.urgency_bins[0])
        


