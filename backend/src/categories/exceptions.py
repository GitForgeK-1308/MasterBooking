class CategoryNotFoundError(Exception):
    pass


class CategoryAlreadyExistsError(Exception):
    pass


class CategoryInactiveError(Exception):
    pass


class CategoryInvalidParentError(Exception):
    pass


class CategoryHasChildrenError(Exception):
    pass


class CategoryInUseError(Exception):
    pass
