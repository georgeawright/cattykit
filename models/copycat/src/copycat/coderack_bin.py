import random


class CoderackBin:
    def __init__(self, urgency_value):
        self.urgency_value = urgency_value
        self.codelets = []

    def __len__(self):
        return len(self.codelets)

    @property
    def total_urgency(self):
        return self.urgency_value * len(self.codelets)

    def add(self, codelet):
        self.codelets.append(codelet)

    def remove(self, codelet):
        self.codelets.remove(codelet)

    def choose(self):
        chosen_codelet = random.choice(self.codelets)
        self.remove(chosen_codelet)
        return chosen_codelet
