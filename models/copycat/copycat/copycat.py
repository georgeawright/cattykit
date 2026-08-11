import json
import random

from cattykit.logging import ModelEvent, ModelLogger, NullLogger

from .answer_builder import AnswerBuilder
from .codelet_result import Finish, Fizzle
from .codelets import (
    BottomUpBondScout,
    BottomUpCorrespondenceScout,
    ReplacementFinder,
)
from .coderack import Coderack
from .slipnet import Slipnet
from .snag_exception import SnagException
from .workspace import Workspace
from .workspace_objects import Group, Letter
from .workspace_structures import Bond, Description

DESCRIPTION_TESTERS = {
    # LENGTH
    "length_is_one": lambda x: isinstance(x, Group) and len(x) == 1,
    "length_is_two": lambda x: isinstance(x, Group) and len(x) == 2,
    "length_is_three": lambda x: isinstance(x, Group) and len(x) == 3,
    "length_is_four": lambda x: isinstance(x, Group) and len(x) == 4,
    "length_is_five": lambda x: isinstance(x, Group) and len(x) == 5,
    # STRING POSITION
    "is_leftmost": lambda x: not x.spans_whole_string and x.leftmost_in_string,
    "is_rightmost": lambda x: not x.spans_whole_string and x.rightmost_in_string,
    "is_middle": lambda x: (
        any(
            neighbour.group is None and neighbour.is_leftmost_in_string()
            for neighbour in x.left_neighbours
        )
        and any(
            neighbour.group is None and neighbour.is_rightmost_in_string()
            for neighbour in x.right_neighbours
        )
    ),
    "is_single": lambda x: isinstance(x, Letter) and x.spans_whole_string,
    "is_whole": lambda x: isinstance(x, Group) and x.spans_whole_string,
    # ALPHABETIC POSITION
    "is_first": lambda x: x.get_descriptor("letter_category") == "a",
    "is_last": lambda x: x.get_descriptor("letter_category") == "z",
    # OBJECT TYPE
    "is_letter_object": lambda x: isinstance(x, Letter),
    "is_group_object": lambda x: isinstance(x, Group),
}


