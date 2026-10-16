class ValidationException(Exception):
    def __init__(self, field: str) -> None:
        super().__init__(f"{field} can't be blank")
        self.field = field
        self.message = ["can't be blank"]


class DuplicateException(Exception):
    def __init__(self, field: str) -> None:
        super().__init__(f"{field} has already been taken")
        self.field = field
        self.message = ["has already been taken"]


class AuthenticationException(Exception):
    def __init__(self) -> None:
        super().__init__("credentials invalid")
