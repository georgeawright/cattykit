from copycat.workspace_structure import WorkspaceStructure


class Replacement(WorkspaceStructure):
    def __init__(self, source: "WorkspaceObject", target: "WorkspaceObject"):
        self.source = source
        self.target = target
