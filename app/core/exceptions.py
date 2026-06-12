from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Conflicto con recurso existente"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "No autenticado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Sin permisos para este recurso"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BusinessRuleException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
