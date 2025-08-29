from copycat import Structure


class Description(Structure):
    def __init__(self, argument_object, string, facet, descriptor, description_number):
        self.argument_object = argument_object
        self.string = string
        self.facet = facet
        self.descriptor = descriptor
        self.description_number = description_number

    def __eq__(self, other):
        return (self.facet, self.descriptor) == (other.facet, other.descriptor)
