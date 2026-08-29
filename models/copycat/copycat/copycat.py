import json
import random
from typing import Optional

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
from .workspace_structure import WorkspaceStructure
from .workspace_structures import Bond, Description

DESCRIPTION_TESTERS = {
    # LENGTH
    "length_is_one": lambda x: isinstance(x, Group) and len(x) == 1,
    "length_is_two": lambda x: isinstance(x, Group) and len(x) == 2,
    "length_is_three": lambda x: isinstance(x, Group) and len(x) == 3,
    "length_is_four": lambda x: isinstance(x, Group) and len(x) == 4,
    "length_is_five": lambda x: isinstance(x, Group) and len(x) == 5,
    # STRING POSITION
    "is_leftmost": lambda x: not x.spans_whole_string() and x.is_leftmost_in_string(),
    "is_rightmost": lambda x: not x.spans_whole_string() and x.is_rightmost_in_string(),
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
    "is_single": lambda x: isinstance(x, Letter) and x.spans_whole_string(),
    "is_whole": lambda x: isinstance(x, Group) and x.spans_whole_string(),
    # ALPHABETIC POSITION
    "is_first": lambda x: (lambda d: d.name == "a" if d is not None else False)(
        x.descriptor_with_facet_name("letter_category")
    ),
    "is_last": lambda x: (lambda d: d.name == "z" if d is not None else False)(
        x.descriptor_with_facet_name("letter_category")
    ),
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
        self.found_answer = False
        self.snag_condition = False
        self.snag_count = 0
        self.snag_structures: list[WorkspaceStructure] = []
        self.last_snag_time: Optional[int] = None
        self.clamp_temperature = False
        self.logger = logger if logger is not None else NullLogger()
        for component in (self.workspace, self.slipnet, self.coderack):
            if component is not None and hasattr(component, "set_logger"):
                component.set_logger(self.logger)

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

    def solve(self, string: str) -> str | None:
        """
        Solve a string analogy problem (e.g. "abc -> abd ==> ijk -> ?")
        """
        self.logger.log(
            ModelEvent.create(
                "copycat",
                "run_started",
                problem=string,
                time=self.coderack.number_of_codelets_run,
            )
        )
        try:
            self._add_letters_to_workspace(string)
            self._add_initial_descriptions_to_workspace()
            self._post_initial_codelets()
            self.slipnet.log_definition()
            self.slipnet.update_activations()
            self.run()
            return "".join(
                [
                    letter.letter_category.name
                    for letter in self.workspace.answer_string.letters
                ]
            )
        finally:
            self.logger.log(
                ModelEvent.create(
                    "copycat",
                    "run_finished",
                    codelets_run=self.coderack.number_of_codelets_run,
                    found_answer=self.found_answer,
                    temperature=self.temperature,
                    time=self.coderack.number_of_codelets_run,
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
        for i, char in enumerate(initial_string.strip()):
            self.workspace.initial_string.add_letter(
                Letter(
                    string=self.workspace.initial_string,
                    letter_category=self.slipnet[char],
                    string_position=i,
                )
            )
        self.workspace.initial_string.distribution_of_bond_counts = [
            i for i in range(len(initial_string.strip()))
        ]
        for i, char in enumerate(modified_string.strip()):
            self.workspace.modified_string.add_letter(
                Letter(self.workspace.modified_string, self.slipnet[char], i)
            )
        for i, char in enumerate(target_string.strip()):
            self.workspace.target_string.add_letter(
                Letter(self.workspace.target_string, self.slipnet[char], i)
            )
        self.workspace.target_string.distribution_of_bond_counts = [
            i for i in range(len(target_string.strip()))
        ]
        for i, char in enumerate(answer_string.strip()):
            self.workspace.answer_string.add_letter(
                Letter(self.workspace.answer_string, self.slipnet[char], i)
            )
        for role, value in (
            ("initial", initial_string.strip()),
            ("modified", modified_string.strip()),
            ("target", target_string.strip()),
            ("answer", answer_string.strip()),
        ):
            self.logger.log(
                ModelEvent.create(
                    "copycat",
                    "string_initialized",
                    string_id=role,
                    role=role,
                    value=value,
                )
            )

    def _add_initial_descriptions_to_workspace(self):
        for string in [
            self.workspace.initial_string,
            self.workspace.modified_string,
            self.workspace.target_string,
        ]:
            for letter in string.letters:
                letter.add_description(
                    Description(
                        letter,
                        self.slipnet["object_category"],
                        self.slipnet["letter"],
                    )
                )
                letter.add_description(
                    Description(
                        letter,
                        self.slipnet["letter_category"],
                        letter.letter_category,
                    )
                )
            if len(string) > 1:
                string.letters[0].add_description(
                    Description(
                        string.letters[0],
                        self.slipnet["string_position_category"],
                        self.slipnet["leftmost"],
                    )
                )
                string.letters[-1].add_description(
                    Description(
                        string.letters[-1],
                        self.slipnet["string_position_category"],
                        self.slipnet["rightmost"],
                    )
                )
            else:
                string.letters[0].add_description(
                    Description(
                        string.letters[0],
                        self.slipnet["string_position_category"],
                        self.slipnet["single"],
                    )
                )
            if len(string) == 3:
                string.letters[1].add_description(
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
                    urgency_bin=1,
                    coderack=self.coderack,
                    workspace=self.workspace,
                    slipnet=self.slipnet,
                ),
                self.temperature,
            )
            self.coderack.post(
                ReplacementFinder(
                    urgency_bin=1,
                    coderack=self.coderack,
                    workspace=self.workspace,
                    slipnet=self.slipnet,
                ),
                self.temperature,
            )
            self.coderack.post(
                BottomUpCorrespondenceScout(
                    urgency_bin=1,
                    coderack=self.coderack,
                    workspace=self.workspace,
                    slipnet=self.slipnet,
                ),
                self.temperature,
            )

    def run(self):
        while True:
            if self.coderack.number_of_codelets_run > 9999:
                break
            if self.coderack.number_of_codelets_run % self.time_step_length == 0:
                self.update()
            if self.coderack.is_empty():
                self._clamp_initially_clamped_nodes()
                self._post_initial_codelets()
            self.step()
            if self.workspace.translated_rule is None:
                continue
            try:
                answer_builder = AnswerBuilder(self.slipnet, self.workspace)
                previous_answer_letters = list(self.workspace.answer_string.letters)
                answer_builder.build()
                self._log_answer_letters(previous_answer_letters)
                self.found_answer = True
                self.logger.log(
                    ModelEvent.create(
                        "copycat",
                        "answer_found",
                        answer="".join(
                            letter.letter_category.name
                            for letter in self.workspace.answer_string.letters
                        ),
                        time=self.coderack.number_of_codelets_run,
                    )
                )
                break
            except SnagException:
                self.logger.log(
                    ModelEvent.create(
                        "copycat",
                        "snag_encountered",
                        time=self.coderack.number_of_codelets_run,
                    )
                )
                self.handle_snag()

    def _log_answer_letters(self, previous_answer_letters) -> None:
        """Record the answer-string replacement produced by AnswerBuilder."""
        time = self.coderack.number_of_codelets_run
        for letter in previous_answer_letters:
            self.logger.log(
                ModelEvent.create(
                    "copycat",
                    "letter_destroyed",
                    letter_id=f"letter:{letter.hash_id}",
                    time=time,
                )
            )
        for letter in self.workspace.answer_string.letters:
            self.logger.log(
                ModelEvent.create(
                    "copycat",
                    "letter_created",
                    letter_id=f"letter:{letter.hash_id}",
                    string_id="answer",
                    position=letter.left_position,
                    letter_category=letter.letter_category.name,
                    time=time,
                )
            )

    def update(self):
        """Update values of workspace structures and slipnet activations."""
        codelets_to_post = []
        self.workspace.update()
        if (
            self.coderack.number_of_codelets_run
            == self.initial_slipnode_clamp_time * self.time_step_length
        ):
            self._unclamp_initially_clamped_nodes()
        if self.workspace.snag_object and self.snag_condition:
            self._probabilistically_unsnag()
        if self.coderack.number_of_codelets_run > 0:
            self._update_temperature()
            codelets_to_post += self.workspace.get_bottom_up_codelets(
                self.slipnet, self.coderack, self.temperature
            )
            codelets_to_post += self.slipnet.get_top_down_codelets(
                self.coderack, self.workspace, self.temperature
            )
            self.slipnet.update_activations()
        if codelets_to_post:
            self.coderack.post_many(codelets_to_post, self.temperature)

    def step(self):
        """Run a single codelet."""
        codelet = self.coderack.choose(self.temperature)
        self.logger.log(
            ModelEvent.create(
                "copycat",
                "codelet_selected",
                codelet_id=f"codelet:{codelet.hash_id}",
                codelet_type=type(codelet).__name__,
                urgency_bin=codelet.urgency_bin,
                birth_time=codelet.birth_time,
                time=self.coderack.number_of_codelets_run,
            )
        )
        rule = self.workspace.rule
        translated_rule = self.workspace.translated_rule
        result = codelet.run(self.temperature)
        self._log_rule_changes(codelet, rule, translated_rule)
        data = {
            "codelet": type(codelet).__name__,
            "urgency_bin": codelet.urgency_bin,
            "temperature": self.temperature,
            "outcome": "finish" if isinstance(result, Finish) else "fizzle",
        }
        if isinstance(result, Fizzle):
            data["reason"] = result.reason.value
        self.logger.log(
            ModelEvent.create(
                "copycat",
                "codelet_finished",
                codelet_id=f"codelet:{codelet.hash_id}",
                time=self.coderack.number_of_codelets_run,
                **data,
            )
        )

    def _log_rule_changes(self, codelet, rule, translated_rule) -> None:
        """Record rule state, which is owned by Copycat rather than a component."""
        proposed_rule = getattr(codelet, "proposed_rule", None)
        if proposed_rule is not None:
            self._log_rule("rule_proposed", proposed_rule)
        if self.workspace.rule is not rule:
            if rule is not None:
                self._log_rule("rule_destroyed", rule)
            if self.workspace.rule is not None:
                self._log_rule("rule_created", self.workspace.rule)
        if self.workspace.translated_rule is not translated_rule:
            if translated_rule is not None:
                self._log_rule("translated_rule_destroyed", translated_rule)
            if self.workspace.translated_rule is not None:
                self._log_rule(
                    "translated_rule_created", self.workspace.translated_rule
                )

    def _log_rule(self, kind: str, rule) -> None:
        self.logger.log(
            ModelEvent.create(
                "copycat",
                kind,
                rule_id=f"rule:{rule.hash_id}",
                time=self.coderack.number_of_codelets_run,
                **{
                    attribute: None
                    if getattr(rule, attribute) is None
                    else getattr(rule, attribute).name
                    for attribute in (
                        "object_category_1",
                        "descriptor_1_facet",
                        "descriptor_1",
                        "object_category_2",
                        "descriptor_2",
                        "replaced_description_type",
                        "relation",
                    )
                },
            )
        )

    def _update_temperature(self):
        if self.clamp_temperature:
            return
        rule_weakness = self.workspace.rule.total_weakness if self.workspace.rule else 1
        self.temperature = self.workspace.total_unhappiness * 0.8 + rule_weakness * 0.2
        time = 0 if self.coderack is None else self.coderack.number_of_codelets_run
        self.logger.log(
            ModelEvent.create(
                "copycat",
                "attribute_updated",
                time=time,
                object_id="temperature",
                attribute="value",
                value=self.temperature,
            )
        )

    def _probabilistically_unsnag(self):
        """Check if new structures have been made since snag
        and probabilistically end snag."""
        new_structure_list = [
            structure
            for structure in self.workspace.structures
            if not isinstance(structure, Bond)
            and not any(
                [
                    structure.equates_to(snag_structure)
                    for snag_structure in self.snag_structures
                ]
            )
        ]
        unclamp_probability = (
            max([s.total_strength for s in new_structure_list])
            if new_structure_list
            else 0
        )
        if unclamp_probability > random.random():
            self.snag_condition = False
            self.clamp_temperature = False
            for description in self.workspace.snag_object.descriptions:
                self.slipnet.unclamp_node(description.descriptor.name)
            self.workspace.snag_object.salience_is_clamped = False

    def _clamp_initially_clamped_nodes(self):
        for node in self.initially_clamped_nodes:
            self.slipnet.clamp_node(node)

    def _unclamp_initially_clamped_nodes(self):
        for node in self.initially_clamped_nodes:
            self.slipnet.unclamp_node(node)

    def handle_snag(self):
        self.snag_count += 1
        self.last_snag_time = self.coderack.number_of_codelets_run
        self.snag_structures = self.workspace.structures
        self.workspace.delete_proposed_structures()
        self.coderack.empty()
        self.workspace.delete_translated_rule()
        self.workspace.answer_string.empty()
        self.snag_condition = True
        self.temperature = 1.0
        self.clamp_temperature = True
        for description in self.workspace.snag_object.descriptions:
            self.slipnet.clamp_node(description.descriptor.name)
        self.workspace.snag_object.salience_is_clamped = True
        self._post_initial_codelets()
        self.update()

    def delete_answer(self):
        pass
