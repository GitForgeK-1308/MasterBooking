class TagNotFoundError(Exception):
    pass


class TagAlreadyExistsError(Exception):
    pass


class TagInactiveError(Exception):
    pass


class TagInUseError(Exception):
    pass
