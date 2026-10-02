from os import getenv
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
import secrets
from hashlib import sha256

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

def decode_access_token(token: str):
    try:
        decoded_token = decode(
            token,
            secret_key,
            algorithms=[ALGORITHM]
        )
        
        return {
            'role':decoded_token["role"],
            'id': decoded_token["sub"]
        }
    
    except ExpiredSignatureError:
        return None
    
    except InvalidTokenError:
        return None

def hash_refresh_token(token: str) -> str:
    token_bytes = token.encode()
    digest = sha256(token_bytes)
    return digest.hexdigest()


def create_refresh_token() -> str:
    token = secrets.token_urlsafe(32)
    return token
