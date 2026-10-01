from os import getenv
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from jwt import encode

load_dotenv()
secret_key = getenv("SECRET_KEY")

if not secret_key:
    raise ValueError("secret_key cannot be empty")

ALGORITHM = "HS256"


def create_access_token(user_id: int, user_role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "role": user_role,
        "exp": now + timedelta(minutes=15)
    }
    token = encode(payload, secret_key, algorithm=ALGORITHM)
    return token