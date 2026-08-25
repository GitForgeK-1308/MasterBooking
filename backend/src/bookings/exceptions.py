class MasterNotFoundError(Exception):
    pass


class MasterInactiveError(Exception):
    pass


class OfferingNotFoundError(Exception):
    pass


class OfferingInactiveError(Exception):
    pass


class OfferingDoesNotBelongToMasterError(Exception):
    pass


class MasterScheduleUnavailableError(Exception):
    pass


class BookingInPastError(Exception):
    pass


class BookingOutsideWorkingHoursError(Exception):
    pass


class InvalidBookingStartTimeError(Exception):
    pass


class BookingTimeConflictError(Exception):
    pass


class BookingNotFoundError(Exception):
    pass


class ClientPhoneRequiredError(Exception):
    pass


class BookingAccessDeniedError(Exception):
    pass


class InvalidBookingStatusTransitionError(Exception):
    pass


class SelfBookingNotAllowedError(Exception):
    pass
