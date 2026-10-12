from getpass import getpass
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from app.schemas.user import CreateUser, UserRole
import sys
from app.database import SessionLocal, transaction
from app.models.user import User as UserModel
from app.security.password import hash_password

name = input("Name: ")
email = input("Email: ")
password = getpass("Password: ")
role = UserRole.admin

try:
   user_data = CreateUser(name = name, email = email, role = role, password = password)
except ValidationError as e:
    print(e)
    sys.exit(1)

db = SessionLocal()

try:
    user = UserModel(
        name=user_data.name,
        email=str(user_data.email).lower(),
        role=user_data.role.value,
        password_hash=hash_password(user_data.password)
    )

    try:
        with transaction(db):
            db.add(user)

    except IntegrityError:
        print(
            "Could not create admin. The email may already exist.",
            file=sys.stderr
        )
        sys.exit(1)

    print(f"Admin created: id={user.id}, email={user.email}")

finally:
    db.close()