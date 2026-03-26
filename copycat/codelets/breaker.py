from copycat.codelet import Codelet


class Breaker(Codelet):
    def __init__(self, birth_time: int, urgency_bin: int):
        super().__init__(birth_time=birth_time, urgency_bin=urgency_bin)
