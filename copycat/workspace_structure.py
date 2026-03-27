class WorkspaceStructure:
    def __init__(self):
        self.internal_strength = 0
        self.external_strength = 0
        self.total_strength = 0

    def update_strength_values(self):
        self.internal_strength = self.calculate_internal_strength()
        self.external_strength = self.calculate_external_strength()
        self.total_strength = self.calculate_total_strength()

    def calculate_internal_strength(self):
        raise NotImplementedError("Subclasses must implement this method")

    def calculate_external_strength(self):
        raise NotImplementedError("Subclasses must implement this method")

    def calculate_total_strength(self):
        (
            self.internal_strength * self.internal_strength
            + self.external_strength * (1 - self.internal_strength)
        )