class Copycat:
    def __init__(
        self,
        slipnet: Slipnet,
        coderack: Coderack,
        workspace: Workspace,
        time_step_length: int,
        initially_clamped_nodes: list[str],
        initial_slipnode_clamp_time: int,
        logger: ModelLogger | None = None,
    ):
        self.slipnet = slipnet
        self.coderack = coderack
        self.workspace = workspace
        self.temperature = 1.0
        self.time_step_length = time_step_length
        self.initially_clamped_nodes = initially_clamped_nodes
        self.initial_slipnode_clamp_time = initial_slipnode_clamp_time
        self.translated_rule = None
        self.found_answer = False
        self.snag_condition = False
        self.snag_object = False
        self.clamp_temperature = False
        self.logger = logger if logger is not None else NullLogger()

    def close(self) -> None:
        """Copycat owns no resources"""

    @classmethod
    def from_json(
        cls,
        slipnet_json_file: str,
        coderack_json_file: str,
        hyperparameters_file: str,
        logger: ModelLogger | None = None,
    ):
        with open(hyperparameters_file) as f:
            hyperparameters = json.load(f)
        with open(slipnet_json_file) as f:
            slipnet_json = json.load(f)
        slipnet = Slipnet.from_json(
            slipnet_json,
            DESCRIPTION_TESTERS,
            workspace_activation=hyperparameters["workspace_activation"],
            full_activation_threshold=hyperparameters["full_activation_threshold"],
            full_activation_probability_exponent=hyperparameters[
                "full_activation_probability_exponent"
            ],
            initially_clamped_nodes=hyperparameters["initially_clamped_nodes"],
        )
        with open(coderack_json_file) as f:
            coderack_json = json.load(f)
        coderack = Coderack.from_json(coderack_json)
        workspace = Workspace.setup()
        return cls(
            slipnet,
            coderack=coderack,
            workspace=workspace,
            time_step_length=hyperparameters["time_step_length"],
            initially_clamped_nodes=hyperparameters["initially_clamped_nodes"],
            initial_slipnode_clamp_time=hyperparameters["initial_slipnode_clamp_time"],
            logger=logger,
        )

    def solve(self, string: str) -> None:
        """
        Solve a string analogy problem (e.g. "abc -> abd ==> ijk -> ?")
        """
        self.logger.log(ModelEvent.create("copycat", "run_started", problem=string))
        try:
            self._add_letters_to_workspace(string)
            self._add_initial_descriptions_to_workspace()
            self._post_initial_codelets()
            self.slipnet.update_activations()
            self.run()
        finally:
            self.logger.log(
                ModelEvent.create(
                    "copycat",
                    "run_finished",
                    codelets_run=self.coderack.number_of_codelets_run,
                    found_answer=self.found_answer,
                )
            )

    def _add_letters_to_workspace(self, string: str):
        """
        Initialize workspace with a problem (e.g. "abc -> abd ==> ijk -> ?")
        """
        initial_and_modified, target_and_answer = string.split("==>")
        initial_string, modified_string = initial_and_modified.split("->")
        target_string, answer_string = target_and_answer.split("->")
        answer_string = answer_string.split("?")[0]
        self.workspace.initial_string.letters = [
            Letter(
                string=self.workspace.initial_string,
                letter_category=self.slipnet[char],
                string_position=i,
            )
            for i, char in enumerate(initial_string.strip())
        ]
        self.workspace.initial_string.distribution_of_bond_counts = [
            i for i in range(len(initial_string.strip()) - 1)
        ]
        self.workspace.modified_string.letters = [
            Letter(
                string=self.workspace.modified_string,
                letter_category=self.slipnet[char],
                string_position=i,
            )
            for i, char in enumerate(modified_string.strip())
        ]
        self.workspace.target_string.letters = [
            Letter(
                string=self.workspace.target_string,
                letter_category=self.slipnet[char],
                string_position=i,
            )
            for i, char in enumerate(target_string.strip())
        ]
        self.workspace.target_string.distribution_of_bond_counts = [
            i for i in range(len(target_string.strip()) - 1)
        ]
        self.workspace.answer_string.letters = [
            Letter(
                string=self.workspace.answer_string,
                letter_category=self.slipnet[char],
                string_position=i,
            )
            for i, char in enumerate(answer_string.strip())
        ]

    def _add_initial_descriptions_to_workspace(self):
        for string in [
            self.workspace.initial_string,
            self.workspace.modified_string,
            self.workspace.target_string,
        ]:
            for letter in string.letters:
                letter.descriptions.append(
                    Description(
                        letter,
                        self.slipnet["object_category"],
                        self.slipnet["letter"],
                    )
                )
                letter.descriptions.append(
                    Description(
                        letter,
                        self.slipnet["letter_category"],
                        letter.letter_category,
                    )
                )
            if len(string) > 1:
                string.letters[0].descriptions.append(
                    Description(
                        string.letters[0],
                        self.slipnet["string_position_category"],
                        self.slipnet["leftmost"],
                    )
                )
                string.letters[-1].descriptions.append(
                    Description(
                        string.letters[-1],
                        self.slipnet["string_position_category"],
                        self.slipnet["rightmost"],
                    )
                )
            else:
                string.letters[0].descriptions.append(
                    Description(
                        string.letters[0],
                        self.slipnet["string_position_category"],
                        self.slipnet["single"],
                    )
                )
            if len(string) == 3:
                string.letters[1].descriptions.append(
                    Description(
                        letter,
                        self.slipnet["string_position_category"],
                        self.slipnet["middle"],
                    )
                )

    def _post_initial_codelets(self):
        for _ in range(2 * len(self.workspace.objects)):
            self.coderack.post(
                BottomUpBondScout(
                    urgency_bin=2,
                    coderack=self.coderack,
                    workspace=self.workspace,
                    slipnet=self.slipnet,
                ),
                self.temperature,
            )
            self.coderack.post(
                ReplacementFinder(
                    urgency_bin=2,
                    coderack=self.coderack,
                    workspace=self.workspace,
                    slipnet=self.slipnet,
                ),
                self.temperature,
            )
            self.coderack.post(
                BottomUpCorrespondenceScout(
                    urgency_bin=2,
                    coderack=self.coderack,
                    workspace=self.workspace,
                    slipnet=self.slipnet,
                ),
                self.temperature,
            )

    def run(self):
        while True:
            if self.coderack.number_of_codelets_run % self.time_step_length == 0:
                self.update()
            if self.coderack.empty():
                self._clamp_initially_clamped_nodes()
                self._post_intial_codelets()
            self.step()
            if self.translated_rule is None:
                continue
            try:
                answer_builder = AnswerBuilder(self.slipnet, self.workspace)
                answer_builder.build()
                self.found_answer = True
                self.logger.log(
                    ModelEvent.create(
                        "copycat",
                        "answer_found",
                        answer="".join(
                            letter.letter_category.name
                            for letter in self.workspace.answer_string.letters
                        ),
                    )
                )
                break
            except SnagException:
                self.logger.log(ModelEvent.create("copycat", "snag_encountered"))
                self.handle_snag()

    def update(self):
        """Update values of workspace structures and slipnet activations."""
        codelets_to_post = []
        self.workspace.update()
        if (
            self.coderack.number_of_codelets_run
            == self.initial_slipnode_clamp_time * self.time_step_length
        ):
            self._unclamp_initially_clamped_nodes()
        if self.snag_object and self.snag_condition:
            self._probabilistically_unsnag()
        if self.coderack.number_of_codelets_run > 0:
            self._update_temperature()
            codelets_to_post += self.workspace.get_bottom_up_codelets(
                self.slipnet, self.coderack, self.temperature
            )
            codelets_to_post += self.slipnet.get_top_down_codelets(
                self.coderack, self.workspace
            )
            self.slipnet.update_activations()
        if codelets_to_post:
            self.coderack.post_many(codelets_to_post, self.temperature)

    def step(self):
        """Run a single codelet."""
        codelet = self.coderack.choose(self.temperature)
        self.logger.log(
            ModelEvent.create(
                "copycat", "codelet_selected", codelet_type=str(type(codelet))
            )
        )
        result = codelet.run(self.temperature)
        data = {
            "codelet": type(codelet).__name__,
            "urgency_bin": codelet.urgency_bin,
            "temperature": self.temperature,
            "outcome": "finish" if isinstance(result, Finish) else "fizzle",
        }
        if isinstance(result, Fizzle):
            data["reason"] = result.reason.value
        self.logger.log(ModelEvent.create("copycat", "codelet_finished", **data))

    def _update_temperature(self):
        if self.clamp_temperature:
            return
        rule_weakness = (
            1 if not self.translated_rule else 1 - self.translated_rule.total_strength
        )
        self.temperature = self.workspace.total_unhappiness * 0.8 + rule_weakness * 0.2

    def _probabilistically_unsnag(self):
        """Check if new structures have been made since snag
        and probabilistically end snag."""
        new_structure_list = [
            s
            for s in self.workspace.structures
            if not isinstance(s, Bond) and s not in self.workspace.snag_structure_list
        ]
        unclamp_probability = (
            max([s.total_strength for s in new_structure_list])
            if new_structure_list
            else 0
        )
        if random.random() > unclamp_probability:
            self.snag_condition = False
            self.clamp_temperature = False
            for description in self.snag_object.descriptions:
                description.descriptor.unclamp()
            self.snag_object.set_clamp_salience = False

    def _clamp_initially_clamped_nodes(self):
        for node in self.initially_clamped_nodes:
            self.slipnet.clamp_node(node)

    def _unclamp_initially_clamped_nodes(self):
        for node in self.initially_clamped_nodes:
            self.slipnet.unclamp_node(node)

    def handle_snag(self):
        """If there is a snag in building the answer:
        - delete all proposed structures,
        - empty coderack,
        - raise and clamp temperature,
        - clamp activation of all descriptions of the offending object."""

    def delete_answer(self):
        pass
