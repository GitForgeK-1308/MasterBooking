class CategoryNotFoundError(Exception):
    pass


class CategoryAlreadyExistsError(Exception):
    pass


class CategoryInactiveError(Exception):
    pass


class CategoryInvalidParentError(Exception):
    pass