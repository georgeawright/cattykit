import numpy as np
import pytest
from random import choice as random_choice
from random import choices as random_choices

from copycat import Copycat
from copycat.answer_builder import AnswerBuilder
from copycat.codelet_result import Finish, Fizzle, FizzleReason
from copycat.codelets import (
    BottomUpBondScout,
    BottomUpCorrespondenceScout,
    Breaker,
    ReplacementFinder,
    RuleScout,
    RuleTranslator,
    WholeStringGroupScout,
)
from copycat.codelets.scouts.description_scouts import TopDownDescriptionScout
from copycat.codelets.builders import (
    BondBuilder,
    CorrespondenceBuilder,
    DescriptionBuilder,
    GroupBuilder,
    RuleBuilder,
)
from copycat.codelets.strength_testers import (
    BondStrengthTester,
    CorrespondenceStrengthTester,
    DescriptionStrengthTester,
    GroupStrengthTester,
    RuleStrengthTester,
)

SLIPNET_JSON_FILE = "configs/slipnet.json"
CODERACK_JSON_FILE = "configs/coderack.json"
HYPERPARAMETERS_FILE = "configs/hyperparameters.json"


def test_single_run(monkeypatch):
    # initial set up
    copycat = Copycat.from_json(
        SLIPNET_JSON_FILE, CODERACK_JSON_FILE, HYPERPARAMETERS_FILE
    )

    # coderack starts empty
    assert copycat.coderack.population == 0

    # all node activations are zero except for initially clamped nodes
    active_node_count = 0
    for node_id, node in copycat.slipnet.node_index_lookup.items():
        if node_id in ["letter_category", "string_position_category"]:
            assert copycat.slipnet.get_node_activation(node_id) == 1.0
            active_node_count += 1
        else:
            assert copycat.slipnet.get_node_activation(node_id) == 0.0
    assert active_node_count == 2

    # add problem to workspace
    copycat._add_letters_to_workspace("abc -> abd ==> ijk -> ?")
    copycat._add_initial_descriptions_to_workspace()

    # each string should have letter category and position descriptions
    assert {
        l.letter_category.name: [
            (d.facet.name, d.descriptor.name) for d in l.descriptions
        ]
        for l in copycat.workspace.initial_string.letters
    } == {
        "a": [
            ("object_category", "letter"),
            ("letter_category", "a"),
            ("string_position_category", "leftmost"),
        ],
        "b": [
            ("object_category", "letter"),
            ("letter_category", "b"),
            ("string_position_category", "middle"),
        ],
        "c": [
            ("object_category", "letter"),
            ("letter_category", "c"),
            ("string_position_category", "rightmost"),
        ],
    }
    assert {
        l.letter_category.name: [
            (d.facet.name, d.descriptor.name) for d in l.descriptions
        ]
        for l in copycat.workspace.modified_string.letters
    } == {
        "a": [
            ("object_category", "letter"),
            ("letter_category", "a"),
            ("string_position_category", "leftmost"),
        ],
        "b": [
            ("object_category", "letter"),
            ("letter_category", "b"),
            ("string_position_category", "middle"),
        ],
        "d": [
            ("object_category", "letter"),
            ("letter_category", "d"),
            ("string_position_category", "rightmost"),
        ],
    }
    assert {
        l.letter_category.name: [
            (d.facet.name, d.descriptor.name) for d in l.descriptions
        ]
        for l in copycat.workspace.target_string.letters
    } == {
        "i": [
            ("object_category", "letter"),
            ("letter_category", "i"),
            ("string_position_category", "leftmost"),
        ],
        "j": [
            ("object_category", "letter"),
            ("letter_category", "j"),
            ("string_position_category", "middle"),
        ],
        "k": [
            ("object_category", "letter"),
            ("letter_category", "k"),
            ("string_position_category", "rightmost"),
        ],
    }
    # the answer string is empty at the start
    assert [
        l.letter_category.name for l in copycat.workspace.answer_string.letters
    ] == []

    copycat._post_initial_codelets()

    # 3 types of codelets have been added.
    # 2 for each workspace object (initial and target string objects)
    assert copycat.coderack.population == 36

    selected_codelet = [None]
    chosen_object = [None]
    monkeypatch.setattr(
        "copycat.coderack.random.choice",
        lambda population: (
            selected_codelet[0]
            if selected_codelet[0] in population
            else chosen_object[0]
            if chosen_object[0] in population
            else random_choice(population)
        ),
    )
    monkeypatch.setattr(
        "copycat.coderack.random.choices",
        lambda population, weights=None, k=1: (
            [copycat.coderack.get_urgency_bin(selected_codelet[0].urgency_bin)]
            if population is copycat.coderack._urgency_bins
            else random_choices(population, weights=weights, k=k)
        ),
    )

    copycat.slipnet.update_activations()

    # letter category spreads activation to letters and other structure types
    assert 1.0 == copycat.slipnet.get_node_activation("letter_category")
    assert np.isclose(0.03, copycat.slipnet.get_node_activation("a"))
    assert np.isclose(0.4, copycat.slipnet.get_node_activation("bond_facet"))
    # The replacement finder normally samples an initial letter.  In this
    # deterministic reconstruction of Mitchell's representative run, choose
    # the changed c instead.
    chosen_object[0] = copycat.workspace.initial_string.letters[2]
    selected_codelet[0] = next(
        c for c in copycat.coderack.codelets if isinstance(c, ReplacementFinder)
    )
    assert selected_codelet[0].birth_time == 0
    codelet = copycat.coderack.choose(temperature=1.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=1.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 1
    changed_letter = copycat.workspace.initial_string.letters[2]
    assert changed_letter.is_changed_letter
    assert changed_letter.replacement.target.letter_category.name == "d"

    # The book's snapshots omit most unsuccessful exploratory codelets.  Run a
    # deterministic sample of those intervening actions before any structures
    # have been built.  Each codelet and all of its arguments remain visible;
    # only identical expected-fizzle actions are grouped.
    coderack_population = copycat.coderack.population
    chosen_object[0] = changed_letter
    for codelet_index in range(25):
        selected_codelet[0] = ReplacementFinder(
            urgency_bin=2,
            coderack=copycat.coderack,
            workspace=copycat.workspace,
            slipnet=copycat.slipnet,
        )
        copycat.coderack.post(selected_codelet[0], temperature=1.0)
        assert selected_codelet[0].birth_time == codelet_index + 1
        codelet = copycat.coderack.choose(temperature=1.0)
        assert codelet is selected_codelet[0]
        assert codelet.run(temperature=1.0) == Fizzle(
            FizzleReason.LETTER_ALREADY_HAS_REPLACEMENT
        )
        assert copycat.coderack.number_of_codelets_run == codelet_index + 2
        assert len(copycat.workspace.replacements) == 1
        assert copycat.coderack.population == coderack_population

    chosen_object[0] = None
    for codelet_index in range(25):
        selected_codelet[0] = WholeStringGroupScout(
            urgency_bin=2,
            coderack=copycat.coderack,
            workspace=copycat.workspace,
            slipnet=copycat.slipnet,
        )
        copycat.coderack.post(selected_codelet[0], temperature=1.0)
        assert selected_codelet[0].birth_time == codelet_index + 26
        codelet = copycat.coderack.choose(temperature=1.0)
        assert codelet is selected_codelet[0]
        assert codelet.run(temperature=1.0) == Fizzle(FizzleReason.NO_BONDS)
        assert copycat.coderack.number_of_codelets_run == codelet_index + 27
        assert copycat.workspace.groups == []
        assert copycat.coderack.population == coderack_population

    for codelet_index in range(25):
        selected_codelet[0] = Breaker(
            urgency_bin=2,
            coderack=copycat.coderack,
            workspace=copycat.workspace,
            slipnet=copycat.slipnet,
        )
        copycat.coderack.post(selected_codelet[0], temperature=1.0)
        assert selected_codelet[0].birth_time == codelet_index + 51
        codelet = copycat.coderack.choose(temperature=1.0)
        assert codelet is selected_codelet[0]
        assert codelet.run(temperature=1.0) == Fizzle(FizzleReason.NO_STRUCTURES)
        assert copycat.coderack.number_of_codelets_run == codelet_index + 52
        assert copycat.workspace.structures == []
        assert copycat.coderack.population == coderack_population

    # Run a fixed, manually scheduled sequence.  Selection is controlled, but
    # every structure below is proposed and built by a codelet.
    a, b = copycat.workspace.initial_string.letters[:2]
    selected_codelet[0] = BottomUpBondScout(
        2, copycat.coderack, copycat.workspace, copycat.slipnet
    )
    monkeypatch.setattr(copycat.workspace, "choose_object", lambda *_: a)
    monkeypatch.setattr(a, "choose_neighbor", lambda _: b, raising=False)
    monkeypatch.setattr(
        selected_codelet[0],
        "_choose_bond_facet",
        lambda *_: copycat.slipnet["letter_category"],
    )
    monkeypatch.setattr(
        selected_codelet[0],
        "_get_bond_category",
        lambda *_: copycat.slipnet["successor"],
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 76
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 77
    assert len(copycat.workspace.initial_string.proposed_bonds) == 1
    assert (
        copycat.slipnet.activation_buffers[copycat.slipnet.node_index_lookup["a"]] > 0
    )
    selected_codelet[0] = next(
        c
        for c in copycat.coderack.codelets
        if isinstance(c, BondStrengthTester) and c.birth_time == 77
    )
    monkeypatch.setattr(
        "copycat.codelets.strength_testers.bond_strength_tester.random.random",
        lambda: 0.0,
    )
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 78
    assert any(isinstance(c, BondBuilder) for c in copycat.coderack.codelets)
    selected_codelet[0] = next(
        c
        for c in copycat.coderack.codelets
        if isinstance(c, BondBuilder) and c.birth_time == 78
    )
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 79
    assert len(copycat.workspace.initial_string.bonds) == 1
    assert a.right_bond is b.left_bond
    assert (
        copycat.slipnet.activation_buffers[
            copycat.slipnet.node_index_lookup["successor"]
        ]
        > 0
    )

    # b-c successor bond: scout, strength tester, builder.
    selected_codelet[0] = BottomUpBondScout(
        2, copycat.coderack, copycat.workspace, copycat.slipnet
    )
    monkeypatch.setattr(copycat.workspace, "choose_object", lambda *_: b)
    monkeypatch.setattr(b, "choose_neighbor", lambda _: changed_letter, raising=False)
    monkeypatch.setattr(
        selected_codelet[0],
        "_choose_bond_facet",
        lambda *_: copycat.slipnet["letter_category"],
    )
    monkeypatch.setattr(
        selected_codelet[0],
        "_get_bond_category",
        lambda *_: copycat.slipnet["successor"],
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 79
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 80
    assert len(copycat.workspace.initial_string.proposed_bonds) == 1
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, BondStrengthTester) and c.birth_time == 80
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 81
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, BondBuilder) and c.birth_time == 81
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 82
    assert len(copycat.workspace.initial_string.bonds) == 2
    assert b.right_bond is changed_letter.left_bond

    # i-j successor bond: scout, strength tester, builder.
    i, j, k = copycat.workspace.target_string.letters
    selected_codelet[0] = BottomUpBondScout(
        2, copycat.coderack, copycat.workspace, copycat.slipnet
    )
    monkeypatch.setattr(copycat.workspace, "choose_object", lambda *_: i)
    monkeypatch.setattr(i, "choose_neighbor", lambda _: j, raising=False)
    monkeypatch.setattr(
        selected_codelet[0],
        "_choose_bond_facet",
        lambda *_: copycat.slipnet["letter_category"],
    )
    monkeypatch.setattr(
        selected_codelet[0],
        "_get_bond_category",
        lambda *_: copycat.slipnet["successor"],
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 82
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 83
    assert len(copycat.workspace.target_string.proposed_bonds) == 1
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, BondStrengthTester) and c.birth_time == 83
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 84
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, BondBuilder) and c.birth_time == 84
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 85
    assert len(copycat.workspace.target_string.bonds) == 1
    assert i.right_bond is j.left_bond

    # j-k successor bond: scout, strength tester, builder.
    selected_codelet[0] = BottomUpBondScout(
        2, copycat.coderack, copycat.workspace, copycat.slipnet
    )
    monkeypatch.setattr(copycat.workspace, "choose_object", lambda *_: j)
    monkeypatch.setattr(j, "choose_neighbor", lambda _: k, raising=False)
    monkeypatch.setattr(
        selected_codelet[0],
        "_choose_bond_facet",
        lambda *_: copycat.slipnet["letter_category"],
    )
    monkeypatch.setattr(
        selected_codelet[0],
        "_get_bond_category",
        lambda *_: copycat.slipnet["successor"],
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 85
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 86
    assert len(copycat.workspace.target_string.proposed_bonds) == 1
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, BondStrengthTester) and c.birth_time == 86
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 87
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, BondBuilder) and c.birth_time == 87
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 88
    assert len(copycat.workspace.target_string.bonds) == 2
    assert j.right_bond is k.left_bond

    # Build the initial-string successor group using three codelets.
    monkeypatch.setattr(
        copycat.workspace, "get_random_string", lambda: copycat.workspace.initial_string
    )
    selected_codelet[0] = WholeStringGroupScout(
        2, copycat.coderack, copycat.slipnet, copycat.workspace
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 88
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 89
    assert len(copycat.workspace.initial_string.proposed_groups) == 1
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, GroupStrengthTester) and c.birth_time == 89
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 90
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, GroupBuilder) and c.birth_time == 90
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 91
    initial_group = copycat.workspace.initial_string.groups[0]
    assert initial_group.spans_whole_string()

    # Give the initial group its successor-group description before attempting
    # any group correspondence.
    monkeypatch.setattr(copycat.workspace, "choose_object", lambda *_: initial_group)
    monkeypatch.setattr(
        copycat.slipnet["group_category"],
        "get_possible_descriptors",
        lambda _: [copycat.slipnet["successor_group"]],
    )
    monkeypatch.setattr(
        "copycat.codelets.scouts.description_scouts.top_down_description_scout.np.random.choice",
        lambda *_args, **_kwargs: copycat.slipnet["successor_group"],
    )
    selected_codelet[0] = TopDownDescriptionScout(
        urgency_bin=2,
        coderack=copycat.coderack,
        slipnet=copycat.slipnet,
        workspace=copycat.workspace,
        description_type=copycat.slipnet["group_category"],
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 91
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 92
    selected_codelet[0] = next(
        c
        for c in copycat.coderack.codelets
        if isinstance(c, DescriptionStrengthTester) and c.birth_time == 92
    )
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 93
    selected_codelet[0] = next(
        c
        for c in copycat.coderack.codelets
        if isinstance(c, DescriptionBuilder) and c.birth_time == 93
    )
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 94
    assert (
        initial_group.get_descriptor(copycat.slipnet["group_category"])
        is copycat.slipnet["successor_group"]
    )

    # Build the target-string successor group using three codelets.
    monkeypatch.setattr(
        copycat.workspace, "get_random_string", lambda: copycat.workspace.target_string
    )
    selected_codelet[0] = WholeStringGroupScout(
        2, copycat.coderack, copycat.slipnet, copycat.workspace
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 94
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 95
    assert len(copycat.workspace.target_string.proposed_groups) == 1
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, GroupStrengthTester) and c.birth_time == 95
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 96
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, GroupBuilder) and c.birth_time == 96
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 97
    target_group = copycat.workspace.target_string.groups[0]
    assert target_group.spans_whole_string()

    # Give the target group the matching successor-group description.
    monkeypatch.setattr(copycat.workspace, "choose_object", lambda *_: target_group)
    selected_codelet[0] = TopDownDescriptionScout(
        urgency_bin=2,
        coderack=copycat.coderack,
        slipnet=copycat.slipnet,
        workspace=copycat.workspace,
        description_type=copycat.slipnet["group_category"],
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 97
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 98
    selected_codelet[0] = next(
        c
        for c in copycat.coderack.codelets
        if isinstance(c, DescriptionStrengthTester) and c.birth_time == 98
    )
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 99
    selected_codelet[0] = next(
        c
        for c in copycat.coderack.codelets
        if isinstance(c, DescriptionBuilder) and c.birth_time == 99
    )
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 100
    assert (
        target_group.get_descriptor(copycat.slipnet["group_category"])
        is copycat.slipnet["successor_group"]
    )

    # Propose, test, and build the group-to-group correspondence.
    monkeypatch.setattr(
        copycat.workspace.initial_string, "choose_object", lambda **_: initial_group
    )
    monkeypatch.setattr(
        copycat.workspace.target_string, "choose_object", lambda **_: target_group
    )
    selected_codelet[0] = BottomUpCorrespondenceScout(
        2, copycat.coderack, copycat.workspace, copycat.slipnet
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 100
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 101
    assert len(copycat.workspace.proposed_correspondences) == 1
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, CorrespondenceStrengthTester) and c.birth_time == 101
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 102
    copycat.slipnet.update_activations()
    selected_codelet[0] = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, CorrespondenceBuilder) and c.birth_time == 102
    ][-1]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 103
    assert initial_group.correspondence is target_group.correspondence

    # Finish the unchanged replacements with two selected replacement finders.
    chosen_object[0] = a
    selected_codelet[0] = ReplacementFinder(
        2, copycat.coderack, copycat.workspace, copycat.slipnet
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 103
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 104
    assert a.replacement.target.letter_category.name == "a"
    chosen_object[0] = b
    selected_codelet[0] = ReplacementFinder(
        2, copycat.coderack, copycat.workspace, copycat.slipnet
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 104
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 105
    assert b.replacement.target.letter_category.name == "b"
    chosen_object[0] = None

    # Rule scout, strength tester, and builder.
    selected_codelet[0] = RuleScout(
        2, copycat.coderack, copycat.workspace, copycat.slipnet
    )
    monkeypatch.setattr(
        selected_codelet[0],
        "_get_initial_description",
        lambda *_: next(
            d
            for d in changed_letter.descriptions
            if d.descriptor is copycat.slipnet["rightmost"]
        ),
    )
    monkeypatch.setattr(
        selected_codelet[0],
        "_get_modified_description",
        lambda modified_object, *_: next(
            d
            for d in modified_object.extrinsic_descriptions
            if d.description_type_related is copycat.slipnet["letter_category"]
            and d.relation is copycat.slipnet["successor"]
        ),
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 105
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 106
    assert any(isinstance(c, RuleStrengthTester) for c in copycat.coderack.codelets)
    selected_codelet[0] = next(
        c
        for c in copycat.coderack.codelets
        if isinstance(c, RuleStrengthTester) and c.birth_time == 106
    )
    assert (
        selected_codelet[0].proposed_rule.descriptor_1_facet
        is copycat.slipnet["string_position_category"]
    )
    assert (
        selected_codelet[0].proposed_rule.descriptor_1
        is copycat.slipnet["rightmost"]
    )
    assert (
        selected_codelet[0].proposed_rule.replaced_description_type
        is copycat.slipnet["letter_category"]
    )
    assert selected_codelet[0].proposed_rule.relation is copycat.slipnet["successor"]
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 107
    selected_codelet[0] = next(
        c
        for c in copycat.coderack.codelets
        if isinstance(c, RuleBuilder) and c.birth_time == 107
    )
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 108
    # RIGHTMOST locates the letter to change; LETTER_CATEGORY is what changes.
    assert (
        copycat.workspace.rule.descriptor_1_facet
        is copycat.slipnet["string_position_category"]
    )
    assert copycat.workspace.rule.descriptor_1 is copycat.slipnet["rightmost"]
    assert (
        copycat.workspace.rule.replaced_description_type
        is copycat.slipnet["letter_category"]
    )
    assert copycat.workspace.rule.relation is copycat.slipnet["successor"]
    assert (
        repr(copycat.workspace.rule)
        == "Replace LETTER_CATEGORY of RIGHTMOST LETTER by SUCCESSOR"
    )

    # Translate the rule and let the answer builder apply it.
    selected_codelet[0] = RuleTranslator(
        2, copycat.coderack, copycat.workspace, copycat.slipnet
    )
    copycat.coderack.post(selected_codelet[0], temperature=0.0)
    assert selected_codelet[0].birth_time == 108
    codelet = copycat.coderack.choose(temperature=0.0)
    assert codelet is selected_codelet[0]
    assert codelet.run(temperature=0.0) == Finish()
    assert copycat.coderack.number_of_codelets_run == 109
    assert copycat.workspace.translated_rule.relation is copycat.slipnet["successor"]
    assert AnswerBuilder(copycat.slipnet, copycat.workspace).build() is None
    assert [
        letter.letter_category.name
        for letter in copycat.workspace.answer_string.letters
    ] == ["i", "j", "l"]
    assert copycat.coderack.number_of_codelets_run == 109
