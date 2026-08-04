from types import SimpleNamespace

import pytest

from copycat import Slipnode


def test_category():
    node = Slipnode("node", 1)
    assert node.category is None
    category_node = Slipnode("category", 1)
    node.category_links.append(SimpleNamespace(target=category_node))
    assert node.category == category_node


@pytest.mark.parametrize(
    ["activation", "is_active"],
    [
        (1.1, True),
        (1.0, True),
        (0.9999, False),
        (0.9, False),
        (0.5, False),
        (0.0, False),
    ],
)
def test_is_active(activation, is_active):
    slipnode = Slipnode("name", 1, 1, 1, lambda x: None)
    slipnode.activation = activation
    assert is_active == slipnode.is_active()


def test_is_related_to_and_is_linked_to():
    node_a = Slipnode("a", 1)
    node_b = Slipnode("b", 1)
    node_c = Slipnode("c", 1)
    node_a.lateral_sliplinks.append(SimpleNamespace(source=node_a, target=node_b))

    assert not node_a.is_linked_to(node_a)  # no self-links
    assert node_a.is_linked_to(node_b)  # linked relationship
    assert not node_a.is_linked_to(node_c)  # no relationship

    assert node_a.is_related_to(node_a)  # identity relationship
    assert node_a.is_related_to(node_b)  # linked relationship
    assert not node_a.is_related_to(node_c)  # no relationship


def test_get_similar_has_property_links():
    node = Slipnode("node", 1)
    link1 = SimpleNamespace(
        label=SimpleNamespace(name="has_property"),
        target=SimpleNamespace(name="property1"),
        degree_of_association=1.0,
    )
    link2 = SimpleNamespace(
        label=SimpleNamespace(name="has_property"),
        target=SimpleNamespace(name="property2"),
        degree_of_association=0.0,
    )
    node.has_property_links.extend([link1, link2])

    similar_links = node.get_similar_has_property_links(temperature=0.5)
    assert link1 in similar_links
    assert link2 not in similar_links


def test_get_possible_descriptors():
    ginger_cat = SimpleNamespace(name="ginger_cat")
    striped_cat = SimpleNamespace(name="striped_cat")

    cat_node = Slipnode("cat", 1)
    ginger_descriptor = Slipnode(
        "ginger", 1, description_tester=lambda x: x.name == "ginger_cat"
    )
    striped_descriptor = Slipnode(
        "striped", 1, description_tester=lambda x: x.name == "striped_cat"
    )
    cat_ginger = SimpleNamespace(source=cat_node, target=ginger_descriptor)
    cat_striped = SimpleNamespace(source=cat_node, target=striped_descriptor)
    cat_node.instance_links.extend([cat_ginger, cat_striped])

    assert cat_node.get_possible_descriptors(ginger_cat) == [ginger_descriptor]
    assert cat_node.get_possible_descriptors(striped_cat) == [striped_descriptor]


@pytest.mark.parametrize(
    ["supporting_objects", "non_supporting_objects", "activation", "expected"],
    [
        (0, 0, 0.0, 0.0),  # no objects, no support
        (0, 0, 1.0, 0.5),  # no objects, no support
        (1, 0, 0.0, 0.5),  # one object supports, full support
        (1, 0, 1.0, 1.0),  # one object supports, full support
        (0, 1, 0.0, 0.0),  # one object doesn't support, no support
        (0, 1, 1.0, 0.5),  # one object doesn't support, no support
        (2, 0, 0.0, 0.5),  # all objects support, full support
        (2, 0, 1.0, 1.0),  # all objects support, full support
        (1, 1, 0.0, 0.25),  # half of the objects support, half support
        (1, 1, 1.0, 0.75),  # half of the objects support, half support
        (0, 2, 0.0, 0.0),  # no objects support, no support
        (0, 2, 1.0, 0.5),  # no objects support, no support
    ],
)
def test_support(supporting_objects, non_supporting_objects, activation, expected):
    node = Slipnode("node", 1)
    node.activation = activation
    workspace_string = SimpleNamespace(name="workspace_string", objects=[])
    for _ in range(supporting_objects):
        obj = SimpleNamespace(name="object")
        obj.has_description_type = lambda x: True
        workspace_string.objects.append(obj)
    for _ in range(non_supporting_objects):
        obj = SimpleNamespace(name="object")
        obj.has_description_type = lambda x: False
        workspace_string.objects.append(obj)
    assert node.total_description_type_support(workspace_string) == expected
