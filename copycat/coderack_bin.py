import random


class CoderackBin:
    def __init__(self):
        self.codelets = []

    def __len__(self):
        return len(self.codelets)

    @property
    def total_urgency(self):
        return sum([codelet.urgency for codelet in self.codelets])

    def add(self, codelet):
        self.codelets.append(codelet)

    def remove(self, codelet):
        self.codelets.remove(codelet)

    def choose(self):
        chosen_codelet = random.choice(self.codelets)
        self.remove(chosen_codelet)
        return chosen_codelet
