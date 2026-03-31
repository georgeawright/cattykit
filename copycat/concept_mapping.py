from .slipnode import Slipnode
from .workspace_object import WorkspaceObject


class ConceptMapping:
    def __init__(
        self,
        description_type_1: Slipnode,
        description_type_2: Slipnode,
        descriptor_1: Slipnode,
        descriptor_2: Slipnode,
        label: Slipnode,
        object_1: WorkspaceObject,
        object_2: WorkspaceObject,
    ):
        self.description_type_1 = description_type_1
        self.description_type_2 = description_type_2
        self.descriptor_1 = descriptor_1
        self.descriptor_2 = descriptor_2
        self.label = label
        self.object_1 = object_1
        self.object_2 = object_2
