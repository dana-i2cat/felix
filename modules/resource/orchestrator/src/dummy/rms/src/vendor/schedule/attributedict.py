class AttributeDict(dict):
    """
    Behaves like a dict, but you can also access the keys of the dict as properties:
    ad = AttributeDict({"x" : 1, "y" : 2})
    ad["x"]  # -> 1
    ad.x     # -> 1
    ad.y     # -> 2
    ad.x = 3
    ad.x     # -> 3
    """
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value