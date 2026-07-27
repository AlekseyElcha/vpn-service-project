class DBBaseException(BaseException):
    pass


class ClientAlreadyExists(DBBaseException):
    pass


class UserAlreadyExists(DBBaseException):
    pass


class DBCrudException(BaseException):
    pass


class NotFoundException(BaseException):
    pass
