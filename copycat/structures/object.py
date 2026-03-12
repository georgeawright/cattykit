from copycat.structure import Structure


class Object(Structure):
    def __init__(self, string, left_position: int, right_position: int):
        self.string = string
        self.left_position = left_position
        self.right_position = right_position
        self.raw_importance = 0
        self.relative_importance = 0
        self.intra_string_unhappiness = 0
        self.inter_string_unhappiness = 0
        self.total_unhappiness = 0
        self.intra_string_salience = 0
        self.inter_string_salience = 0
        self.total_salience = 0
        self.descriptions = []
        self.extrinsic_descriptions = []
        self.outgoing_bonds = []
        self.incoming_bonds = []
        self.group = None
        self.replacement = None
        self.correspondence = None
        self.is_changed_letter = False
        self.is_new_answer_letter = False
        self.salience_is_clamped = False
