from typing import Optional

import numpy as np

from copycat.codelets.scouts.description_scout import DescriptionScout
from copycat.workspace_object import WorkspaceObject


class BottomUpDescriptionScout(DescriptionScout):
    """Chooses an object probabilistically by total salience.
    Chooses a relevant description probabilistically by activation.
    Checks if the descriptor has any "has property" links that are short enough.
    Chooses one of the properties probabilistically by degree of association and activation.
    Proposes a description based on the property and posts a description strength tester
    with urgency a function of the property's activation."""

    def run(self, temperature: float):
        chosen_object = self.workspace.choose_object(
            temperature, lambda x: x.total_salience
        )
        if chosen_object is None:
            return
        chosen_description = chosen_object.choose_relevant_description_by_activation()
        if chosen_description is None:
            return
        chosen_descriptor = chosen_description.descriptor
        has_property_links = chosen_descriptor.get_similar_has_property_links(
            temperature
        )
        if not has_property_links:
            return
        choice_list = np.array(
            [
                link.degree_of_association
                * self.slipnet.get_node_activation(link.to_node.name)
                for link in has_property_links
            ]
        )
        chosen_link = np.random.choice(
            has_property_links, p=choice_list / choice_list.sum()
        )
        chosen_property = chosen_link.to_node
        self.propose_description(
            chosen_object, chosen_property.category, chosen_property
        )
