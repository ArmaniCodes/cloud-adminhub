from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User as UserModel
from app.schemas.user import User, UserRole, CreateUser, UpdateUser

router = APIRouter()

@router.get("/users",response_model=list[User])
def get_users(db: Session = Depends(get_db)):
    stmt = select(UserModel)
    users = db.scalars(stmt).all()
    return users


@router.get("/users/{user_id}",response_model=User)
def get_user_by_id(user_id: int,  db: Session = Depends(get_db)):
    user = db.get(UserModel,user_id)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail= f"User with id: {user_id} does not exist")


@router.patch("/users/{user_id}", response_model = User)
def update_user(user_id: int, user_update: UpdateUser, db: Session = Depends(get_db)):
    
    user = db.get(UserModel,user_id)
    
    if not user:
        raise HTTPException(
             status_code=404, 
             detail= f"User with id: {user_id} does not exist"
             )

    # Convert the enum to a string before storing it in the database
    user_input = user_update.model_dump(exclude_unset=True)
    if "role" in user_input and type(user_input["role"]) == UserRole:
         user_input["role"] = user_input["role"].value
    
    for k,v in user_input.items():
        setattr(user,k,v)   
    
    try:
        db.commit()
    except IntegrityError:
         db.rollback()
         raise HTTPException(
              status_code=409, 
              detail = f'A user with that email already exists.'
         )
    
    db.refresh(user)
    return user
   

@router.delete("/users/{user_id}",response_model = User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(UserModel,user_id)
    if not user:
            raise HTTPException(
                 status_code=404, 
                 detail= f"User with id: {user_id} does not exist"
                 )
    
    db.delete(user)
    db.commit()
    return user


@router.post("/users",response_model=User,status_code=201)
def post_user(user: CreateUser, db: Session = Depends(get_db)):
    userm = UserModel(
        name = user.name,
        email = user.email,
        role = user.role.value
    )
    db.add(userm)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
        status_code=409,
        detail="A user with that email already exists."
    )

    db.refresh(userm)
    return userm