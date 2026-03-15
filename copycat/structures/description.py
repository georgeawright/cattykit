from copycat.slipnode import Slipnode
from copycat.structure import Structure


class Description(Structure):
    def __init__(
        self, argument_object: Structure, facet: Slipnode, descriptor: Slipnode
    ):
        self.argument_object = argument_object
        self.facet = facet
        self.descriptor = descriptor

    def __eq__(self, other):
        return (self.facet, self.descriptor) == (other.facet, other.descriptor)
