class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def not_found(what: str):
    return ApiError(404, "not_found", f"{what} not found")


def bad_request(code: str, message: str):
    return ApiError(400, code, message)


def unprocessable(code: str, message: str):
    return ApiError(422, code, message)
