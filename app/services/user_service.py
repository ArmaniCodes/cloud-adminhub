from sqlalchemy.orm import Session
from app.schemas.user import CreateUser
from app.models.user import User as UserModel

def create_user(user: CreateUser, db: Session):
    userm = UserModel(
            name = user.name,
            email = user.email,
            role = user.role.value
        )
    db.add(userm)
    db.commit()
    db.refresh(userm)
    return userm

def find_user_by_id(user_id: int, db: Session):
    user = db.get(UserModel,user_id)
    return user