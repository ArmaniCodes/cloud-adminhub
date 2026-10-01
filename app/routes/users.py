from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException,APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import User, CreateUser, UpdateUser
from app.services.user_service import (
    create_user as service_create_user,
    list_users,
    get_user_by_id as service_get_user_by_id,
    update_user as service_update_user,
    delete_user as service_delete_user,
)
from app.exceptions.user import UserAlreadyExistsError
from app.security.auth import require_role

router = APIRouter()

@router.get("/users", response_model=list[User])
def get_users(db: Session = Depends(get_db)):
    return list_users(db)


@router.get("/users/{user_id}",response_model=User)
def get_user_by_id(user_id: int,  db: Session = Depends(get_db)):
    
    user = service_get_user_by_id(user_id, db)
    
    if not user:
        raise HTTPException(status_code=404, detail= f"User with id: {user_id} does not exist")
    return user
   
        


@router.patch("/users/{user_id}", response_model = User)
def update_user(user_id: int, user_update: UpdateUser, db: Session = Depends(get_db)):
    
    try:
        user = service_update_user(user_id, user_update, db)
        if not user:
            raise HTTPException(
             status_code=404, 
             detail= f"User with id: {user_id} does not exist"
             )
        return user
    
    except UserAlreadyExistsError:
         raise HTTPException(
              status_code=409, 
              detail = f'A user with that email already exists.'
         )
    
   

@router.delete("/users/{user_id}",response_model = User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = service_delete_user(user_id,db)
    if not user:
            raise HTTPException(
                 status_code=404, 
                 detail= f"User with id: {user_id} does not exist"
                 )
    return user


@router.post("/users",response_model=User,status_code=201)
def post_user(user: CreateUser, db: Session = Depends(get_db), authorized_user = Depends(require_role("admin"))):
    try:
        created_user = service_create_user(user,db)
        return created_user
    except UserAlreadyExistsError:
        raise HTTPException(
        status_code=409,
        detail="A user with that email already exists."
    )

    
    