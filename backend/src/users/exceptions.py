class EmailAlreadyExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class InvalidAvatarTypeError(Exception):
    pass


class AvatarTooLargeError(Exception):
    pass
