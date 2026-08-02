import itertools

from copycat.workspace_structure import WorkspaceStructure


class Replacement(WorkspaceStructure):
    _next_id = itertools.count(1)

    def __init__(self, source: "WorkspaceObject", target: "WorkspaceObject"):
        self.source = source
        self.target = target
        self.hash_id = next(Replacement._next_id)
