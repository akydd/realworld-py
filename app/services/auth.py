import jwt

ALGORITHM = "HS256"


class AuthService:
    def __init__(self, jwt_secret: str):
        self.jwt_secret = jwt_secret

    def create_jwt_token(self, user_id: int) -> str:
        return jwt.encode({"id": user_id}, self.jwt_secret, algorithm=ALGORITHM)

    def get_id_from_jwt_token(self, jwt_token: str) -> int:
        return jwt.decode(jwt_token, self.jwt_secret, algorithms=ALGORITHM)["id"]
