class PromoBaseException(BaseException):
    pass


class PromoAlreadyUsedException(PromoBaseException):
    pass


class PromoExpiredException(PromoBaseException):
    pass
