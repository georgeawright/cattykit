import json
import random
from typing import Optional

from cattykit.logging import ModelEvent, ModelLogger, NullLogger

from .answer_builder import AnswerBuilder
from .codelets import (
    BottomUpBondScout,
    BottomUpCorrespondenceScout,
    ReplacementFinder,
)
from .coderack import Coderack
from .slipnet import Slipnet
from .snag_exception import SnagException
from .workspace import Workspace
from .workspace_objects_and_structures import (
    Bond,
    Correspondence,
    Group,
    Letter,
    Rule,
    WorkspaceStructure,
)

DESCRIPTION_TESTERS = {
    # LENGTH
    "length_is_one": lambda x: isinstance(x, Group) and len(x) == 1,
    "length_is_two": lambda x: isinstance(x, Group) and len(x) == 2,
    "length_is_three": lambda x: isinstance(x, Group) and len(x) == 3,
    "length_is_four": lambda x: isinstance(x, Group) and len(x) == 4,
    "length_is_five": lambda x: isinstance(x, Group) and len(x) == 5,
    # STRING POSITION
    "is_leftmost": lambda x: not x.spans_whole_string and x.is_leftmost_in_string,
    "is_rightmost": lambda x: not x.spans_whole_string and x.is_rightmost_in_string,
    "is_middle": lambda x: x.is_middle_in_string,
    "is_single": lambda x: isinstance(x, Letter) and x.spans_whole_string,
    "is_whole": lambda x: isinstance(x, Group) and x.spans_whole_string,
    # ALPHABETIC POSITION
    "is_first": lambda x: (lambda d: d.name == "a" if d is not None else False)(
        x.get_descriptor_with_facet_name("letter_category")
    ),
    "is_last": lambda x: (lambda d: d.name == "z" if d is not None else False)(
        x.get_descriptor_with_facet_name("letter_category")
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
        logger: ModelLogger,
        seed: int | None = None,
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
        self.logger = logger
        self.seed = seed

    def close(self) -> None:
        """Copycat owns no resources"""

    @classmethod
    def from_json(
        cls,
        slipnet_json_file: str,
        coderack_json_file: str,
        hyperparameters_file: str,
        logger: ModelLogger | None = None,
        seed: int | None = None,
    ):
        logger = logger if logger is not None else NullLogger()
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
            logger=logger,
        )
        with open(coderack_json_file) as f:
            coderack_json = json.load(f)
        coderack = Coderack.from_json(coderack_json, logger)
        workspace = Workspace.setup(logger)
        return cls(
            slipnet,
            coderack=coderack,
            workspace=workspace,
            time_step_length=hyperparameters["time_step_length"],
            initially_clamped_nodes=hyperparameters["initially_clamped_nodes"],
            initial_slipnode_clamp_time=hyperparameters["initial_slipnode_clamp_time"],
            logger=logger,
            seed=seed,
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
                seed=self.seed,
                time=self.coderack.number_of_codelets_run,
            )
        )
        try:
            self.initialize(string)
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

    def initialize(self, string: str):
        """Initialize Copycat's components for one analogy problem."""
        self.workspace.initialize(string, self.slipnet)
        self._post_initial_codelets()
        self.slipnet.initialize()

    def run(self):
        """
        Unlike the original Copycat, this implementation has a limit of 99k codelets.
        This prevents infinite loops during development.
        Mitchell 1993 reports slowest performance on problem abc->abd==>xyz:
        mean codelets = 3,208; standard error of 88.3 over 1,000 runs (= stdev 2,792)
        According to Cantelli's inequality, this means that
        (without assumptions regarding distribution)
        fewer than 0.1% of runs on that problem should have lengths above 91,454 codelets
        """

        while True:
            if self.coderack.number_of_codelets_run > 99_000:
                break
            if self.coderack.number_of_codelets_run % self.time_step_length == 0:
                self.update()
            if self.coderack.is_empty:
                self._clamp_initially_clamped_nodes()
                self._post_initial_codelets()
            self.coderack.run_next_codelet(self.temperature)
            if self.workspace.translated_rule is None:
                continue
            try:
                answer_builder = AnswerBuilder(self.slipnet, self.workspace)
                previous_answer_letters = list(self.workspace.answer_string.letters)
                answer_builder.build()
                self._log_answer_letters(previous_answer_letters)
                self.found_answer = True
                self.update()
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

    def _update_temperature(self):
        if not self.clamp_temperature:
            rule_weakness = (
                1 - self.workspace.rule.total_strength if self.workspace.rule else 1
            )
            self.temperature = (
                self.workspace.total_unhappiness * 0.8 + rule_weakness * 0.2
            )
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
        new_structures = [
            structure
            for structure in self.workspace.structures
            if not isinstance(structure, Bond)
            and not self._structure_in_snag_structures(structure)
        ]
        unclamp_probability = max((s.total_strength for s in new_structures), default=0)
        if unclamp_probability > random.random():
            self.snag_condition = False
            self.clamp_temperature = False
            for description in self.workspace.snag_object.descriptions:
                self.slipnet.unclamp_node(description.descriptor.name)
            self.workspace.snag_object.salience_is_clamped = False
            self.logger.log(
                ModelEvent.create(
                    "copycat",
                    "snag_ended",
                    time=self.coderack.number_of_codelets_run,
                )
            )

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

    def _structure_in_snag_structures(self, structure: WorkspaceStructure) -> bool:
        for old in self.snag_structures:
            if isinstance(structure, Group) and isinstance(old, Group):
                if (
                    old.left_object is structure.left_object
                    and old.right_object is structure.right_object
                    and old.group_category is structure.group_category
                    and old.direction_category is structure.direction_category
                ):
                    return True
            elif isinstance(structure, Correspondence) and isinstance(
                old, Correspondence
            ):
                if (
                    old.source is structure.source
                    and old.target is structure.target
                    and len(old.relevant_distinguishing_mappings)
                    >= len(structure.relevant_distinguishing_mappings)
                ):
                    return True
            elif isinstance(structure, Rule) and isinstance(old, Rule):
                if old.equates_to(structure):
                    return True
        return False
