import numpy as np
import pytest

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
from copycat.codelets.builders import (
    BondBuilder,
    CorrespondenceBuilder,
    GroupBuilder,
    RuleBuilder,
)
from copycat.codelets.strength_testers import (
    BondStrengthTester,
    CorrespondenceStrengthTester,
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

    copycat.slipnet.update_activations()

    # letter category spreads activation to letters and other structure types
    assert 1.0 == copycat.slipnet.get_node_activation("letter_category")
    assert np.isclose(0.03, copycat.slipnet.get_node_activation("a"))
    assert np.isclose(0.4, copycat.slipnet.get_node_activation("bond_facet"))
    # The replacement finder normally samples an initial letter.  In this
    # deterministic reconstruction of Mitchell's representative run, choose
    # the changed c instead.
    monkeypatch.setattr(
        "copycat.codelets.replacement_finder.random.choice",
        lambda _: copycat.workspace.initial_string.letters[2],
    )
    assert (
        ReplacementFinder(
            urgency_bin=2,
            coderack=copycat.coderack,
            workspace=copycat.workspace,
            slipnet=copycat.slipnet,
        ).run(temperature=1.0)
        == Finish()
    )
    changed_letter = copycat.workspace.initial_string.letters[2]
    assert changed_letter.is_changed_letter
    assert changed_letter.replacement.target.letter_category.name == "d"
    monkeypatch.undo()

    # The book's snapshots omit most unsuccessful exploratory codelets.  Run a
    # deterministic sample of those intervening actions before any structures
    # have been built.  Each codelet and all of its arguments remain visible;
    # only identical expected-fizzle actions are grouped.
    codelets_run = 1
    coderack_population = copycat.coderack.population
    monkeypatch.setattr(
        "copycat.codelets.replacement_finder.random.choice",
        lambda _: changed_letter,
    )
    for _ in range(25):
        codelet = ReplacementFinder(
            urgency_bin=2,
            coderack=copycat.coderack,
            workspace=copycat.workspace,
            slipnet=copycat.slipnet,
        )
        assert codelet.run(temperature=1.0) == Fizzle(
            FizzleReason.LETTER_ALREADY_HAS_REPLACEMENT
        )
        codelets_run += 1
        assert len(copycat.workspace.replacements) == 1
        assert copycat.coderack.population == coderack_population
    monkeypatch.undo()

    for _ in range(25):
        codelet = WholeStringGroupScout(
            urgency_bin=2,
            coderack=copycat.coderack,
            workspace=copycat.workspace,
            slipnet=copycat.slipnet,
        )
        assert codelet.run(temperature=1.0) == Fizzle(FizzleReason.NO_BONDS)
        codelets_run += 1
        assert copycat.workspace.groups == []
        assert copycat.coderack.population == coderack_population

    for _ in range(25):
        codelet = Breaker(
            urgency_bin=2,
            coderack=copycat.coderack,
            workspace=copycat.workspace,
            slipnet=copycat.slipnet,
        )
        assert codelet.run(temperature=1.0) == Fizzle(FizzleReason.NO_STRUCTURES)
        codelets_run += 1
        assert copycat.workspace.structures == []
        assert copycat.coderack.population == coderack_population

    # Run a fixed, manually scheduled sequence.  Selection is controlled, but
    # every structure below is proposed and built by a codelet.
    a, b = copycat.workspace.initial_string.letters[:2]
    codelet = BottomUpBondScout(2, copycat.coderack, copycat.workspace, copycat.slipnet)
    monkeypatch.setattr(copycat.workspace, "choose_object", lambda *_: a)
    monkeypatch.setattr(a, "choose_neighbor", lambda _: b, raising=False)
    monkeypatch.setattr(
        codelet, "_choose_bond_facet", lambda *_: copycat.slipnet["letter_category"]
    )
    monkeypatch.setattr(
        codelet, "_get_bond_category", lambda *_: copycat.slipnet["successor"]
    )
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.initial_string.proposed_bonds) == 1
    assert (
        copycat.slipnet.activation_buffers[copycat.slipnet.node_index_lookup["a"]] > 0
    )
    codelet = next(
        c for c in copycat.coderack.codelets if isinstance(c, BondStrengthTester)
    )
    monkeypatch.setattr(
        "copycat.codelets.strength_testers.bond_strength_tester.random.random",
        lambda: 0.0,
    )
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert any(isinstance(c, BondBuilder) for c in copycat.coderack.codelets)
    codelet = next(c for c in copycat.coderack.codelets if isinstance(c, BondBuilder))
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.initial_string.bonds) == 1
    assert a.right_bond is b.left_bond
    assert (
        copycat.slipnet.activation_buffers[
            copycat.slipnet.node_index_lookup["successor"]
        ]
        > 0
    )

    # b-c successor bond: scout, strength tester, builder.
    codelet = BottomUpBondScout(2, copycat.coderack, copycat.workspace, copycat.slipnet)
    monkeypatch.setattr(copycat.workspace, "choose_object", lambda *_: b)
    monkeypatch.setattr(b, "choose_neighbor", lambda _: changed_letter, raising=False)
    monkeypatch.setattr(
        codelet, "_choose_bond_facet", lambda *_: copycat.slipnet["letter_category"]
    )
    monkeypatch.setattr(
        codelet, "_get_bond_category", lambda *_: copycat.slipnet["successor"]
    )
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.initial_string.proposed_bonds) == 1
    codelet = [
        c for c in copycat.coderack.codelets if isinstance(c, BondStrengthTester)
    ][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert isinstance(copycat.coderack.codelets[-1], BondBuilder)
    codelet = copycat.coderack.codelets[-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.initial_string.bonds) == 2
    assert b.right_bond is changed_letter.left_bond

    # i-j successor bond: scout, strength tester, builder.
    i, j, k = copycat.workspace.target_string.letters
    codelet = BottomUpBondScout(2, copycat.coderack, copycat.workspace, copycat.slipnet)
    monkeypatch.setattr(copycat.workspace, "choose_object", lambda *_: i)
    monkeypatch.setattr(i, "choose_neighbor", lambda _: j, raising=False)
    monkeypatch.setattr(
        codelet, "_choose_bond_facet", lambda *_: copycat.slipnet["letter_category"]
    )
    monkeypatch.setattr(
        codelet, "_get_bond_category", lambda *_: copycat.slipnet["successor"]
    )
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.target_string.proposed_bonds) == 1
    codelet = [
        c for c in copycat.coderack.codelets if isinstance(c, BondStrengthTester)
    ][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert isinstance(copycat.coderack.codelets[-1], BondBuilder)
    codelet = copycat.coderack.codelets[-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.target_string.bonds) == 1
    assert i.right_bond is j.left_bond

    # j-k successor bond: scout, strength tester, builder.
    codelet = BottomUpBondScout(2, copycat.coderack, copycat.workspace, copycat.slipnet)
    monkeypatch.setattr(copycat.workspace, "choose_object", lambda *_: j)
    monkeypatch.setattr(j, "choose_neighbor", lambda _: k, raising=False)
    monkeypatch.setattr(
        codelet, "_choose_bond_facet", lambda *_: copycat.slipnet["letter_category"]
    )
    monkeypatch.setattr(
        codelet, "_get_bond_category", lambda *_: copycat.slipnet["successor"]
    )
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.target_string.proposed_bonds) == 1
    codelet = [
        c for c in copycat.coderack.codelets if isinstance(c, BondStrengthTester)
    ][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert isinstance(copycat.coderack.codelets[-1], BondBuilder)
    codelet = copycat.coderack.codelets[-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.target_string.bonds) == 2
    assert j.right_bond is k.left_bond

    # Build the initial-string successor group using three codelets.
    monkeypatch.setattr(
        copycat.workspace, "get_random_string", lambda: copycat.workspace.initial_string
    )
    codelet = WholeStringGroupScout(
        2, copycat.coderack, copycat.slipnet, copycat.workspace
    )
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.initial_string.proposed_groups) == 1
    codelet = [
        c for c in copycat.coderack.codelets if isinstance(c, GroupStrengthTester)
    ][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    codelet = [c for c in copycat.coderack.codelets if isinstance(c, GroupBuilder)][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    initial_group = copycat.workspace.initial_string.groups[0]
    assert initial_group.spans_whole_string()

    # Build the target-string successor group using three codelets.
    monkeypatch.setattr(
        copycat.workspace, "get_random_string", lambda: copycat.workspace.target_string
    )
    codelet = WholeStringGroupScout(
        2, copycat.coderack, copycat.slipnet, copycat.workspace
    )
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.target_string.proposed_groups) == 1
    codelet = [
        c for c in copycat.coderack.codelets if isinstance(c, GroupStrengthTester)
    ][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    codelet = [c for c in copycat.coderack.codelets if isinstance(c, GroupBuilder)][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    target_group = copycat.workspace.target_string.groups[0]
    assert target_group.spans_whole_string()

    # Propose, test, and build the group-to-group correspondence.
    monkeypatch.setattr(
        copycat.workspace.initial_string, "choose_object", lambda **_: initial_group
    )
    monkeypatch.setattr(
        copycat.workspace.target_string, "choose_object", lambda **_: target_group
    )
    codelet = BottomUpCorrespondenceScout(
        2, copycat.coderack, copycat.workspace, copycat.slipnet
    )
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert len(copycat.workspace.proposed_correspondences) == 1
    codelet = [
        c
        for c in copycat.coderack.codelets
        if isinstance(c, CorrespondenceStrengthTester)
    ][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    codelet = [
        c for c in copycat.coderack.codelets if isinstance(c, CorrespondenceBuilder)
    ][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert initial_group.correspondence is target_group.correspondence

    # Finish the unchanged replacements with two selected replacement finders.
    monkeypatch.setattr(
        "copycat.codelets.replacement_finder.random.choice", lambda _: a
    )
    codelet = ReplacementFinder(2, copycat.coderack, copycat.workspace, copycat.slipnet)
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert a.replacement.target.letter_category.name == "a"
    monkeypatch.setattr(
        "copycat.codelets.replacement_finder.random.choice", lambda _: b
    )
    codelet = ReplacementFinder(2, copycat.coderack, copycat.workspace, copycat.slipnet)
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert b.replacement.target.letter_category.name == "b"
    monkeypatch.undo()

    # Rule scout, strength tester, and builder.
    codelet = RuleScout(2, copycat.coderack, copycat.workspace, copycat.slipnet)
    monkeypatch.setattr(
        codelet,
        "_get_initial_description",
        lambda *_: next(
            d
            for d in changed_letter.descriptions
            if d.descriptor is copycat.slipnet["rightmost"]
        ),
    )
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert any(isinstance(c, RuleStrengthTester) for c in copycat.coderack.codelets)
    codelet = [
        c for c in copycat.coderack.codelets if isinstance(c, RuleStrengthTester)
    ][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    codelet = [c for c in copycat.coderack.codelets if isinstance(c, RuleBuilder)][-1]
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert copycat.workspace.rule.relation is copycat.slipnet["successor"]

    # Translate the rule and let the answer builder apply it.
    codelet = RuleTranslator(2, copycat.coderack, copycat.workspace, copycat.slipnet)
    assert codelet.run(temperature=0.0) == Finish()
    codelets_run += 1
    assert copycat.workspace.translated_rule.relation is copycat.slipnet["successor"]
    assert AnswerBuilder(copycat.slipnet, copycat.workspace).build() is None
    assert [
        letter.letter_category.name
        for letter in copycat.workspace.answer_string.letters
    ] == ["i", "j", "l"]
    assert codelets_run >= 100
