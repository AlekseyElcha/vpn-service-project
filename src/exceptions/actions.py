class ActionsBaseException(BaseException):
    pass


class DBActionException(ActionsBaseException):
    pass


class NotFoundExceptionAction(ActionsBaseException):
    pass
