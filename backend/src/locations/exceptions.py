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


class CityHasDistrictsError(Exception):
    pass


class CityInUseError(Exception):
    pass


class DistrictInUseError(Exception):
    pass
