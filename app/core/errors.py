class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class BadRequestError(DomainError):
    pass


class RateLimitError(DomainError):
    pass
