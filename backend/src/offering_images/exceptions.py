class OfferingImageNotFoundError(Exception):
    pass


class OfferingImageLimitExceededError(Exception):
    pass


class InvalidOfferingImageTypeError(Exception):
    pass


class OfferingImageTooLargeError(Exception):
    pass


class OfferingImageAccessDeniedError(Exception):
    pass