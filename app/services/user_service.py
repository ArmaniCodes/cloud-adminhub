from sqlalchemy.orm import Session
from app.schemas.user import CreateUser, UpdateUser, UserRole
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

def upd_user(user_id: int, updated_info: UpdateUser, db: Session):
    user = db.get(UserModel,user_id)
    if not user:
        return None
    user_input = updated_info.model_dump(exclude_unset=True)
    if "role" in user_input and type(user_input["role"]) == UserRole:
        user_input["role"] = user_input["role"].value
        
    for k,v in user_input.items():
        setattr(user,k,v)

    db.commit()
    db.refresh(user)
    return user 

def del_user(user_id: int, db: Session):
    user = db.get(UserModel,user_id)
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user