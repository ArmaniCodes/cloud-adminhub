from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User as UserModel
from app.schemas.user import User, UserRole, CreateUser, UpdateUser
from app.services.user_service import create_user,find_user_by_id,upd_user,del_user

router = APIRouter()

@router.get("/users",response_model=list[User])
def get_users(db: Session = Depends(get_db)):
    
    stmt = select(UserModel)
    users = db.scalars(stmt).all()
    return users


@router.get("/users/{user_id}",response_model=User)
def get_user_by_id(user_id: int,  db: Session = Depends(get_db)):
    
    user = find_user_by_id(user_id,db)
    
    if not user:
        raise HTTPException(status_code=404, detail= f"User with id: {user_id} does not exist")
    return user
   
        


@router.patch("/users/{user_id}", response_model = User)
def update_user(user_id: int, user_update: UpdateUser, db: Session = Depends(get_db)):
    
    try:
        user = upd_user(user_id, user_update, db)
        if not user:
            raise HTTPException(
             status_code=404, 
             detail= f"User with id: {user_id} does not exist"
             )
        return user
    
    except IntegrityError:
         db.rollback()
         raise HTTPException(
              status_code=409, 
              detail = f'A user with that email already exists.'
         )
    
   

@router.delete("/users/{user_id}",response_model = User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = del_user(user_id,db)
    if not user:
            raise HTTPException(
                 status_code=404, 
                 detail= f"User with id: {user_id} does not exist"
                 )
    return user


@router.post("/users",response_model=User,status_code=201)
def post_user(user: CreateUser, db: Session = Depends(get_db)):
    
    try:
        created_user = create_user(user,db)
        return created_user
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
        status_code=409,
        detail="A user with that email already exists."
    )

    
    