class CityNotFoundError(Exception):
    pass


class CityAlreadyExistsError(Exception):
    pass


class DistrictNotFoundError(Exception):
    pass


class DistrictAlreadyExistsError(Exception):
    pass


class DistrictCityMismatchError(Exception):
    pass