class ReviewBookingNotFoundError(Exception):
    pass


class ReviewAccessDeniedError(Exception):
    pass


class BookingNotCompletedError(Exception):
    pass


class ReviewAlreadyExistsError(Exception):
    pass
