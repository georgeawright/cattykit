from copycat.codelet import Codelet


class Breaker(Codelet):
    def __init__(self, urgency_bin: int):
        super().__init__(urgency_bin=urgency_bin)
